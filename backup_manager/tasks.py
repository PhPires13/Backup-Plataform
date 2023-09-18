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

    # Run the pg_dump command
    try:
        backup.dt_start = datetime.now()
        backup.save()
        result = subprocess.run(command, input=password.encode(), check=True, text=True)
        # Set the status and end time after a successful backup
        backup.status = True
        backup.description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and end time after a failed backup
        backup.status = False
        backup.description = e.stderr

    backup.dt_end = datetime.now()
    backup.save()


@shared_task
def perform_restore(restore: Restore, user: str, password: str):
    pass
