from pathlib import Path
from datetime import datetime, timedelta
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
import json
from airflow.sdk import dag, task


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# locate the SQL "sqlbook" file relative to this DAG file:
sql_path = (
    Path(__file__).resolve().parent.parent.parent
    / "sample_data"
    / "create_database_postgresql.sqlbook"
)
sql_text = sql_path.read_text()

with DAG(
    dag_id="generate_sample_data",
    default_args=default_args,
    description="Generate sample data: create database and objects from SQL book",
    start_date=datetime(2025, 11, 1),
    catchup=False,
    schedule=None,
    tags=["sample_data"],
) as dag:

    create_database = SQLExecuteQueryOperator(
        task_id="create_database_from_sqlbook",
        conn_id="clientes_db",
        sql=sql_text,
    )

    def convertir_dict_a_tupla(lista_de_diccionarios, orden_columnas):
        """
        Convierte una lista de diccionarios a una lista de tuplas,
        garantizando el orden de los valores. (Esta función NO requiere cambios de driver)

        Args:
            lista_de_diccionarios (list): La lista de diccionarios a convertir.
            orden_columnas (list): Una lista de strings con las claves en el orden deseado.

        Returns:
            list: Una lista de tuplas con los valores ordenados.
        """
        records_as_tuples = []
        for record in lista_de_diccionarios:
            try:
                # Obtener los valores en el orden especificado
                tuple_record = tuple(record[key] for key in orden_columnas)
                records_as_tuples.append(tuple_record)
            except KeyError as e:
                print(
                    f"Advertencia: El diccionario {record} no contiene la clave {e}. Se omite."
                )
        return records_as_tuples

    def cargar_json(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                print("Datos cargados desde el archivo:")
                print(data[:1])
                print("El tipo de dato cargado es:", type(data))
                return data
        except FileNotFoundError:
            print(f"Error: El archivo '{file_path}' no fue encontrado.")
        except json.JSONDecodeError:
            print(
                "Error: No se pudo decodificar el JSON. Asegúrate de que el formato sea correcto."
            )

    # More tasks to generate sample data can be added below and set dependencies.
    @task.virtualenv(
        task_id="virtualenv_python",
        requirements=["faker==37.11.0"],
        system_site_packages=False,
        multiple_outputs=True,
    )
    def generate_sample_data():
        """
        Example function that will be performed in a virtual environment.

        Importing at the module level ensures that it will not attempt to import the
        library before it is installed.
        """
        import random
        from faker import Faker
        from datetime import datetime, timedelta

        fake = Faker("es_ES")

        # Generate 50 fake users
        users = []
        for i in range(0, 50):
            user_id = fake.uuid4()
            users.append(
                {
                    "user_id": user_id,
                    "nombre": fake.name(),
                    "email": fake.email(),
                    "telefono": fake.phone_number(),
                    "direccion": fake.address(),
                    "fecha_registro": (
                        datetime.now() - timedelta(days=random.randint(180, 365))
                    ).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
        print("--- 50 Sample Users (Salvadoran Spanish) ---")
        print(users[:10])

        # Generate 6 months of billing data for each user
        billing_data = []
        service = "Internet Residencial"
        base_amount = 35.00
        today = datetime.now()

        for user in users:
            for month_offset in range(6, 0, -1):
                bill_date = today - timedelta(days=30 * month_offset)
                amount = base_amount + round(random.uniform(-5.00, 5.00), 2)
                status = random.choice(["Cancelado", "Pendiente"])

                billing_id = fake.uuid4()
                billing_data.append(
                    {
                        "billing_id": billing_id,
                        "user_id": user["user_id"],
                        "fecha_factura": bill_date.strftime("%Y-%m-%d 00:00:00"),
                        "monto": amount,
                        "estado": status,
                        "servicio": service,
                    }
                )
        print("\n--- 6 Months of Billing Data for 'Internet Residencial' ---")
        print(billing_data[:10])
        # Return a dict so downstream tasks can lookup XCom by string keys (XComArg requires str keys)
        return {"users": users, "billing": billing_data}
    @task
    def insert_users(users):
        if not users:
            print("No hay usuarios para insertar.")
            return 0
        hook = PostgresHook(postgres_conn_id="clientes_db")
        target_fields = [
            "user_id",
            "nombre",
            "email",
            "telefono",
            "direccion",
            "fecha_registro",
        ]
        tuplas_users = convertir_dict_a_tupla(
            users,
            target_fields,
        )
        if not tuplas_users:
            print("No se generaron tuplas de usuarios.")
            return 0
        hook.insert_rows(
            table="users",
            rows=tuplas_users,
            target_fields=target_fields,
            commit_every=1000,
            on_conflict="DO NOTHING",
        )
        print(f"Se insertaron {len(tuplas_users)} usuarios.")
        return len(tuplas_users)

    @task
    def insert_billing(billing_data):
        if not billing_data:
            print("No hay facturas para insertar.")
            return 0
        orden = [
            "billing_id",
            "user_id",
            "fecha_factura",
            "monto",
            "estado",
        ]
        tuplas = convertir_dict_a_tupla(billing_data, orden)
        if not tuplas:
            print("No se generaron tuplas de facturación.")
            return 0
        hook = PostgresHook(postgres_conn_id="clientes_db")
        hook.insert_rows(
            table="billing_data",
            rows=tuplas,
            target_fields=orden,
            commit_every=1000,
            on_conflict="DO NOTHING",
        )
        print(f"Se insertaron {len(tuplas)} registros de facturación.")
        return len(tuplas)

    # wire the pipeline: ensure DB is created before generating data, then insert users -> billing
    data = generate_sample_data()
    insert_users_task = insert_users(data["users"])
    insert_billing_task = insert_billing(data["billing"])

    create_database >> data
    data >> insert_users_task >> insert_billing_task
