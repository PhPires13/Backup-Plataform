# Start the Redis server
sudo service redis-server start

# Start the Celery worker
# Might need sudo to manipulate files
sudo python3.11 manage.py celery worker --loglevel=info &

# Start the Celery beat
python3.11 manage.py celery beat --loglevel=info &

# Start the Django development server
python3.11 manage.py runserver 0.0.0.0:8000