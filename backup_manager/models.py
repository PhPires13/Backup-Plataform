from datetime import datetime

from django.db import models

# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=255)
    backup_path = models.CharField(max_length=255)

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
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    database = models.ForeignKey(Database, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.name} ({self.database}) [{self.dt_create}]'

    def save(self, *args, **kwargs):
        date_time: str = datetime.now().strftime('%d-%m-%Y-%H-%M')
        self.name = f'{self.database.project.name}_{self.database.environment.name}_{date_time}'
        self.path = f'{self.database.project.name}_{self.database.name}_{date_time}.sql'
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'tb_backup'


class Restore(models.Model):
    name = models.CharField(max_length=255)
    origin_backup = models.ForeignKey(Backup, on_delete=models.CASCADE)
    destination_environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True, blank=True)
    dt_end = models.DateTimeField(null=True, blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} (({self.origin_backup}) -> {self.destination_environment.name}) [{self.dt_create}]'

    class Meta:
        db_table = 'tb_restore'
