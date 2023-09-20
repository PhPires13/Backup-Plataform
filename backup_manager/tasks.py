import os
import subprocess
from datetime import datetime

from celery import shared_task

from backup_manager.models import Database, Backup, Restore


def run_command(obj, command: list, password: str):
    # Set the status and description before running the command
    obj.set_status('ST')
    obj.dt_start = datetime.now()
    obj.save()

    # Run the command
    try:
        result = subprocess.run(command, input=password.encode(), check=True, text=True)
        # Set the status and description after a success
        obj.set_status('SC')
        obj.description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and description after a fail
        obj.set_status('FL')
        obj.description = e.stderr
    except Exception as e:
        # Set the status and description after a fail
        obj.set_status('FL')
        obj.description = str(e)

    obj.dt_end = datetime.now()  # Set the end date
    obj.save()


@shared_task
def perform_backup(backup_id: int, user: str, password: str):
    backup = Backup.objects.get(id=backup_id)  # Get the backup object

    # Verify if the backup is not already done
    if backup.status != 'NS':
        return

    host = backup.database.host
    database = backup.database

    # Construct the pg_dump command
    command = [
        'pg_dump',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--no-password',  # Use this flag to prompt for a password
        database.name,
        '--file', backup.complete_path(),
    ]

    run_command(backup, command, password)


@shared_task
def perform_restore(restore_id: int, user: str, password: str):
    restore = Restore.objects.get(id=restore_id)  # Get the restore object

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

    run_command(restore, command, password)
