from django.contrib import admin

from backup_manager.models import Environment, Project, Backup, Restore

# Register your models here.


class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'backup_path')
    search_fields = ('name',)


admin.site.register(Project, ProjectAdmin)


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'host_db', 'port_db', 'backup_path')
    search_fields = ('name', 'host_db')


admin.site.register(Environment, EnvironmentAdmin)


class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'project', 'environment', 'dt_create')
    search_fields = ('name', 'path', 'project__name', 'environment__name')


admin.site.register(Backup, BackupAdmin)


class RestoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_backup', 'destination_environment', 'dt_restore')
    search_fields = ('name', 'origin_backup__name', 'destination_environment__name')


admin.site.register(Restore, RestoreAdmin)
