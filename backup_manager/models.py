from django.db import models

# Create your models here.


class Project(models.Model):
    name = models.CharField(max_length=255)
    backup_path = models.CharField(max_length=255)


class Environment(models.Model):
    name = models.CharField(max_length=255)
    host_db = models.CharField(max_length=255)
    port_db = models.IntegerField()
    backup_path = models.CharField(max_length=255)


class Backup(models.Model):
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=255)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Restore(models.Model):
    name = models.CharField(max_length=255)
    origin_backup = models.ForeignKey(Backup, on_delete=models.CASCADE)
    destination_environment = models.ForeignKey(Environment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
