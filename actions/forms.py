from rasa_sdk import FormValidationAction, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from typing import Any, Text, Dict, List
from dotenv import load_dotenv, find_dotenv
import psycopg2
import psycopg2.extras
import os

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

class ValidateProductForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_product_form"
    
    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        return ["plan", "producto_id", "nombre_producto", "precio_producto"]

    def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> List[Dict]:
        # Cuando el formulario está completo, confirma el producto
        dispatcher.utter_message(response="utter_confirmar_plan")
        return []

    def validate_plan(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar que el producto seleccionado esté en nuestra lista de productos válidos."""
        
        # Normalizamos el valor a minúsculas para la comparación
        product_normalized = str(slot_value).lower()

        # Leer credenciales desde variables de entorno
        pg_host = os.getenv("PG_HOST", "localhost")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_db = os.getenv("PG_DB", "mydb")
        pg_user = os.getenv("PG_USER", "postgres")
        pg_password = os.getenv("PG_PASSWORD", "")
        print(pg_host, pg_port, pg_db, pg_user, pg_password)

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
                # build a safe ILIKE pattern and use parameterized query correctly
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
                    (pattern,)
                )

                resultado_busqueda_producto = cur.fetchone()

                if not resultado_busqueda_producto:
                    dispatcher.utter_message(text=f"No reconozco '{slot_value}'. Por favor, elige uno de nuestros planes válidos.")
                    dispatcher.utter_message(response="action_fetch_product_plans")
                    return {"plan": None, "producto_id": None, "nombre_producto": None, "precio_producto": None}
                else:
                    # DictCursor returns a mapping; access columns by name instead of by index
                    print(f"Producto encontrado: {resultado_busqueda_producto['producto_id']} - {resultado_busqueda_producto['nombre']}")
                    return {
                        "plan": slot_value,
                        "producto_id": resultado_busqueda_producto["producto_id"],
                        "nombre_producto": resultado_busqueda_producto["nombre"],
                        "precio_producto": resultado_busqueda_producto["precio_mensual"],
                    }
        
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            dispatcher.utter_message(text="Lo siento, estoy teniendo problemas para verificar el producto en este momento. Por favor, intenta más tarde.")
            return {"plan": None}
        finally:
            if conn:
                conn.close()