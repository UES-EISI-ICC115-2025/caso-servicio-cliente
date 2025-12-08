from typing import Any, Dict, List
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv, find_dotenv


# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

# Leer credenciales desde variables de entorno
pg_host = os.getenv("PG_HOST", "localhost")
pg_port = os.getenv("PG_PORT", "5432")
pg_db = os.getenv("PG_DB", "mydb")
pg_user = os.getenv("PG_USER", "postgres")
pg_password = os.getenv("PG_PASSWORD", "")
print(pg_host, pg_port, pg_db, pg_user, pg_password)

def save_calificacion(session_id, user_id, rating, comentarios) -> List[Dict[str, Any]]:
    conn = None
    try: 
        conn = psycopg2.connect(
            host=pg_host,
            port=pg_port,
            dbname=pg_db,
            user=pg_user,
            password=pg_password,
            connect_timeout=5,
        )
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Insert feedback instead of fetching product plans
            cur.execute(
                """
                INSERT INTO feedback (session_id, user_id, rating, comentarios)
                VALUES (%s, %s, %s, %s)
                RETURNING feedback_id, session_id, user_id, rating, comentarios, fecha_feedback
                """,
                (session_id, user_id, rating, comentarios),
            )
            inserted = cur.fetchone()
            conn.commit()
            return [inserted] if inserted else []
            return cur.fetchall()
    except psycopg2.OperationalError as e:
        print(f"POSTGRES ERROR (fetch plans): {e}")
        return []
    except Exception as e:
        print(f"DB QUERY ERROR (fetch plans): {e}")
        return []
    finally:
        if conn:
            conn.close()