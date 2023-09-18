import os

from celery import shared_task

from backup_manager.models import Database, Backup, Restore


@shared_task
def perform_backup(backup: Backup, user: str, password: str):
    pass


@shared_task
def perform_restore(restore: Restore, user: str, password: str):
    pass
