# Generated by Django 4.2.5 on 2023-09-22 15:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_beat', '0018_improve_crontab_helptext'),
        ('backup_manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='periodicbackup',
            name='name',
            field=models.CharField(blank=True, help_text='Default: "Backup {database.project.name} - {database.environment.name} ({database.name})"', max_length=255),
        ),
        migrations.AlterField(
            model_name='periodicbackup',
            name='periodic_task',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='django_celery_beat.periodictask'),
        ),
    ]
