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
    host_db = models.CharField(max_length=255)
    port_db = models.IntegerField()
    backup_path = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'tb_environment'


class Database(models.Model):
    name = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({self.project.name} - {self.environment.name})'

    class Meta:
        db_table = 'tb_database'


class Backup(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    dt_create = models.DateTimeField(auto_now_add=True)
    dt_start = models.DateTimeField(null=True)
    dt_end = models.DateTimeField(null=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} ({self.project.name} - {self.environment.name}) [{self.dt_create}]'

    class Meta:
        db_table = 'tb_backup'


class Restore(models.Model):
    name = models.CharField(max_length=255)
    origin_backup = models.ForeignKey(Backup, on_delete=models.CASCADE)
    destination_environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    dt_restore = models.DateTimeField(auto_now_add=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} (({self.origin_backup.name}) -> {self.destination_environment.name}) [{self.dt_restore}]'

    class Meta:
        db_table = 'tb_restore'
