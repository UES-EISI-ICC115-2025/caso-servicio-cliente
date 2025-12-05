from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from dotenv import load_dotenv, find_dotenv

from actions.calificacion import save_calificacion

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

class ActionSaveCalificacion(Action):
    def name(self) -> Text:
        return "action_save_calificacion"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        session_id = tracker.sender_id
        user_id = tracker.get_slot("dui")  # Asumiendo que tienes un slot user_id
        rating = tracker.get_slot("rating")
        comentarios = tracker.get_slot("comentarios")

        feedback_records = save_calificacion(session_id, user_id, rating, comentarios)

        if feedback_records:
            dispatcher.utter_message(text="¡Gracias por tu calificación y comentarios!")
        else:
            dispatcher.utter_message(text="Hubo un error al guardar tu calificación. Por favor, intenta nuevamente más tarde.")

        return []