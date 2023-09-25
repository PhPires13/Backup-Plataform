# Generated by Django 4.2.5 on 2023-09-25 10:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backup_manager', '0002_alter_periodicbackup_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodicbackup',
            name='name',
            field=models.CharField(blank=True, help_text='Default: "Backup {database.project.name} - {database.environment.name} ({database.name}) [{periodic_task.crontab}]"', max_length=255),
        ),
    ]