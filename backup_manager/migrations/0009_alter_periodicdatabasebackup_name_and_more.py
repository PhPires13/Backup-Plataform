# Generated by Django 4.2.5 on 2023-09-25 11:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backup_manager', '0008_periodicenvironmentbackup'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodicdatabasebackup',
            name='name',
            field=models.CharField(blank=True, help_text='Default: "Backup {database.project.name} - {database.environment.name} ({database.name}) [{self.periodic_task.crontab}]"', max_length=255),
        ),
        migrations.AlterField(
            model_name='periodicenvironmentbackup',
            name='name',
            field=models.CharField(blank=True, help_text='Default: "Backup {environment.name} [{self.periodic_task.crontab}]"', max_length=255),
        ),
    ]
