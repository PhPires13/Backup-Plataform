from django.contrib import admin
from django import forms
from django.utils import timezone
from django_celery_beat.admin import PeriodicTaskAdmin
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
    search_fields = ('name', 'host_db')


admin.site.register(Environment, EnvironmentAdmin)


class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip', 'port')
    search_fields = ('name', 'ip')


admin.site.register(Host, HostAdmin)


class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'project', 'environment')
    search_fields = ('name', 'host__name', 'project__name', 'environment__name')
    autocomplete_fields = ('host', 'project', 'environment')


admin.site.register(Database, DatabaseAdmin)


class BackupAdminForm(forms.ModelForm):
    user = forms.CharField(max_length=255, required=False, help_text='User with permission to perform backup')
    password = forms.CharField(max_length=255, widget=forms.PasswordInput, required=False, help_text='Password of user with permission to perform backup')

    class Meta:
        model = Backup
        fields = '__all__'


class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'database', 'dt_create', 'dt_start', 'dt_end', 'status', 'description')
    search_fields = ('name', 'path', 'database', 'dt_create', 'status')
    autocomplete_fields = ('database',)

    form = BackupAdminForm

    def add_view(self, request, form_url='', extra_context=None):
        self.exclude = ('path', 'dt_start', 'dt_end', 'status', 'description')
        return super(BackupAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.exclude = ('path',)
        return super(BackupAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # Save the model
        # Verify if the status is not 'Not Started'
        if obj.status == STATUS.PENDING.value:
            # Start the backup
            result = tasks.perform_backup.delay(obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'))
        elif obj.status == STATUS.SCHEDULED.value:
            # Schedule the backup
            result = tasks.perform_backup.apply_async(
                args=[obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password')],
                countdown=(obj.dt_create - timezone.now()).total_seconds()
            )

        # Set the task id
        obj.set_task(result.id)
        obj.save()


admin.site.register(Backup, BackupAdmin)


class RestoreAdminForm(forms.ModelForm):
    user = forms.CharField(max_length=255, required=False, help_text='User with permission to perform restore')
    password = forms.CharField(max_length=255, widget=forms.PasswordInput, required=False, help_text='Password of user with permission to perform restore')
    to_keep_old_data = forms.BooleanField(initial=True, required=False, help_text='Keep old data in the destination database (rename current schemas to {schema_old_DD_MM_YYYY_HH_MM})')
    to_ignore_public_schema = forms.BooleanField(initial=True, required=False, help_text='Ignore public schema in the destination database')

    class Meta:
        model = Restore
        fields = '__all__'


class RestoreAdmin(admin.ModelAdmin):
    def truncated_description(self, obj):
        if not obj.description:  # Verify if it is empty
            return obj.description

        size = 300
        if len(obj.description) > size:
            return obj.description[:size+1] + '...' if obj.description else ''
        else:
            return obj.description

    list_display = ('name', 'origin_backup', 'destination_database', 'dt_create', 'dt_start', 'dt_end', 'status', 'truncated_description')
    search_fields = ('name', 'origin_backup__name', 'origin_backup__project__name', 'destination_database__name', 'dt_start', 'status')
    autocomplete_fields = ('origin_backup', 'destination_database')

    form = RestoreAdminForm

    def add_view(self, request, form_url='', extra_context=None):
        self.exclude = ('dt_start', 'dt_end', 'status', 'description')
        return super(RestoreAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self.exclude = ()
        return super(RestoreAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)  # Save the model
        # Verify if the status is not 'Not Started'
        if obj.status == STATUS.PENDING.value:
            # Start the restore
            result = tasks.perform_restore.delay(obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'), form.cleaned_data.get('to_keep_old_data'), form.cleaned_data.get('to_ignore_public_schema'))
        elif obj.status == STATUS.SCHEDULED.value:
            # Schedule the restore
            result = tasks.perform_restore.apply_async(
                args=[obj.id, form.cleaned_data.get('user'), form.cleaned_data.get('password'), form.cleaned_data.get('to_keep_old_data'), form.cleaned_data.get('to_ignore_public_schema')],
                countdown=(obj.dt_create - timezone.now()).total_seconds()
            )

        # Set the task id
        obj.set_task(result.id)
        obj.save()


admin.site.register(Restore, RestoreAdmin)


class PeriodicTaskAdminForm(forms.ModelForm):
    crontab = forms.ModelChoiceField(
        queryset=CrontabSchedule.objects.all(),
        required=False,
    )

    class Meta:
        model = PeriodicDatabaseBackup
        fields = '__all__'


class PeriodicDatabaseBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'periodic_task', 'database')
    autocomplete_fields = ('periodic_task', 'database')

    form = PeriodicTaskAdminForm

    def add_view(self, request, form_url="", extra_context=None):
        self.exclude = ('periodic_task',)
        return super(PeriodicDatabaseBackupAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.exclude = ()
        return super(PeriodicDatabaseBackupAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.periodic_task:
            # Update PeriodicTask
            obj.periodic_task.name = obj.name
            obj.periodic_task.crontab = form.cleaned_data.get('crontab')
            obj.periodic_task.save()
        else:
            # Create PeriodicTask
            periodic_task = PeriodicTask.objects.create(
                name=obj.name,
                crontab=form.cleaned_data.get('crontab'),
                task='backup_manager.tasks.create_backup',
                args=f'[{obj.database.id}]',
            )
            obj.periodic_task = periodic_task
            obj.save()


admin.site.register(PeriodicDatabaseBackup, PeriodicDatabaseBackupAdmin)


class PeriodicEnvironmentBackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'periodic_task', 'environment')
    autocomplete_fields = ('periodic_task', 'environment')

    form = PeriodicTaskAdminForm

    def add_view(self, request, form_url="", extra_context=None):
        self.exclude = ('periodic_task',)
        return super(PeriodicEnvironmentBackupAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.exclude = ()
        return super(PeriodicEnvironmentBackupAdmin, self).change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.periodic_task:
            # Update PeriodicTask
            obj.periodic_task.name = obj.name
            obj.periodic_task.crontab = form.cleaned_data.get('crontab')
            obj.periodic_task.save()
        else:
            # Create PeriodicTask
            periodic_task = PeriodicTask.objects.create(
                name=obj.name,
                crontab=form.cleaned_data.get('crontab'),
                task='backup_manager.tasks.backup_environment',
                args=f'[{obj.environment.id}]',
            )
            obj.periodic_task = periodic_task
            obj.save()


admin.site.register(PeriodicEnvironmentBackup, PeriodicEnvironmentBackupAdmin)
