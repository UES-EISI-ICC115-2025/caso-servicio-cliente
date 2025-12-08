from __future__ import annotations
import sys
from airflow.decorators import dag, task
import pendulum


@dag(
    start_date=pendulum.datetime(2023, 1, 1, tz="UTC"),
    schedule=None,
    catchup=False,
    dag_id="debug_environment_dag",
    tags=["debug", "environment"],
)
def debug_environment():
    @task
    def print_env_info():
        print("--- Python Executable ---")
        print(sys.executable)
        print("--- sys.path (Import Paths) ---")
        for p in sys.path:
            print(p)
        print("--- Installed Packages (pip list output) ---")

        try:
            import airflow.providers.postgres

            print("\nSUCCESS: airflow-providers-postgres found!")
            print(f"Location: {airflow.providers.postgres.__file__}")
        except ImportError:
            print("\nERROR: airflow-providers-postgres NOT found in this environment!")

    print_env_info()


debug_environment()
