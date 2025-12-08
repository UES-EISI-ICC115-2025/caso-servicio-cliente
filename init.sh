# Env vars
export RASA_DB_USER=rasa_user
export RASA_DB_PASSWORD=icc115
export RASA_DB_NAME=rasa_db
export RASA_DB_HOST=localhost
export RASA_DB_PORT=5432

export AIRFLOW_HOME=/home/icc115/caso-servicio-cliente/airflow/airflow/
export AIRFLOW_DB_USER=airflow_user
export AIRFLOW_DB_PASSWORD=icc115
export AIRFLOW_DB_NAME=airflow_db
export AIRFLOW_DB_HOST=localhost
export AIRFLOW_DB_PORT=5432

export CLIENTS_DB_USER=clients_user
export CLIENTS_DB_PASSWORD=icc115
export CLIENTS_DB_NAME=clients_db
export CLIENTS_DB_HOST=localhost
export CLIENTS_DB_PORT=5432

# Instalación de paquetes de python
sudo apt update
sudo apt install -y python3 python3-pip python3-venv libpq-dev
sudo apt update

# Instalación de version de python con pyenv (3.10.12)
sudo apt install -y build-essential libssl-dev zlib1g-dev \
libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm \
libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python3-openssl
curl https://pyenv.run | bash
# Load pyenv
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
source ~/.bashrc  # or source ~/.zshrc
pyenv install 3.10.12
pyenv versions

# Instalación y configuración de PostgreSQL
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql

sudo -u postgres psql -c "CREATE DATABASE $RASA_DB_NAME;"
sudo -u postgres psql -c "CREATE USER $RASA_DB_USER WITH PASSWORD '$RASA_DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $RASA_DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $RASA_DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $RASA_DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "ALTER DATABASE $RASA_DB_NAME OWNER TO $RASA_DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $RASA_DB_NAME TO $RASA_DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $RASA_DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $RASA_DB_USER;"

sudo -u postgres psql -c "CREATE DATABASE $AIRFLOW_DB_NAME;"
sudo -u postgres psql -c "CREATE USER $AIRFLOW_DB_USER WITH PASSWORD '$AIRFLOW_DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $AIRFLOW_DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $AIRFLOW_DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $AIRFLOW_DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "ALTER DATABASE $AIRFLOW_DB_NAME OWNER TO $AIRFLOW_DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $AIRFLOW_DB_NAME TO $AIRFLOW_DB_USER;"

sudo -u postgres psql -c "CREATE DATABASE $CLIENTS_DB_NAME;"
sudo -u postgres psql -c "CREATE USER $CLIENTS_DB_USER WITH PASSWORD '$CLIENTS_DB_PASSWORD';"
sudo -u postgres psql -c "ALTER ROLE $CLIENTS_DB_USER SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE $CLIENTS_DB_USER SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE $CLIENTS_DB_USER SET timezone TO 'UTC';"
sudo -u postgres psql -c "ALTER DATABASE $CLIENTS_DB_NAME OWNER TO $CLIENTS_DB_USER;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $CLIENTS_DB_NAME TO $CLIENTS_DB_USER;"

~/.pyenv/versions/3.10.12/bin/python -m venv ./gradio/gradio_env
source ./gradio/gradio_env/bin/activate
pip install -r ./gradio/gradio_requirements.txt
deactivate

~/.pyenv/versions/3.10.12/bin/python -m venv ./rasa/rasa_env
source ./rasa/rasa_env/bin/activate
pip install -r ./rasa/rasa_requirements.txt
deactivate

~/.pyenv/versions/3.10.12/bin/python -m venv ./airflow/airflow_env
source ./airflow/airflow_env/bin/activate
pip install -r ./airflow/airflow_requirements.txt
export AIRFLOW_HOME=/home/icc115/caso-servicio-cliente/airflow/airflow
export AIRFLOW__SQL_ALCHEMY_CONN="postgresql+psycopg2://${AIRFLOW_DB_USER}:${AIRFLOW_DB_PASSWORD}@localhost:5432/${AIRFLOW_DB_NAME}"
export AIRFLOW_VERSION=3.0.3
airflow db migrate
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password icc115
deactivate


# Instalación de pgAdmin4
# Install the public key for the repository (if not done previously):
curl -fsS https://www.pgadmin.org/static/packages_pgadmin_org.pub | sudo gpg --dearmor -o /usr/share/keyrings/packages-pgadmin-org.gpg

# Create the repository configuration file:
sudo sh -c 'echo "deb [signed-by=/usr/share/keyrings/packages-pgadmin-org.gpg] https://ftp.postgresql.org/pub/pgadmin/pgadmin4/apt/$(lsb_release -cs) pgadmin4 main" > /etc/apt/sources.list.d/pgadmin4.list && apt update'

# Install for web mode only: 
sudo apt install pgadmin4-web -y
# Configure the webserver
sudo /usr/pgadmin4/bin/setup-web.sh

# Verificación y edición de configuración de PostgreSQL
sudo ss -tuln | grep 5432 # Verificar que PostgreSQL esté escuchando en el puerto 5432

# Si es necesario, editar el archivo postgresql.conf para permitir conexiones remotas
# sudo nano /etc/postgresql/16/main/postgresql.conf
#------------------------------------------------------------------------------
# CONNECTION AND AUTHENTICATION
#------------------------------------------------------------------------------

# listen_addresses (string)
# What IP address(es) to listen on; '*' means all
# listen_addresses = '*'    # Change from 'localhost' to '*'
# sudo systemctl restart postgresql

# Whitelist IP addresses in pg_hba.conf
# sudo -u postgres psql -c  'SHOW hba_file';
# sudo nano /etc/postgresql/16/main/pg_hba.conf
# TYPE  DATABASE        USER            ADDRESS         METHOD
# local   all             all                             peer

# Creación del servicio de Airflow
sudo nano /etc/systemd/system/airflow.service

[Unit]
Description=Apache Airflow
After=network.target postgresql.service
Wants=postgresql.service
[Service]
Environment=AIRFLOW_HOME=/home/icc115/caso-servicio-cliente/airflow/airflow
Environment="PATH=/home/icc115/caso-servicio-cliente/airflow/airflow_env/bin:$PATH"
User=icc115
Group=icc115
Type=simple
ExecStart=/home/icc115/caso-servicio-cliente/airflow/airflow_env/bin/airflow standalone
Restart=on-failure
RestartSec=5s
StandardOutput=journal

systemctl daemon-reload
sudo systemctl start airflow.service
sudo systemctl status airflow.service

# Instalar Nginx
sudo apt install nginx -y
sudo nano /etc/nginx/sites-available/airflow

server {
    listen 80;
    server_name dominio.com [IP_DEL_SERVIDOR]; # El dominio o IP principal
    # Bloque de ubicación para manejar la subruta /airflow/
    location /airflow/ {
        # Se requiere el trailing slash ('/') aquí y en base_url de Airflow
        proxy_pass http://127.0.0.1:8080/airflow/;
        # Cabeceras estándar para proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        # Directivas requeridas para la subruta de Airflow
        proxy_read_timeout 150;
        proxy_connect_timeout 150;
    }
    # Otros bloques 'location' para otros servicios:
    # location /servicio_b/ { ... }
}

sudo ln -s /etc/nginx/sites-available/airflow /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Gradio

sudo nano /etc/systemd/system/app-frontend.service

[Unit]
Description=Frontend Gradio
After=network.target
[Service]
# Usuario bajo el cual se ejecuta el servicio (debe tener permisos en el directorio)
User=demo
Group=demo
# Ruta absoluta al directorio donde reside app.py
WorkingDirectory=/home/icc115/caso-servicio-cliente/
# Comando de Inicio: Ejecuta el script app.py con el intérprete de Python del venv
# Gradio está configurado internamente para usar el puerto 8081.
ExecStart=/home/icc115/caso-servicio-cliente/gradio/gradio_env/bin/python3.10 /home/icc115/caso-servicio-cliente/gradio>
StandardOutput=journal
StandardError=journal
# El servicio debe reiniciarse automáticamente en caso de fallo
Restart=always
[Install]
WantedBy=multi-user.target

# Editar nginx reverse proxy
    location / {
        # Se requiere el trailing slash ('/') aquí y en base_url de Airflow
        proxy_pass http://127.0.0.1:8081;
        # Cabeceras estándar para proxy
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        # Directivas requeridas para la subruta de Airflow
        proxy_read_timeout 150;
        proxy_connect_timeout 150;
    }

# Instalando ollama
curl -fsSL https://ollama.com/install.sh | sh