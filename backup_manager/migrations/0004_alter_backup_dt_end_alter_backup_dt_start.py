# Generated by Django 4.2.5 on 2023-09-13 13:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backup_manager', '0003_database'),
    ]

    operations = [
        migrations.AlterField(
            model_name='backup',
            name='dt_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='backup',
            name='dt_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
