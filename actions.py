import requests
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

print(">>> actions.py LOADED <<<")

class ActionIdentificarCliente(Action):
    def name(self) -> str:
        return "action_identificar_cliente"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
        
        # Aquí puedes agregar la lógica para verificar si el cliente ya existe
        # Obtenemos el intent del último mensaje para determinar el camino
        # ultimo_intent = tracker.latest_message.get("intent", {}).get("name")

        # # Asumimos que si el usuario mencionó "soy nuevo cliente", el slot debe ser falso
        # if ultimo_intent == "nuevo_cliente":
        #     dispatcher.utter_message(text="¡Qué bien! Un gusto que estes interesado.")
        #     return [SlotSet("cliente_existente", False)]
        
        # # Si el usuario mencionó "soy cliente" o similar, el slot puede ser verdadero
        # # Esta es la lógica para el caso de cliente existente, la incluimos para completar el ejemplo
        # # elif ultimo_intent == "identificar_cliente":
        # #     dispatcher.utter_message(text="Por favor, proporciónanos el número de teléfono asociado a tu servicio, el nombre y el DUI del titular para poder identificarte.")
        # #     return [SlotSet("cliente_existente", True)]
        
        # # Si el intent no fue claro, o por defecto
        # dispatcher.utter_message(text="Por favor, indícanos si ya eres cliente o si eres un cliente nuevo.")
        # return []
        dispatcher.utter_message(text="Identificando cliente...")
        return []

# class ActionGenerarRespuestaRag(Action):
#     def name(self):
#         return "action_generar_respuesta_rag"

#     def run(self, dispatcher, tracker, domain):
#         pregunta = tracker.latest_message.get("text")
#         resp = requests.post("http://localhost:8000/query", json={"question": pregunta})
#         dispatcher.utter_message(text=resp.json().get("answer"))
#         return []
