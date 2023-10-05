#!/bin/bash

# Stop the Celery worker
sudo pkill -f 'sudo celery -A plataforma_backup worker --loglevel=info'

# Stop the Celery beat
sudo pkill -f 'celery -A plataforma_backup beat --loglevel=info'

# Start the Django development server
sudo pkill -f 'python3.11 manage.py runserver 0.0.0.0:8000'