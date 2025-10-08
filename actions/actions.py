# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List

from rasa_sdk import Action, Tracker
from rasa_sdk.events import SlotSet
from rasa_sdk.executor import CollectingDispatcher
#
#
class ActionHelloWorld(Action):

    def name(self) -> Text:
        return "action_hello_world"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")

        return []
    
class ActionIdentificarCliente(Action):
    def name(self) -> str:
        return "action_identificar_cliente"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]):
    
        dispatcher.utter_message(text="Identificando cliente...")
        return []

class ActionValidarPlan(Action):
    def name(self):
        return "action_validar_plan"

    def run(self, dispatcher, tracker, domain):
        plan_usuario = tracker.latest_message.get("text").lower()
        
        # Lista de planes disponibles (puedes incluir varias variantes)
        planes_disponibles = ["plan a", "plan b", "plan c"]
        
        # Verifica si el mensaje coincide con cualquiera
        if any(plan in plan_usuario for plan in planes_disponibles):
            dispatcher.utter_message(text=f"Perfecto, {plan_usuario} está disponible.")
            return [SlotSet("plan_valido", True), SlotSet("plan_elegido", plan_usuario)]
        else:
            dispatcher.utter_message(text=f"Lo siento, {plan_usuario} no está disponible.")
            return [SlotSet("plan_valido", False), SlotSet("planes_disponibles", planes_disponibles)]
