from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
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

import requests  # Necesario para la llamada HTTP

# --- CONFIGURACIÓN DE LA API RAG LOCAL ---
# Este es el puerto del servidor Gunicorn que corre rasa_rag_api_server.py
RAG_API_URL = "http://localhost:8000/rag/query"
RAG_API_REPHRASE_URL = "http://localhost:8000/rag/query_with_context"


# Esta clase de formulario ahora maneja la recolección del user_id
class ValidateUserVerificationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_user_verification_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        # Solo necesitamos user_id para este ejemplo
        if tracker.get_slot("user_id") is None:
            return ["user_id"]
        return []

    def validate_user_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        # Validar el ID (simulación: debe ser al menos 9 caracteres)
        if len(str(slot_value)) >= 9:
            # Verificar que el ID exista en tu DB.
            return {"user_id": slot_value}
        else:
            dispatcher.utter_message(
                text="El ID debe tener al menos 9 caracteres. ¿Me lo puedes dar de nuevo?"
            )
            return {"user_id": None}


# Esta acción consulta a la base de datos y establece el slot 'billing_status'
class ActionCheckBillingStatus(Action):
    def name(self) -> Text:
        return "action_check_billing_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_id = tracker.get_slot("user_id")

        # 1. Lógica de simulación para estado de facturación
        # En una aplicación real, aquí va la consulta a la DB de PostgreSQL.

        status_map = {
            "cliente123": "PAGADA",
            "mora": "VENCIDA",
            "pendiente": "PENDIENTE",
        }

        # Asigna un estado basado en el ID de simulación o usa un valor por defecto
        status = status_map.get(user_id, "PENDIENTE")

        # 2. Responde al usuario y establece el slot de estado de facturación
        if status == "VENCIDA":
            dispatcher.utter_message(response="utter_billing_overdue")
        elif status == "PAGADA":
            dispatcher.utter_message(response="utter_billing_paid")
        else:
            dispatcher.utter_message(response="utter_billing_pending")

        # 3. Retorna el estado para que el diálogo pueda continuar
        return [SlotSet("billing_status", status)]


class ActionClearUserId(Action):
    def name(self) -> Text:
        return "action_clear_user_id"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Fuerza el slot user_id a None para que el formulario lo pida
        return [SlotSet("user_id", None)]


# class ActionHumanHandoff(Action):
#     def name(self) -> Text:
#         return "action_human_handoff"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:

#         # En un sistema real, este código enviaría una notificación al CRM o LiveChat
#         dispatcher.utter_message(
#             text="Te estamos transfiriendo con un agente en vivo. Por favor, espera un momento."
#         )
#         return []


# --- Configuración del LLM Destilado ---
# El modelo debe estar descargado localmente con 'ollama pull phi3'
OLLAMA_MODEL_NAME = "phi3"
OLLAMA_BASE_URL = "http://localhost:11434"


class ActionTechnicalSupportRAG(Action):
    def name(self) -> Text:
        return "action_technical_support_rag"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_question = tracker.latest_message.get("text")

        if not user_question:
            dispatcher.utter_message(text="No entendí tu pregunta. ¿Puedes repetirla?")
            return []

        # 1. Preparar Historial para la API RAG (Cliente)
        # La API RAG espera una lista de tuplas: [(user_msg, bot_msg), ...]
        chat_history_rasa_format = self._get_chat_history(tracker)

        # 2. Construir el Payload
        payload = {"question": user_question, "history": chat_history_rasa_format}

        # 3. Llamar al Microservicio RAG API (Puerto 8000)
        try:
            response = requests.post(
                RAG_API_URL,
                json=payload,
                timeout=60,  # Tiempo límite para evitar que Rasa se congele
            )
            response.raise_for_status()  # Lanza un error si el código HTTP no es 200

            rag_response = response.json()

            # 4. Enviar Respuesta de la API RAG al Usuario
            answer_text = rag_response.get(
                "answer", "Lo siento, la respuesta RAG no fue clara."
            )
            dispatcher.utter_message(text=answer_text)

        except requests.exceptions.ConnectionError:
            print(f"ERROR RAG: Falló la conexión al servidor RAG en {RAG_API_URL}")
            dispatcher.utter_message(
                text="Lo siento, el motor de soporte técnico está fuera de servicio temporalmente. ¿Quieres que te transfiera?"
            )

        except requests.exceptions.HTTPError as e:
            # Captura errores como 400 (Bad Request) o 500 (Internal Server Error en el RAG)
            print(f"ERROR RAG API: Falló la consulta con estado {response.status_code}")
            dispatcher.utter_message(
                text="Lo siento, el servidor de conocimiento técnico tuvo un fallo al procesar la consulta. Te recomiendo preguntar de otra forma."
            )

        return []

    def _get_chat_history(self, tracker: Tracker) -> List[Tuple[str, str]]:
        """Extrae el historial reciente en formato (user_msg, bot_msg) para la API RAG."""
        history: List[Tuple[str, str]] = []
        current_user_message: str = None

        for event in tracker.events_after_latest_restart():
            if event.get("event") == "user" and event.get("text"):
                current_user_message = event.get("text")

            elif (
                event.get("event") == "bot"
                and event.get("text")
                and current_user_message
            ):
                history.append((current_user_message, event.get("text")))
                current_user_message = None  # Resetea después de emparejar

        # Si hay un mensaje de usuario sin respuesta, lo añadimos como tupla incompleta para el turno actual
        if current_user_message:
            history.append((current_user_message, None))

        # La API RAG sólo necesita el historial *anterior* al turno actual.
        # El turno actual (la última pregunta del usuario) se envía en la clave "question".
        # Por lo tanto, enviamos todo el historial menos el último turno (el que está en 'user_question')

        # El historial de Rasa ya excluye el último turno del usuario si lo extraemos
        # correctamente, pero para seguridad, limitamos las interacciones anteriores.

        # Dejaremos la lógica simple para enviar los últimos 4 pares de mensajes anteriores
        return history[-4:]


class ActionFetchUserData(Action):
    def name(self) -> str:
        return "action_fetch_user_data"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        user_id = tracker.get_slot("user_id")
        if not user_id:
            dispatcher.utter_message(
                text="¿Me ayudas con tu DUI para buscarte en el sistema?"
            )
            return []

        # Leer credenciales desde variables de entorno; cambiar según sea necesario.
        pg_host = os.getenv("PG_HOST", "localhost")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_db = os.getenv("PG_DB", "mydb")
        pg_user = os.getenv("PG_USER", "postgres")
        pg_password = os.getenv("PG_PASSWORD", "")

        # Imprimir/registrar variables de entorno relevantes para depuración (con cuidado con secretos)
        env_debug = {
            "PG_HOST": pg_host,
            "PG_PORT": pg_port,
            "PG_DB": pg_db,
            "PG_USER": pg_user,
            "PG_PASSWORD": pg_password,
            # "RAG_API_URL": os.getenv("RAG_API_URL", RAG_API_URL),
            # "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL),
        }

        # Registrar en logs del servidor (ocultando la contraseña)
        log_copy = env_debug.copy()
        log_copy["PG_PASSWORD"] = (
            "[REDACTED]" if env_debug["PG_PASSWORD"] else "[EMPTY]"
        )
        print("ENV DEBUG:", log_copy)

        # Notificar al usuario de forma segura (sin exponer la contraseña)
        dispatcher.utter_message(
            text=(
                f"Conectando a la base de datos en {env_debug['PG_HOST']}:{env_debug['PG_PORT']}/"
                f"{env_debug['PG_DB']} como {env_debug['PG_USER']}. "
                f"RAG_API: {env_debug['RAG_API_URL']}"
            )
        )
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
                # Ajusta la consulta a la estructura real de tu DB.
                cur.execute(
                    "SELECT name, billing_status, account_balance FROM customers WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()

                if not row:
                    dispatcher.utter_message(
                        text="No encontré información para ese ID. ¿Estás seguro de que es correcto?"
                    )
                    return [SlotSet("billing_status", None)]

                name = row.get("name")
                billing_status = row.get("billing_status")
                balance = row.get("account_balance")

                # Mensaje de retorno al usuario (puedes usar templates en domain.yml en vez de texto plano)
                dispatcher.utter_message(
                    text=f"Cliente: {name}. Estado de facturación: {billing_status}. Saldo: {balance}"
                )

                # Establecer slots para que el diálogo los use
                return [
                    SlotSet("user_name", name),
                    SlotSet("billing_status", billing_status),
                    SlotSet(
                        "account_balance",
                        float(balance) if balance is not None else None,
                    ),
                ]

        except psycopg2.OperationalError as e:
            print(f"POSTGRES ERROR: {e}")
            dispatcher.utter_message(
                text="No pude conectar con la base de datos en este momento. Intenta de nuevo más tarde."
            )
            return []
        except Exception as e:
            print(f"DB QUERY ERROR: {e}")
            dispatcher.utter_message(
                text="Ocurrió un error al consultar la base de datos."
            )
            return []
        finally:
            if conn:
                conn.close()


# class ActionFetchProductPlans(Action):
#     def name(self) -> Text:
#         return "action_choose_product_plan"

#     def run(
#         self,
#         dispatcher: CollectingDispatcher,
#         tracker: Tracker,
#         domain: Dict[Text, Any],
#     ) -> List[Dict[Text, Any]]:

#         # Leer credenciales desde variables de entorno
#         pg_host = os.getenv("PG_HOST", "localhost")
#         pg_port = os.getenv("PG_PORT", "5432")
#         pg_db = os.getenv("PG_DB", "mydb")
#         pg_user = os.getenv("PG_USER", "postgres")
#         pg_password = os.getenv("PG_PASSWORD", "")
#         print(pg_host, pg_port, pg_db, pg_user, pg_password)

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
#                 dispatcher.utter_message(
#                     text="Dame un momento, estoy validando el plan seleccionado"
#                 )
#                 # Obtener la pregunta actual del usuario (si existe)
#                 user_question = "¿cual es el **producto_id** del plan seleccionado?"

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
#                         "answer",
#                         "Lo siento, no pude validar el plan seleccionado. Podrías darme más detalles?",
#                     )
#                     dispatcher.utter_message(text=answer)

#                     cur.execute(
#                         """
#                         SELECT
#                             producto_id,
#                             nombre,
#                             descripcion,
#                             velocidad_bajada_mbps,
#                             velocidad_subida_mbps,
#                             precio_mensual,
#                             beneficios
#                         FROM productos
#                         where producto_id = %s
#                         ORDER BY precio_mensual ASC
#                         """,
#                         (answer.strip(),),
#                     )

#                     rows = cur.fetchone()
#                     if not rows:
#                         dispatcher.utter_message(text="Lo siento, no pude validar el plan seleccionado. Podrías darme más detalles?")
#                     else:
#                         dispatcher.utter_message(
#                             text=f"Perfecto, tu plan seleccionado es: {rows.get('nombre')} de ${rows.get('precio_mensual')} con {rows.get('velocidad_bajada_mbps')} Mbps y {rows.get('velocidad_subida_mbps')} Mbps de subida"
#                         )
#                         set_slots = [
#                             SlotSet("producto_id", rows.get("producto_id")),
#                             SlotSet("nombre_producto", rows.get("nombre")),
#                             SlotSet(
#                                 "precio_producto", float(rows.get("precio_mensual"))
#                                 if rows.get("precio_mensual") is not None
#                                 else None
#                             ),
#                         ]
#                         return set_slots
#                 except requests.exceptions.ConnectionError:
#                     print(f"ERROR RAG: conexión fallida a {RAG_API_URL}")

#                     # Fallback: mostrar resumen simple de planes
#                     search_results = []
#                     for p in plans_list:
#                         if (
#                             user_question
#                             in f"{p['nombre']} - ${p['precio_mensual']} - ${p['descripcion']} - ${p['beneficios']} - {p['velocidad_bajada_mbps']} Mbps - {p['velocidad_subida_mbps']} Mbps"
#                         ):
#                             search_results.append(
#                                 f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
#                             )
#                     if len(search_results) == 0:
#                         lines = []
#                         for p in plans_list:
#                             lines.append(
#                                 f"{p['nombre']} de ${p['precio_mensual']} con {p['velocidad_bajada_mbps']} Mbps y {p['velocidad_subida_mbps']} Mbps de subida"
#                             )
#                         dispatcher.utter_message(
#                             text="No se encontre el plan seleccionado, me puedes decir el nombre del plan por favor. tengo estos planes disponibles:"
#                         )
#                         dispatcher.utter_message(
#                             text=(
#                                 "\n".join(lines)
#                                 if lines
#                                 else "Lo siento, no hay planes disponibles."
#                             )
#                         )
#                     elif len(search_results) == 1:
#                         dispatcher.utter_message(
#                             text="Perfecto, tu plan seleccionado es:"
#                             + "\n".join(search_results)
#                         )
#                     else:
#                         dispatcher.utter_message(
#                             text="He encontrado varios planes que coinciden con tu selección:"
#                             + "\n".join(search_results)
#                         )
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
#                         text="Ocurrió un error inesperado al validar el plan."
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
