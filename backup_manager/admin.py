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


class DatabaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'host', 'project', 'environment')
    search_fields = ('name', 'host__name', 'project__name', 'environment__name')


admin.site.register(Database, DatabaseAdmin)


class BackupAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'project', 'environment', 'dt_create', 'dt_start', 'dt_end', 'status')
    search_fields = ('name', 'path', 'project__name', 'environment__name', 'dt_create', 'status')


admin.site.register(Backup, BackupAdmin)


class RestoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'origin_backup', 'destination_environment', 'dt_restore', 'status')
    search_fields = ('name', 'origin_backup__name', 'origin_backup__project__name', 'destination_environment__name', 'dt_restore', 'status')


admin.site.register(Restore, RestoreAdmin)
