import os
from datetime import datetime

from django.db import models

# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_project'


class Environment(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_environment'


class Host(models.Model):
    name = models.CharField(max_length=255)
    ip = models.CharField(max_length=255)
    port = models.IntegerField()

    def __str__(self):
        return f'{self.name} ({self.ip}:{self.port})'

    class Meta:
        db_table = 'tb_host'


class Database(models.Model):
    name = models.CharField(max_length=255)
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.project.name} - {self.environment.name})'

    class Meta:
        db_table = 'tb_database'


class Backup(models.Model):
    name = models.CharField(max_length=255, blank=True, help_text='Default: "{project.name}_{environment.name}_{date_time}"')
    path = models.CharField(max_length=255)
    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(blank=True, help_text='Leave it _blank_ if the backup is to be done now')
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} ({self.database}) [{self.dt_create}]'

    def backup_path(backup: 'Backup') -> str:
        default = os.path.join('/', 'mnt', 'netapp01', 'postgres')
        month_year = backup.dt_create.strftime('%m-%Y')
        path = os.path.join(default, backup.database.environment.name, month_year, backup.database.project.name, backup.path)
        return path

    def save(self, *args, **kwargs):
        # If the creation date has an already been set
        if not self.dt_create:
            self.dt_create = datetime.now()
        else:
            self.status = True  # The backup is already done

        date_time: str = self.dt_create.strftime('%d-%m-%Y-%H-%M')

        if not self.name:
            self.name = f'{self.database.project.name}_{self.database.environment.name}_{date_time}'

        self.path = f'{self.database.project.name}_{self.database.name}_{date_time}.sql'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'tb_backup'


class Restore(models.Model):
    name = models.CharField(max_length=255)
    origin_backup = models.ForeignKey(Backup, on_delete=models.CASCADE)
    destination_database = models.ForeignKey(Database, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} (({self.origin_backup}) -> {self.destination_database.name}) [{self.dt_create}]'

    class Meta:
        db_table = 'tb_restore'
