# Generated by Django 4.2.5 on 2023-09-15 17:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backup_manager', '0008_remove_environment_backup_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backup',
            name='dt_create',
            field=models.DateTimeField(blank=True, help_text='Leave it _blank_ if the backup is to be done now'),
        ),
        migrations.AlterField(
            model_name='backup',
            name='name',
            field=models.CharField(blank=True, help_text='Default: "{project.name}_{environment.name}_{date_time}"', max_length=255),
        ),
        migrations.AlterField(
            model_name='backup',
            name='status',
            field=models.BooleanField(default=False),
        ),
    ]
