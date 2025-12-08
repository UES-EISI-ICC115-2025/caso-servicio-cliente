sudo apt update
sudo apt install -y python3-pip python3-venv libpq-dev build-essential
# sudo apt install -y default-mysql-client default-libmysqlclient-dev pkg-config
python3 -m venv airflow_env
source airflow_env/bin/activate

sudo chown -R $(whoami):$(whoami) ~/caso-servicio-cliente/airflow/airflow/
sudo chmod -R 755 ~/caso-servicio-cliente/airflow/airflow/

export AIRFLOW_HOME=/home/icc115/caso-servicio-cliente/airflow/airflow/
export AIRFLOW__SQL_ALCHEMY_CONN="postgresql+psycopg2://${AIRFLOW_DB_USER}:${AIRFLOW_DB_PASSWORD}@localhost:5432/${AIRFLOW_DB_NAME}"
export AIRFLOW_VERSION=3.0.3

# sudo -u postgres psql

# Extract the version of Python you have installed. If you're currently using a Python version that is not supported by Airflow, you may want to set this manually.
# See above for supported versions.
export PYTHON_VERSION="$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')"

export CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
# For example this would install 3.0.0 with python 3.10: https://raw.githubusercontent.com/apache/airflow/constraints-3.1.0/constraints-3.10.txt

pip install "apache-airflow[postgres]==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
pip install apache-airflow-providers-postgres
