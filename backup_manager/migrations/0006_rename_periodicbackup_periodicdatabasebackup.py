# Generated by Django 4.2.5 on 2023-09-25 10:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0018_improve_crontab_helptext'),
        ('backup_manager', '0005_alter_periodicbackup_table'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PeriodicBackup',
            new_name='PeriodicDatabaseBackup',
        ),
    ]
