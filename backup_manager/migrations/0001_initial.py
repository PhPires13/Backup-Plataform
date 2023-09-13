# Generated by Django 4.2.5 on 2023-09-13 14:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Backup',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('path', models.CharField(max_length=255)),
                ('dt_create', models.DateTimeField(auto_now_add=True)),
                ('dt_start', models.DateTimeField(blank=True, null=True)),
                ('dt_end', models.DateTimeField(blank=True, null=True)),
                ('status', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'tb_backup',
            },
        ),
        migrations.CreateModel(
            name='Environment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('backup_path', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'tb_environment',
            },
        ),
        migrations.CreateModel(
            name='Host',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('ip', models.CharField(max_length=255)),
                ('port', models.IntegerField()),
            ],
            options={
                'db_table': 'tb_host',
            },
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('backup_path', models.CharField(max_length=255)),
            ],
            options={
                'db_table': 'tb_project',
            },
        ),
        migrations.CreateModel(
            name='Restore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('dt_restore', models.DateTimeField(auto_now_add=True)),
                ('status', models.BooleanField(default=False)),
                ('destination_environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.environment')),
                ('origin_backup', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.backup')),
            ],
            options={
                'db_table': 'tb_restore',
            },
        ),
        migrations.CreateModel(
            name='Database',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.environment')),
                ('host', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.host')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.project')),
            ],
            options={
                'db_table': 'tb_database',
            },
        ),
        migrations.AddField(
            model_name='backup',
            name='environment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.environment'),
        ),
        migrations.AddField(
            model_name='backup',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backup_manager.project'),
        ),
    ]