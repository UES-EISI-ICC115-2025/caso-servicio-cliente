from typing import Any, Dict, List, Text
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

def fetch_product_plans() -> List[Dict[str, Any]]:
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
            cur.execute(
                """
                SELECT
                    producto_id,
                    nombre,
                    descripcion,
                    velocidad_bajada_mbps,
                    velocidad_subida_mbps,
                    precio_mensual,
                    beneficios
                FROM productos
                ORDER BY precio_mensual ASC
                """
            )
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

def find_product(product_name: str) -> List[Dict[Text, Any]]:
    """
    Busca un producto en la base de datos PostgreSQL por nombre.

    Args:
        product_name: Nombre del producto a buscar

    Returns:
        List of Dicts with the product data found or None if it doesn't exist
    """
    product_normalized = product_name.lower()

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
            pattern = f"%{product_normalized}%"
            cur.execute(
                """
                    SELECT
                        producto_id,
                        nombre,
                        descripcion,
                        velocidad_bajada_mbps,
                        velocidad_subida_mbps,
                        precio_mensual,
                        beneficios
                    FROM productos
                    WHERE
                        LOWER(
                            TRANSLATE(
                                nombre,
                                'áéíóúÁÉÍÓÚñÑ',
                                'aeiouAEIOUnN'
                            )
                        ) ILIKE LOWER(
                            TRANSLATE(
                                %s,
                                'áéíóúÁÉÍÓÚñÑ',
                                'aeiouAEIOUnN'
                            )
                        )
                    ORDER BY precio_mensual ASC
                    """,
                (pattern,),
            )

            resultado = cur.fetchall()

            if resultado:
                return resultado
            return []  # No se encontró ningún producto

    except Exception as e:
        print(f"Error al buscar producto en la base de datos: {e}")
        return []  # No se encontró ningún producto
    finally:
        if conn:
            conn.close()