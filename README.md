# PLATAFORMA-BACKUP

## Start Application
- ### Run the Application
  - #### Locally
    - Terminal >> inside the project folder <br> ``python manage.py runserver``
    - The server will be running locally on http://127.0.0.1:8000/ or http://localhost:8000/
  - #### Running the server on a specific address and port
    - Terminal >> inside the project folder <br> ``python manage.py runserver 0.0.0.0:8000``
      - ``0.0.0.0`` wil make the server available on all network interfaces
      - Hosted in your PC accessible by other devices on the same network using your IP
- ### Run the Redis Server
  - #### Locally
    - Terminal >> ``sudo service redis-server start``
    - The server will be running locally on http://127.0.0.1:6379/ or http://localhost:6379/
  - #### Running the server on a specific address and port
    - Terminal >> ``sudo service redis-server --port 6379``
      - ``6379`` is the default port
      - Hosted in your PC accessible by other devices on the same network using your IP
- ### Run the Celery Worker and Beat
  - #### For development purposes
    - Terminal >> inside the project folder <br> ``sudo celery -A plataforma_backup worker --beat --scheduler django --loglevel=info``
    - Will run the worker and beat in the same terminal
  - #### For production purposes
    - Terminal >> inside the project folder <br>
      ``sudo celery -A plataforma_backup worker --loglevel=info`` <br>
      ``sudo celery -A plataforma_backup beat --loglevel=info``
  - #### Detached from the terminal
    - `--detach` or `-d` option in the end of the commands
    - `nohup <command> &` enclosing the command
      - log file `nohup.out` will be created in the current directory


## Installation
- ### Python 3.11
    - https://www.python.org/downloads/
- ### Install Required Modules:
  - Terminal >> inside the project folder <br> ``pip install -r requirements.txt``
- ### Redis
  - https://redis.io/
  - Linux:
    - Terminal >> ``sudo apt install redis``
