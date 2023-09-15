from datetime import datetime

from django.contrib import admin

from backup_manager.models import Environment, Project, Backup, Restore, Database, Host


# Register your models here.


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_path')
    search_fields = ('name',)


admin.site.register(Project, ProjectAdmin)


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_path')
    search_fields = ('name', 'host_db')


admin.site.register(Environment, EnvironmentAdmin)


class HostAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip', 'port')
    search_fields = ('name', 'ip')


admin.site.register(Host, HostAdmin)


@admin.action(description='Create Backup')
def create_backup(model_admin, request, queryset):
    dt: str = datetime.now().strftime('%d-%m-%Y-%H-%M')
    for database in queryset:
        backup = Backup(
            name='teste',
            path=f'{database.project}_{database.name}_{dt}.sql',
            project=database.project,
            environment=database.environment,
            status=False
        )
        backup.save()


class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'project', 'environment')
    search_fields = ('name', 'host__name', 'project__name', 'environment__name')
    autocomplete_fields = ('host', 'project', 'environment')
    actions = [create_backup]


admin.site.register(Database, DatabaseAdmin)


class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'project', 'environment', 'dt_create', 'dt_start', 'dt_end', 'status')
    search_fields = ('name', 'path', 'project__name', 'environment__name', 'dt_create', 'status')
    autocomplete_fields = ('project', 'environment')

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ('dt_start', 'dt_end', 'status')
        form = super(BackupAdmin, self).get_form(request, obj, **kwargs)
        return form


admin.site.register(Backup, BackupAdmin)


class RestoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_backup', 'destination_environment', 'dt_create', 'dt_start', 'dt_end', 'status')
    search_fields = ('name', 'origin_backup__name', 'origin_backup__project__name', 'destination_environment__name', 'dt_start', 'status')
    autocomplete_fields = ('origin_backup', 'destination_environment')

    def get_form(self, request, obj=None, **kwargs):
        self.exclude = ('dt_start', 'dt_end', 'status')
        form = super(RestoreAdmin, self).get_form(request, obj, **kwargs)
        return form


admin.site.register(Restore, RestoreAdmin)
