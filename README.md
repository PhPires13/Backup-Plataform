# PLATAFORMA-BACKUP

## Start Application (Docker)
- ### Build the Docker Image
  - Run ```docker-compose build```
- ### Run the Application
  - Run ```docker-compose up```
    - #### Arguments
      - ``-d``: detached mode


## Stop Application
- Run ```docker-compose down```


## Installation
- ### Environment Variables
  - Configure the ``.env`` file
- ### Docker
  - Run ```sh docker-install.sh```
- ### Python 3.11
    - https://www.python.org/downloads/
- ### Install Required Modules:
  - Terminal >> inside the project folder <br>
    ```pip install -r requirements.txt```
  - Possible errors (mostly on Linux):
    - ``Error: pg_config executable not found.`` <br>
      Terminal >> ```sudo apt install python3-dev libpq-dev```
    - ``error: command 'x86_64-linux-gnu-gcc' failed: No such file or directory`` <br>
      Terminal >> ```sudo apt-get install build-essential libssl-dev libffi-dev python3-dev```
    - ``error: command '/usr/bin/x86_64-linux-gnu-gcc' failed with exit code 1`` <br>
      Terminal >> ```sudo apt-get install python3.11-dev```
- ### Redis
  - https://redis.io/
  - #### Linux:
    - Terminal >> ```sudo apt install redis```
- ### PostgreSQL-Client
  - It is important to have the lates version of the PostgreSQL-Client, in order for the commands to work with all server versions
  - #### Linux:
    - Enable PostgreSQL Package Repository
      ```
      sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
      wget -qO- https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo tee /etc/apt/trusted.gpg.d/pgdg.asc &>/dev/null
      ```
    - Update the package list
      ```
      sudo apt update
      ```
    - Install PostgreSQL-Client
      ```
      sudo apt install postgresql-client
      ```
    - Check the version
      ```
      psql --version
      ```
