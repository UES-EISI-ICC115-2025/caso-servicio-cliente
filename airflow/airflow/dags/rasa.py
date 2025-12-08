from __future__ import annotations

import pendulum

# These imports are standard and work across Airflow 2.x and 3.x
from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator


@dag(
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    doc_md="""
    ### PostgreSQL ELT Pipeline DAG
    This DAG demonstrates an Extract, Load, Transform (ELT) pipeline.
    It creates a source table, extracts and transforms data using Python,
    and loads the transformed data into a destination table.
    """,
    tags=["postgresql", "transform", "elt"],
    dag_id="postgres_transform_pipeline",
)
def postgres_transform_pipeline():
    # Define the connection ID created in the Airflow UI
    POSTGRES_CONN_ID = "rasa_db"

    # # Task 1: Create source and destination tables
    create_tables = SQLExecuteQueryOperator(
        task_id="create_nlu_tables",
        conn_id=POSTGRES_CONN_ID,
        sql="""
            CREATE TABLE IF NOT EXISTS nlu (
                id SERIAL PRIMARY KEY,
                text TEXT,
                slot VARCHAR(50),
                value TEXT,
                intent VARCHAR(100)
            );
        """,
    )

    # Task 2: Load sample data into the source table
    # load_sample_data = SQLExecuteQueryOperator(
    #     task_id="load_sample_data",
    #     conn_id=POSTGRES_CONN_ID,
    #     sql="""
    #         INSERT INTO source_data (value, status) VALUES
    #         (10, 'pending'),
    #         (20, 'completed'),
    #         (30, 'pending')
    #         ON CONFLICT (id) DO NOTHING;
    #     """,
    # )

    # Task 3: Extract and Transform data using Python
    @task
    def transform_data_python(**context):
        # Use the PostgresHook to connect to the database
        pg_hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
        
        # Execute a query to extract data
        # get_records returns a list of tuples
        records = pg_hook.get_records("SELECT * FROM events;")
        
        # Perform transformation (e.g., multiply values by 2)
        # The data must be formatted as a list of tuples for SQL insertion
        transformed_records = [(value[0] * 2, 'transformed') for value in records]
        
        # Push the transformed data to XCom for the next task
        context['ti'].xcom_push(key='transformed_records', value=transformed_records)

    # Task 4: Load transformed data into the destination table
    # # Uses Jinja templating to pull the transformed records from XCom
    # load_transformed_data = SQLExecuteQueryOperator(
    #     task_id="load_transformed_data",
    #     conn_id=POSTGRES_CONN_ID,
    #     sql="""
    #         INSERT INTO transformed_data (transformed_value, status) VALUES
    #         {% for row in ti.xcom_pull(key='transformed_records') %}
    #         {{ row }}{% if not loop.last %},{% endif %}
    #         {% endfor %};
    #     """,
    # )

    # Define task dependencies
    # create_tables >> load_sample_data >> transform_data_python() >> load_transformed_data
    transform_data_python()

# Register the DAG
postgres_transform_pipeline()
