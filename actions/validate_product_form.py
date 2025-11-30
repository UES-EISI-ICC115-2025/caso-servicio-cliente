from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from rasa_sdk.types import DomainDict
import os
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv, find_dotenv
from rasa_sdk.events import ActiveLoop, SlotSet

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

import requests  # Necesario para la llamada HTTP

# --- CONFIGURACIÓN DE LA API RAG LOCAL ---
# Este es el puerto del servidor Gunicorn que corre rasa_rag_api_server.py
RAG_API_URL = "http://localhost:8000/rag/query"
RAG_API_REPHRASE_URL = "http://localhost:8000/rag/query_with_context"

# Leer credenciales desde variables de entorno
pg_host = os.getenv("PG_HOST", "localhost")
pg_port = os.getenv("PG_PORT", "5432")
pg_db = os.getenv("PG_DB", "mydb")
pg_user = os.getenv("PG_USER", "postgres")
pg_password = os.getenv("PG_PASSWORD", "")
print(pg_host, pg_port, pg_db, pg_user, pg_password)

class ActionDeactivateProductForm(Action):
    def name(self) -> Text:
        return "action_deactivate_product_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # dispatcher.utter_message(text="Formulario de selección de producto desactivado.")
        return [
            ActiveLoop(None),
            SlotSet("plan", None),
            SlotSet("producto_id", None),
            SlotSet("nombre_producto", None),
            SlotSet("precio_producto", None),
            # SlotSet("confirmar_product_form", None),
            SlotSet("requested_slot", None),
        ]

# class ActionAskProductFormPlan(Action):
#     def name(self) -> Text:
#         return "action_ask_product_form_plan"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[EventType]:
        
#         conn = None
#         try:
#             conn = psycopg2.connect(
#                 host=pg_host,
#                 port=pg_port,
#                 dbname=pg_db,
#                 user=pg_user,
#                 password=pg_password,
#                 connect_timeout=5,
#             )

#             with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
#                 cur.execute(
#                     """
#                     SELECT
#                         producto_id,
#                         nombre,
#                         descripcion,
#                         velocidad_bajada_mbps,
#                         velocidad_subida_mbps,
#                         precio_mensual,
#                         beneficios
#                     FROM productos
#                     ORDER BY precio_mensual ASC
#                     """
#                 )

#                 rows = cur.fetchall()

#                 if not rows:
#                     dispatcher.utter_message(
#                         text="No hay planes activos disponibles en este momento."
#                     )
#                     return []

#                 # Construir lista de planes desde las filas y consultar la API RAG pasando este resultado como contexto
#                 plans_list = []
#                 for row in rows:
#                     plans_list.append(
#                         {
#                             "producto_id": row.get("producto_id"),
#                             "nombre": row.get("nombre"),
#                             "descripcion": row.get("descripcion"),
#                             "velocidad_bajada_mbps": row.get("velocidad_bajada_mbps"),
#                             "velocidad_subida_mbps": row.get("velocidad_subida_mbps"),
#                             "precio_mensual": (
#                                 float(row.get("precio_mensual"))
#                                 if row.get("precio_mensual") is not None
#                                 else None
#                             ),
#                             "beneficios": row.get("beneficios"),
#                         }
#                     )

#                 # Guardar planes en un slot para uso posterior
#                 # dispatcher.utter_message(
#                 #     text="He encontrado los planes disponibles. Consulto el asistente de conocimiento para darte una recomendación..."
#                 # )
#                 # Obtener la pregunta actual del usuario (si existe)
#                 user_question = (
#                     tracker.latest_message.get("text") or "¿Qué plan me recomiendas?"
#                 )

#                 # Preparar payload para la API RAG: enviamos la pregunta y el contexto (los planes)
#                 chat_history_rasa_format = self._get_chat_history(tracker)
#                 payload = {
#                     "question": user_question,
#                     "context": repr(plans_list),
#                     "history": chat_history_rasa_format,
#                 }
#                 print(f"Payload RAG con contexto de planes: {payload}")

#                 try:
#                     resp = requests.post(RAG_API_REPHRASE_URL, json=payload, timeout=60)
#                     resp.raise_for_status()
#                     rag_json = resp.json()
#                     answer = rag_json.get(
#                         "answer", "Lo siento, no obtuve una recomendación clara."
#                     )
#                     dispatcher.utter_message(text=answer)
#                 except requests.exceptions.ConnectionError:
#                     print(f"ERROR RAG: conexión fallida a {RAG_API_URL}")
#                     dispatcher.utter_message(
#                         text="No puedo conectar con el motor de conocimiento ahora mismo. Te muestro la lista de planes disponibles."
#                     )
#                     # Fallback: mostrar resumen simple de planes
#                     lines = []
#                     for p in plans_list[:5]:
#                         lines.append(
#                             f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
#                         )
#                     dispatcher.utter_message(
#                         text=(
#                             "\n".join(lines) if lines else "No hay planes para mostrar."
#                         )
#                     )
#                 except requests.exceptions.HTTPError as e:
#                     print(f"ERROR RAG API: status {resp.status_code} - {e}")
#                     dispatcher.utter_message(
#                         text="El servicio de recomendaciones tuvo un error. Aquí están los planes encontrados:"
#                     )
#                     lines = [
#                         f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
#                         for p in plans_list[:5]
#                     ]
#                     dispatcher.utter_message(
#                         text=(
#                             "\n".join(lines) if lines else "No hay planes para mostrar."
#                         )
#                     )
#                 except Exception as e:
#                     print(f"ERROR al consultar RAG o procesar planes: {e}")
#                     dispatcher.utter_message(
#                         text="Ocurrió un error inesperado al obtener la recomendación."
#                     )

#                 return []

#         except psycopg2.OperationalError as e:
#             print(f"POSTGRES ERROR (fetch plans): {e}")
#             dispatcher.utter_message(
#                 text="No pude conectar a la base de datos. Intenta más tarde."
#             )
#             return []
#         except Exception as e:
#             print(f"DB QUERY ERROR (fetch plans): {e}")
#             dispatcher.utter_message(text="Ocurrió un error al obtener los planes.")
#             return []
#         finally:
#             if conn:
#                 conn.close()

#     def _get_chat_history(self, tracker: Tracker) -> List[Tuple[str, str]]:
#         """Extrae el historial reciente en formato (user_msg, bot_msg) para la API RAG."""
#         history: List[Tuple[str, str]] = []
#         current_user_message: str = None

#         for event in tracker.events_after_latest_restart():
#             if event.get("event") == "user" and event.get("text"):
#                 current_user_message = event.get("text")

#             elif (
#                 event.get("event") == "bot"
#                 and event.get("text")
#                 and current_user_message
#             ):
#                 history.append((current_user_message, event.get("text")))
#                 current_user_message = None  # Resetea después de emparejar
#         return history[-4:]


class ValidateProductForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_product_form"

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
                    dispatcher.utter_message(text=f"Disculpa, el plan '{slot_value}' no lo tengo disponible.")
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

    #     conn = None
    #     try:
    #         conn = psycopg2.connect(
    #             host=pg_host,
    #             port=pg_port,
    #             dbname=pg_db,
    #             user=pg_user,
    #             password=pg_password,
    #             connect_timeout=5,
    #         )

    #         with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
    #             cur.execute(
    #                 """
    #                 SELECT
    #                     producto_id,
    #                     nombre,
    #                     descripcion,
    #                     velocidad_bajada_mbps,
    #                     velocidad_subida_mbps,
    #                     precio_mensual,
    #                     beneficios
    #                 FROM productos
    #                 ORDER BY precio_mensual ASC
    #                 """
    #             )

    #             rows = cur.fetchall()

    #             if not rows:
    #                 dispatcher.utter_message(
    #                     text="No hay planes activos disponibles en este momento."
    #                 )
    #                 return []

    #             # Construir lista de planes desde las filas y consultar la API RAG pasando este resultado como contexto
    #             plans_list = []
    #             for row in rows:
    #                 plans_list.append(
    #                     {
    #                         "producto_id": row.get("producto_id"),
    #                         "nombre": row.get("nombre"),
    #                         "descripcion": row.get("descripcion"),
    #                         "velocidad_bajada_mbps": row.get("velocidad_bajada_mbps"),
    #                         "velocidad_subida_mbps": row.get("velocidad_subida_mbps"),
    #                         "precio_mensual": (
    #                             float(row.get("precio_mensual"))
    #                             if row.get("precio_mensual") is not None
    #                             else None
    #                         ),
    #                         "beneficios": row.get("beneficios"),
    #                     }
    #                 )

    #             # Guardar planes en un slot para uso posterior
    #             # dispatcher.utter_message(
    #             #     text="He encontrado los planes disponibles. Consulto el asistente de conocimiento para darte una recomendación..."
    #             # )
    #             # Obtener la pregunta actual del usuario (si existe)
    #             user_question = (
    #                 tracker.latest_message.get("text") or "¿Qué plan me recomiendas?"
    #             )

    #             # Preparar payload para la API RAG: enviamos la pregunta y el contexto (los planes)
    #             chat_history_rasa_format = self._get_chat_history(tracker)
    #             payload = {
    #                 "question": user_question,
    #                 "context": repr(plans_list),
    #                 "history": chat_history_rasa_format,
    #             }
    #             print(f"Payload RAG con contexto de planes: {payload}")

    #             try:
    #                 resp = requests.post(RAG_API_REPHRASE_URL, json=payload, timeout=60)
    #                 resp.raise_for_status()
    #                 rag_json = resp.json()
    #                 answer = rag_json.get(
    #                     "answer", "Lo siento, no obtuve una recomendación clara."
    #                 )
    #                 dispatcher.utter_message(text=answer)
    #             except requests.exceptions.ConnectionError:
    #                 print(f"ERROR RAG: conexión fallida a {RAG_API_URL}")
    #                 dispatcher.utter_message(
    #                     text="No puedo conectar con el motor de conocimiento ahora mismo. Te muestro la lista de planes disponibles."
    #                 )
    #                 # Fallback: mostrar resumen simple de planes
    #                 lines = []
    #                 for p in plans_list[:5]:
    #                     lines.append(
    #                         f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
    #                     )
    #                 dispatcher.utter_message(
    #                     text=(
    #                         "\n".join(lines) if lines else "No hay planes para mostrar."
    #                     )
    #                 )
    #             except requests.exceptions.HTTPError as e:
    #                 print(f"ERROR RAG API: status {resp.status_code} - {e}")
    #                 dispatcher.utter_message(
    #                     text="El servicio de recomendaciones tuvo un error. Aquí están los planes encontrados:"
    #                 )
    #                 lines = [
    #                     f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
    #                     for p in plans_list[:5]
    #                 ]
    #                 dispatcher.utter_message(
    #                     text=(
    #                         "\n".join(lines) if lines else "No hay planes para mostrar."
    #                     )
    #                 )
    #             except Exception as e:
    #                 print(f"ERROR al consultar RAG o procesar planes: {e}")
    #                 dispatcher.utter_message(
    #                     text="Ocurrió un error inesperado al obtener la recomendación."
    #                 )

    #             return []

    #     except psycopg2.OperationalError as e:
    #         print(f"POSTGRES ERROR (fetch plans): {e}")
    #         dispatcher.utter_message(
    #             text="No pude conectar a la base de datos. Intenta más tarde."
    #         )
    #         return []
    #     except Exception as e:
    #         print(f"DB QUERY ERROR (fetch plans): {e}")
    #         dispatcher.utter_message(text="Ocurrió un error al obtener los planes.")
    #         return []
    #     finally:
    #         if conn:
    #             conn.close()

    # def _get_chat_history(self, tracker: Tracker) -> List[Tuple[str, str]]:
    #     """Extrae el historial reciente en formato (user_msg, bot_msg) para la API RAG."""
    #     history: List[Tuple[str, str]] = []
    #     current_user_message: str = None

    #     for event in tracker.events_after_latest_restart():
    #         if event.get("event") == "user" and event.get("text"):
    #             current_user_message = event.get("text")

    #         elif (
    #             event.get("event") == "bot"
    #             and event.get("text")
    #             and current_user_message
    #         ):
    #             history.append((current_user_message, event.get("text")))
    #             current_user_message = None  # Resetea después de emparejar
    #     return history[-4:]
