from datetime import datetime

from django.contrib import admin
from django import forms

from backup_manager.models import Environment, Project, Backup, Restore, Database, Host


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
    actions = ['create_backup']

    @admin.action(description='Create Backup')
    def create_backup(self, request, queryset):
        user = request.POST.get('user')
        password = request.POST.get('password')

        for database in queryset:
            backup = Backup(
                database=database
            )
            backup.save(user, password)


admin.site.register(Database, DatabaseAdmin)


class BackupAdminForm(forms.ModelForm):
    user = forms.CharField(max_length=255, help_text='User with permission to perform backup')
    password = forms.CharField(max_length=255, widget=forms.PasswordInput, help_text='Password of user with permission to perform backup')

    class Meta:
        model = Backup
        fields = '__all__'


class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'database', 'dt_create', 'dt_start', 'dt_end', 'status')
    search_fields = ('name', 'path', 'database', 'dt_create', 'status')
    autocomplete_fields = ('database',)

    form = BackupAdminForm

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ('path', 'dt_start', 'dt_end', 'status')
        form = super(BackupAdmin, self).get_form(request, obj, **kwargs)
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # TODO: start backup, form.cleaned_data.get('user'), form.cleaned_data.get('password')


admin.site.register(Backup, BackupAdmin)


class RestoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_backup', 'destination_database', 'dt_create', 'dt_start', 'dt_end', 'status')
    search_fields = ('name', 'origin_backup__name', 'origin_backup__project__name', 'destination_database__name', 'dt_start', 'status')
    autocomplete_fields = ('origin_backup', 'destination_database')

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ('dt_start', 'dt_end', 'status')
        form = super(RestoreAdmin, self).get_form(request, obj, **kwargs)
        return form


admin.site.register(Restore, RestoreAdmin)
