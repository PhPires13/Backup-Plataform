import os
from datetime import datetime
from enum import Enum

from django.core.exceptions import ValidationError
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


# Possible status of a backup or restore
class STATUS(Enum):
    PENDING = 'PD'
    STARTED = 'ST'
    SUCCESS = 'SC'
    FAILED = 'FL'
    MANUAL = 'MN'
    SCHEDULED = 'SD'


STATUS_CHOICES = (
    (STATUS.PENDING.value, STATUS.PENDING.name),
    (STATUS.STARTED.value, STATUS.STARTED.name),
    (STATUS.SUCCESS.value, STATUS.SUCCESS.name),
    (STATUS.FAILED.value, STATUS.FAILED.name),
    (STATUS.MANUAL.value, STATUS.MANUAL.name),
    (STATUS.SCHEDULED.value, STATUS.SCHEDULED.name),
)


class TaskModel(models.Model):
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_scheduled = models.DateTimeField(null=True, blank=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS.PENDING.value)
    description = models.TextField(null=True, blank=True)

    def set_status(self, choice: str = ''):
        if choice not in [status[0] for status in STATUS_CHOICES]:
            raise ValueError(f'Invalid status: {choice}')

        self.status = choice

    class Meta:
        abstract = True


class Backup(TaskModel):
    name = models.CharField(max_length=255, blank=True, help_text='Default: "{project.name}_{environment.name}_{date_time}"')
    path = models.CharField(max_length=255)
    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(blank=True, help_text='Leave it _blank_ if the backup is to be done now')

    def __str__(self):
        return f'{self.name} ({self.database}) [{self.dt_create}] {{{self.status}}}'

    def complete_path(self) -> str:
        default = os.path.join('/', 'mnt', 'netapp01', 'postgres')
        month_year = self.dt_create.strftime('%m-%Y')
        path = os.path.join(default, self.database.environment.name, month_year, self.database.project.name, self.path)
        return path

    def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created
            # If the creation date has an already been set
            if not self.dt_create:
                self.dt_create = datetime.now()
            else:
                self.set_status(STATUS.MANUAL.value)  # The backup is already done

            date_time: str = self.dt_create.strftime('%d-%m-%Y-%H-%M')

            self.path = f'{self.database.project.name}_{self.database.name}_{date_time}.sql'  # Set the path

        date_time: str = self.dt_create.strftime('%d-%m-%Y-%H-%M')

        # If the name is blank, set default
        if not self.name:
            self.name = f'{self.database.project.name}_{self.database.environment.name}_{date_time}'

        if self.dt_scheduled:
            self.set_status(STATUS.SCHEDULED.value)

        super().save(*args, **kwargs)

    class Meta:
        db_table = 'tb_backup'


class Restore(TaskModel):
    name = models.CharField(max_length=255, blank=True, help_text='Default: "{origin_backup} -> {destination_database}"')
    origin_backup = models.ForeignKey(Backup, on_delete=models.CASCADE)
    destination_database = models.ForeignKey(Database, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} (({self.origin_backup}) -> {self.destination_database.name}) [{self.dt_create}] {{{self.status}}}'

    def save(self, *args, **kwargs):
        # If the name is blank, set default
        if not self.name:
            self.name = f'{self.origin_backup} -> {self.destination_database}'

        super().save(*args, **kwargs)

    def clean(self, *args, **kwargs):
        super().clean()

        # Check if the origin and destination databases are of the same project
        if self.origin_backup.database.project != self.destination_database.project:
            raise ValidationError(f'Origin and destination databases must be of the same project')

        # Check if the origin backup is successful
        if self.origin_backup.status != STATUS.SUCCESS.value:
            raise ValidationError(f'Origin backup must be successful before using it to restore')

    class Meta:
        db_table = 'tb_restore'
