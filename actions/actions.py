from typing import Any, Text, Dict, List, Tuple
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

import requests  # Necesario para la llamada HTTP

# --- CONFIGURACIÓN DE LA API RAG LOCAL ---
# Este es el puerto del servidor Gunicorn que corre rasa_rag_api_server.py
RAG_API_URL = "http://localhost:8000/rag/query"


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
                timeout=15,  # Tiempo límite para evitar que Rasa se congele
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
