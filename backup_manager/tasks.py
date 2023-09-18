import os
import subprocess
from datetime import datetime

from celery import shared_task

from backup_manager.models import Database, Backup, Restore


@shared_task
def perform_backup(backup: Backup, user: str, password: str):
    host = backup.database.host
    database = backup.database

    # Construct the pg_dump command
    command = [
        'pg_dump',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--no-password',  # Use this flag to prompt for a password
        '--file', backup.complete_path(),
        database.name
    ]

    backup.set_status('ST')
    backup.dt_start = datetime.now()
    backup.save()

    # Run the pg_dump command
    try:
        result = subprocess.run(command, input=password.encode(), check=True, text=True)
        # Set the status and description after a successful backup
        backup.set_status('SC')
        backup.description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and description after a failed backup
        backup.set_status('FL')
        backup.description = e.stderr

    backup.dt_end = datetime.now()
    backup.save()


@shared_task
def perform_restore(restore: Restore, user: str, password: str):
    origin_backup = restore.origin_backup
    destination_database = restore.destination_database

    host = destination_database.host

    # Construct the pg_restore command
    command = [
        'pg_restore',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--no-password',  # Use this flag to prompt for a password
        '--dbname', destination_database.name,
        origin_backup.complete_path()
    ]

    restore.set_status('ST')
    restore.dt_start = datetime.now()
    restore.save()

    # Run the pg_restore command
    try:
        result = subprocess.run(command, input=password.encode(), check=True, text=True)
        # Set the status and description after a successful restore
        restore.set_status('SC')
        restore.description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and description after a failed restore
        restore.set_status('FL')
        restore.description = e.stderr

    restore.dt_end = datetime.now()
    restore.save()
