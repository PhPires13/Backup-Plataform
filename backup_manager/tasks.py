import os
import subprocess
from datetime import datetime

import psycopg2
from celery import shared_task

from backup_manager.models import Database, Backup, Restore, STATUS


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
def perform_restore(restore_id: int, user: str, password: str, to_keep_old_data: bool):
    restore = Restore.objects.get(id=restore_id)  # Get the restore object

    origin_backup = restore.origin_backup
    destination_database = restore.destination_database

    host = destination_database.host

    try:
        connection, cursor = database_connect(destination_database, user, password)
    except Exception as e:
        # Set the status and description after a fail
        restore.set_status(STATUS.FAILED.value)
        restore.description = str(e)
        restore.dt_end = datetime.now()
        restore.save()
        return

    if to_keep_old_data:
        try:
            # Rename all current schemas to schema_(datetime.now())
            cursor.execute(f"""
            SELECT schema_name
            FROM information_schema.schemata
            WHERE catalog_name = '{destination_database.name}'
            AND schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            AND schema_name NOT LIKE '%_old_%' ;
            """)

            for row in cursor.fetchall():
                schema_name = row[0]
                # if schema_name != 'public':  # If want to ignore public schema
                cursor.execute(f"ALTER SCHEMA {schema_name} RENAME TO {schema_name}_old_{restore.dt_create.strftime('%d_%m_%Y_%H_%M')} ;")
        except Exception as e:
            # Set the status and description after a fail
            restore.set_status(STATUS.FAILED.value)
            restore.description = str(e)
            restore.dt_end = datetime.now()
            restore.save()
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
            restore.set_status(STATUS.FAILED.value)
            restore.description = str(e)
            restore.dt_end = datetime.now()
            restore.save()
            return

    try:
        connection.commit()
        cursor.close()
    except Exception as e:
        # Set the status and description after a fail
        restore.set_status(STATUS.FAILED.value)
        restore.description = str(e)
        restore.dt_end = datetime.now()
        restore.save()
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

    run_command(restore, command, password)
