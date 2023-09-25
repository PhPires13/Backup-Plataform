import os
from enum import Enum

from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django_celery_beat.models import PeriodicTask
from django_cryptography.fields import encrypt


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
    user = models.CharField(max_length=255, null=True, blank=True, help_text='User used in periodic tasks')
    password = encrypt(models.CharField(max_length=255, null=True, blank=True, help_text='Password of user used in periodic tasks (encrypted)'))

    def __str__(self):
        return f'{self.name} ({self.ip}:{self.port})'

    class Meta:
        db_table = 'tb_host'


class Database(models.Model):
    name = models.CharField(max_length=255)
    host = models.ForeignKey(Host, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    user = models.CharField(max_length=255, null=True, blank=True, help_text='Overwrite the user used in periodic tasks')
    password = encrypt(models.CharField(max_length=255, null=True, blank=True, help_text='Overwrite the password of user used in periodic tasks (encrypted)'))

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
    task_id = models.CharField(max_length=255, null=True, blank=True)
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=STATUS.PENDING.value)
    description = models.TextField(null=True, blank=True)

    def set_status(self, choice: str = ''):
        if choice not in [status[0] for status in STATUS_CHOICES]:
            raise ValueError(f'Invalid status: {choice}')

        self.status = choice

    def set_task(self, task_id: str = ''):
        self.task_id = task_id

    def start_task(self) -> bool:
        if self.status == STATUS.STARTED.value:  # Check if the task is already started
            return False

        # Set the status and description before running the command
        self.set_status(STATUS.STARTED.value)
        self.dt_start = timezone.now()
        self.save()

        return True

    def finish_task(self, status: STATUS, description: str):
        # Set the status and description after a success
        self.set_status(status.value)
        self.dt_end = timezone.now()
        self.description = description
        self.save()

    def clean(self):
        # If it already has a task_id, revoke the task
        if self.task_id:
            try:
                result = AsyncResult(self.task_id)
                if result.state != 'STARTED':
                    result.revoke(terminate=True, wait=True, timeout=15)
            except Exception as e:
                raise ValidationError(f'Error revoking task: {e}')
            else:
                raise ValidationError(f'The task is already running, wait for it to finish!')

    class Meta:
        abstract = True


class Backup(TaskModel):
    name = models.CharField(max_length=255, blank=True, help_text='Default: "{project.name}_{environment.name}_{date_time}"')
    path = models.CharField(max_length=255)
    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(blank=True, help_text='Leave it _blank_ if the backup is to be done now  | Set it to a future date if the backup is to be scheduled  | Set it to a past date if the backup is already done')

    def __str__(self):
        return f'{self.name} ({self.database}) [{self.dt_create}] {{{self.status}}}'

    def complete_path(self) -> str:
        default = os.path.join('/', 'mnt', 'netapp01', 'postgres')
        month_year = self.dt_create.strftime('%m-%Y')
        path = os.path.join(default, self.database.environment.name, month_year, self.database.project.name, self.path)
        return path

    def save(self, *args, **kwargs):
        if not self.pk:  # If the object is being created
            # If the creation date is already set
            if not self.dt_create:
                self.dt_create = timezone.now()
            else:
                self.set_status(STATUS.MANUAL.value)  # The backup is already done

        date_time: str = self.dt_create.strftime('%d-%m-%Y-%H-%M')

        # If the name is blank, set default
        if not self.name:
            self.name = f'{self.database.project.name}_{self.database.environment.name}_{date_time}'

        self.path = f'{self.database.project.name}_{self.database.name}_{date_time}.sql'  # Set the path

        # If the creation date is in the future
        if self.dt_create > timezone.now():
            self.set_status(STATUS.SCHEDULED.value)  # The backup is scheduled

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


class PeriodicTaskModel(models.Model):
    name = models.CharField(max_length=255)
    periodic_task = models.OneToOneField(to=PeriodicTask, on_delete=models.CASCADE, null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        if self.periodic_task:
            self.periodic_task.delete()
        super().delete(using, keep_parents)

    class Meta:
        abstract = True


class PeriodicDatabaseBackup(PeriodicTaskModel):
    name = models.CharField(max_length=255, blank=True, help_text='Default: "Backup {database.project.name} - {database.environment.name} ({database.name})"')
    database = models.ForeignKey(Database, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # If the name is blank, set default
        if not self.name:
            self.name = f'Backup {self.database.project.name} - {self.database.environment.name} ({self.database.name})'

        super().save(*args, **kwargs)

    def clean(self):
        user = self.database.user if self.database.user else self.database.host.user
        password = self.database.password if self.database.password else self.database.host.password

        if not user:
            raise ValidationError(f'User not set in database or host')
        if not password:
            raise ValidationError(f'Password not set in database or host')

    class Meta:
        db_table = 'tb_periodic_database_backup'
