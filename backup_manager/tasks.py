import os
import subprocess
from datetime import datetime

from celery import shared_task

from backup_manager.models import Database, Backup, Restore, STATUS


def run_command(obj, command: list, password: str):
    # Set the status and description before running the command
    obj.set_status(STATUS.STARTED.value)
    obj.dt_start = datetime.now()
    obj.save()

    os.environ['PGPASSWORD'] = password

    # Run the command
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=password, check=True, encoding='utf-8')
        # Set the status and description after a success
        obj.set_status(STATUS.SUCCESS.value)
        obj.description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and description after a fail
        obj.set_status(STATUS.FAILED.value)
        obj.description = e.stderr
    except Exception as e:
        # Set the status and description after a fail
        obj.set_status(STATUS.FAILED.value)
        obj.description = str(e)

    obj.dt_end = datetime.now()  # Set the end date
    obj.save()


@shared_task
def perform_backup(backup_id: int, user: str, password: str):
    backup = Backup.objects.get(id=backup_id)  # Get the backup object

    # Verify if the backup is not already done
    if backup.status != STATUS.PENDING.value:
        return

    host = backup.database.host
    database = backup.database

    # Create the directory structure if it doesn't exist
    os.makedirs(os.path.dirname(backup.complete_path()), exist_ok=True)

    # Construct the pg_dump command
    command = [
        'pg_dump',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--dbname', database.name,
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
        'psql',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--dbname', destination_database.name,
        '--file', origin_backup.complete_path()
        '--clean'
    ]

    run_command(restore, command, password)
