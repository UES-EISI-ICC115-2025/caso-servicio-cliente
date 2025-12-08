from __future__ import annotations

import pendulum

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator


# 1. Función para la tarea Python
def my_python_hello():
    """Esta función será llamada por PythonOperator."""
    print("¡Hola desde la función Python de Airflow!")
    return "Ejecución de Python completada"


# 2. Definición del DAG
with DAG(
    dag_id="hello_world_simple_dag",  # ID único del DAG
    start_date=pendulum.datetime(2025, 1, 1, tz="UTC"),  # Fecha de inicio
    schedule=None,  # Lo ejecutaremos manualmente (o puedes usar "@daily")
    catchup=False,  # Evita ejecutar tareas perdidas desde start_date
    tags=["ejemplo", "tutorial"],  # Etiquetas para la UI
) as dag:

    # 3. Tarea 1: Inicio del flujo (Dummy/Bash simple)
    # Ejecuta un comando bash para imprimir un mensaje
    start_task = BashOperator(
        task_id="start_flow",
        bash_command="echo 'Iniciando el flujo de Hola Mundo de Airflow'",
    )

    # 4. Tarea 2: Tarea con PythonOperator
    # Ejecuta la función Python que definimos arriba
    python_task = PythonOperator(
        task_id="run_python_script",
        python_callable=my_python_hello,
    )

    # 5. Tarea 3: Tarea con BashOperator para la fecha
    # Ejecuta un comando para obtener y mostrar la fecha actual
    date_task = BashOperator(
        task_id="show_current_date",
        bash_command="echo 'La fecha de ejecución es: $(date)'",
    )

    # 6. Definición de las dependencias
    # start_task debe completarse primero.
    # Luego, python_task y date_task se ejecutan en paralelo.
    start_task >> [python_task, date_task]
