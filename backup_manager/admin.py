from django.contrib import admin

from backup_manager.models import Environment, Project, Backup, Restore

# Register your models here.
admin.site.register(Project)
admin.site.register(Environment)
admin.site.register(Backup)
admin.site.register(Restore)
