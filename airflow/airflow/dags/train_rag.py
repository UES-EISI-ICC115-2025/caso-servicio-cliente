from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
# Define the absolute path to your Rasa virtual environment's Python binary
RASA_PYTHON_BIN = "/home/icc115/caso-servicio-cliente/rasa_rag/training_env/bin/python3.10"
RASA_PROJECT_DIR = "/home/icc115/caso-servicio-cliente/rasa_rag"
# 2. Definición del DAG
with DAG(
    dag_id="train_rag",  # ID único del DAG
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),  # Fecha de inicio
    schedule=None,  # Lo ejecutaremos manualmente (o puedes usar "@daily")
    catchup=False,  # Evita ejecutar tareas perdidas desde start_date
    tags=["train", "rag", "QA"],  # Etiquetas para la UI
) as dag:

    # 5. Tarea 3: Tarea con BashOperator para la fecha
    # Ejecuta un comando para obtener y mostrar la fecha actual
    train_rag = BashOperator(
        task_id="train_rag_with_pdfs",
        bash_command=f"""
        cd {RASA_PROJECT_DIR}
        # Use the python binary from the venv to run the rasa command
        {RASA_PYTHON_BIN} training.py
        """,
    )

    train_rag   
