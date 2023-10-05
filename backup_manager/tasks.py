import os
import subprocess

import psycopg2
from celery import shared_task
from celery.worker.control import revoke
from django.utils import timezone

from backup_manager.models import Database, Backup, Restore, STATUS, Environment


def database_connect(database: Database, user: str, password: str) -> (psycopg2.extensions.connection, psycopg2.extensions.cursor):
    connection = psycopg2.connect(
        host=database.host.ip,
        port=database.host.port,
        dbname=database.name,
        user=user,
        password=password,
    )
    cursor = connection.cursor()

    return connection, cursor


def run_command(obj, command: list, password: str):
    # Set the postgres password as an environment variable
    os.environ['PGPASSWORD'] = password

    # Run the command
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, input=password, check=True, encoding='utf-8')
        # Set the status and description after a success
        status = STATUS.SUCCESS
        description = result.stdout
    except subprocess.CalledProcessError as e:
        # Set the status and description after a fail
        status = STATUS.FAILED
        description = e.stderr
    except Exception as e:
        # Set the status and description after a fail
        status = STATUS.FAILED
        description = str(e)

    return status, description


@shared_task
def perform_backup(backup_id: int, user: str, password: str, already_started: bool = False):
    backup = Backup.objects.get(id=backup_id)  # Get the backup object

    if not already_started:  # Verify if the task was already started
        successfully_started = backup.start_task()

        # Verify if it was successfully started
        if not successfully_started:
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

    status, description = run_command(backup, command, password)

    backup.finish_task(status, description)


@shared_task
def perform_restore(restore_id: int, user: str, password: str, to_keep_old_data: bool, to_ignore_public_schema: bool):
    restore = Restore.objects.get(id=restore_id)  # Get the restore object

    successfully_started = restore.start_task()

    # Verify if it was successfully started
    if not successfully_started:
        return

    origin_backup = restore.origin_backup
    destination_database = restore.destination_database

    host = destination_database.host

    try:
        connection, cursor = database_connect(destination_database, user, password)
    except Exception as e:
        # Set the status and description after a fail
        restore.finish_task(STATUS.FAILED, str(e))
        return

    if to_keep_old_data:
        try:
            # Rename all current schemas to schema_(timezone.now())
            cursor.execute(f"""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE catalog_name = '{destination_database.name}'
            AND schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            AND schema_name NOT LIKE '%_old_%' ;
            """)

            for row in cursor.fetchall():
                schema_name = row[0]
                if to_ignore_public_schema and schema_name == 'public':  # Verify if the public schema should be ignored
                    continue
                cursor.execute(f"ALTER SCHEMA {schema_name} RENAME TO {schema_name}_old_{restore.dt_reference.strftime('%d_%m_%Y_%H_%M')} ;")
        except Exception as e:
            # Set the status and description after a fail
            restore.finish_task(STATUS.FAILED, str(e))
            return
    else:
        try:
            # Reset the destination database using Django's database management functions
            # Terminate all connections to the database
            cursor.execute(f"""
            SELECT pg_terminate_backend(pg_stat_activity.pid)
            FROM pg_stat_activity
            WHERE pg_stat_activity.datname = '{destination_database.name}' ;
            """)
            cursor.execute(f'DROP DATABASE IF EXISTS {destination_database.name} ;')
            cursor.execute(f'CREATE DATABASE {destination_database.name} ;')
        except Exception as e:
            # Set the status and description after a fail
            restore.finish_task(STATUS.FAILED, str(e))
            return

    try:
        connection.commit()
        cursor.close()
    except Exception as e:
        # Set the status and description after a fail
        restore.finish_task(STATUS.FAILED, str(e))
        return

    # Construct the pg_restore command
    command = [
        'psql',
        '-h', host.ip,
        '-p', str(host.port),
        '-U', user,
        '--dbname', destination_database.name,
        '--file', origin_backup.complete_path(),
    ]

    status, description = run_command(restore, command, password)

    restore.finish_task(status, description)


@shared_task
def create_backup(database_id: int):
    database = Database.objects.get(id=database_id)

    # Create the backup object
    backup = Backup.objects.create(
        database=database
    )

    backup.start_task()

    # Get the user and password from the database
    user = database.user if database.user else database.host.user
    password = database.password if database.password else database.host.password

    if not user:
        backup.finish_task(STATUS.FAILED, 'User not set in database or host')
        return
    if not password:
        backup.finish_task(STATUS.FAILED, 'Password not set in database or host')
        return

    # Start the backup
    perform_backup.delay(backup.id, user, password, already_started=True)


@shared_task
def backup_environment(environment_id: int):
    environment = Environment.objects.get(id=environment_id)

    # Get all databases from the environment
    databases = Database.objects.filter(environment=environment)

    # Create a backup for each database
    for database in databases:
        create_backup.delay(database.id)


@shared_task
def revoke_task(task_id: int, task_type: str):
    if task_type == Backup.__name__:
        task = Backup.objects.get(id=task_id)
    elif task_type == Restore.__name__:
        task = Restore.objects.get(id=task_id)
    else:
        return

    initial_status = task.status

    task.set_status(STATUS.REVOKING.value)
    task.save()

    result = revoke(task.task_id, terminate=True, wait=True)

    if result.get('ok'):
        task.set_task(None)
        task.set_status(STATUS.CANCELED.value)
    else:
        task.set_status(initial_status, result.get('error'))
    task.save()
