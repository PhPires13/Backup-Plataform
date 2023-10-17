from django.contrib import admin
from django import forms
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from backup_manager import tasks
from backup_manager.models import Environment, Project, Backup, Restore, Database, Host, STATUS, PeriodicDatabaseBackup, \
    PeriodicEnvironmentBackup


# Register your models here.


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Project, ProjectAdmin)


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


admin.site.register(Environment, EnvironmentAdmin)


class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip', 'port')
    search_fields = ('name', 'ip')


admin.site.register(Host, HostAdmin)


class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'project', 'environment')
    search_fields = ('name', 'host__name', 'project__name', 'environment__name')
    list_filter = ('host', 'project', 'environment')
    autocomplete_fields = ('host', 'project', 'environment')


admin.site.register(Database, DatabaseAdmin)


class TaskAdminForm(forms.ModelForm):
    user = forms.CharField(max_length=255, required=False, help_text='User with permission to perform the action')
    password = forms.CharField(max_length=255, widget=forms.PasswordInput, required=False, help_text='Password of user with permission to perform the action')

    class Meta:
        fields = '__all__'


class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm

    def delete_model(self, request, obj):
        if obj.task_id:
            tasks.revoke_task.delay(obj.id, type(obj).__name__)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.task_id:
                tasks.revoke_task.delay(obj.id, type(obj).__name__)


class BackupAdmin(TaskAdmin):
    list_display = ('name', 'path', 'database', 'dt_reference', 'dt_start', 'dt_end', 'status', 'description')
    search_fields = ('name', 'path', 'database__name', 'dt_reference', 'status')
    list_filter = ('database', 'database__project', 'database__environment', 'status')
    autocomplete_fields = ('database',)

    def add_view(self, request, form_url='', extra_context=None):
        self.exclude = ('task_id', 'path', 'dt_start', 'dt_end', 'status', 'description')
        return super(BackupAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.exclude = ('task_id', 'path')
        return super(BackupAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # Save the model
        # Verify if the status is not 'Not Started'
        if obj.status == STATUS.PENDING.value:
            # Start the backup
            result = tasks.perform_backup.delay(obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'))

            # Set the task id
            obj.set_task(result.id)
            obj.save()
        elif obj.status == STATUS.SCHEDULED.value:
            # Schedule the backup
            result = tasks.perform_backup.apply_async(
                args=[obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password')],
                countdown=(obj.dt_reference - timezone.now()).total_seconds()
            )

            # Set the task id
            obj.set_task(result.id)
            obj.save()


admin.site.register(Backup, BackupAdmin)


class RestoreAdminForm(TaskAdminForm):
    to_keep_old_data = forms.BooleanField(initial=True, required=False, help_text='Keep old data in the destination database (rename current schemas to {schema_old_DD_MM_YYYY_HH_MM})')
    to_ignore_public_schema = forms.BooleanField(initial=True, required=False, help_text='Ignore public schema in the destination database')

    class Meta:
        model = Restore
        fields = '__all__'


class RestoreAdmin(TaskAdmin):
    def truncated_description(self, obj):
        if not obj.description:  # Verify if it is empty
            return obj.description

        size = 300
        if len(obj.description) > size:
            return obj.description[:size+1] + '...' if obj.description else ''
        else:
            return obj.description

    list_display = ('name', 'origin_backup', 'destination_database', 'dt_reference', 'dt_start', 'dt_end', 'status', 'truncated_description')
    search_fields = ('name', 'origin_backup__name', 'origin_backup__project__name', 'destination_database__name', 'dt_start', 'status')
    list_filter = ('destination_database', 'destination_database__project', 'destination_database__environment', 'status')
    autocomplete_fields = ('origin_backup', 'destination_database')

    def add_view(self, request, form_url='', extra_context=None):
        self.exclude = ('task_id', 'dt_start', 'dt_end', 'status', 'description')
        return super(RestoreAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.exclude = ('task_id',)
        return super(RestoreAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # Save the model
        # Verify if the status is not 'Not Started'
        if obj.status == STATUS.PENDING.value:
            # Start the restore
            result = tasks.perform_restore.delay(obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'), form.cleaned_data.get('to_keep_old_data'), form.cleaned_data.get('to_ignore_public_schema'))

            # Set the task id
            obj.set_task(result.id)
            obj.save()
        elif obj.status == STATUS.SCHEDULED.value:
            # Schedule the restore
            result = tasks.perform_restore.apply_async(
                args=[obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'), form.cleaned_data.get('to_keep_old_data'), form.cleaned_data.get('to_ignore_public_schema')],
                countdown=(obj.dt_reference - timezone.now()).total_seconds()
            )

            # Set the task id
            obj.set_task(result.id)
            obj.save()


admin.site.register(Restore, RestoreAdmin)


class PeriodicTaskAdminForm(forms.ModelForm):
    crontab = forms.ModelChoiceField(
        queryset=CrontabSchedule.objects.all(),
        required=True,
    )

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.periodic_task:
            self.fields['crontab'].initial = self.instance.periodic_task.crontab  # Set the initial value as the current


class PeriodicTaskAdmin(admin.ModelAdmin):
    def enabled(self, obj) -> bool:
        return obj.periodic_task.enabled if obj.periodic_task else None

    form = PeriodicTaskAdminForm

    def add_view(self, request, form_url="", extra_context=None):
        self.exclude = ('name', 'periodic_task')
        return super(PeriodicTaskAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.exclude = ('name',)
        return super(PeriodicTaskAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        if not obj.periodic_task:
            # Create PeriodicTask
            obj.periodic_task = PeriodicTask(
                crontab=form.cleaned_data.get('crontab'),
            )

        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        if obj.periodic_task:
            obj.periodic_task.delete()
        super().delete_model(request, obj)

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.periodic_task:
                obj.periodic_task.delete()
        super().delete_queryset(request, queryset)


class PeriodicDatabaseBackupAdmin(PeriodicTaskAdmin):
    list_display = ('name', 'enabled', 'periodic_task', 'database')
    autocomplete_fields = ('periodic_task', 'database')


admin.site.register(PeriodicDatabaseBackup, PeriodicDatabaseBackupAdmin)


class PeriodicEnvironmentBackupAdmin(PeriodicTaskAdmin):
    list_display = ('name', 'enabled', 'periodic_task', 'environment')
    autocomplete_fields = ('periodic_task', 'environment')


admin.site.register(PeriodicEnvironmentBackup, PeriodicEnvironmentBackupAdmin)
