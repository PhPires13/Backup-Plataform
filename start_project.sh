# Start the Redis server
sudo service redis-server start

# Start the Celery worker
# Might need sudo to manipulate files
sudo celery -A plataforma_backup worker --loglevel=info

# Start the Celery beat
celery -A plataforma_backup beat --loglevel=info

# Start the Django development server
python3.11 manage.py runserver 0.0.0.0:8000