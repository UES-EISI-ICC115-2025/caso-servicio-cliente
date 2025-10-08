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

class ActionEnviarContrato(Action):
    def name(self) -> str:
        return "action_enviar_contrato"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Enviando el contrato al cliente...")
        # Aquí podrías agregar lógica para enviar el contrato por email, etc.
        return []
    
class ActionEnd(Action):
    def name(self) -> str:
        return "action_end"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Gracias por contactarnos. ¡Hasta luego!")
        return []

class ActionConsultarPlanesDisponibles(Action):
    def name(self) -> str:
        return "action_mostrar_planes_disponibles"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        # # Conexión a MySQL
        # conn = mysql.connector.connect(
        #     host="localhost",
        #     user="tu_usuario",
        #     password="tu_contraseña",
        #     database="tu_base_de_datos"
        # )
        # cursor = conn.cursor(dictionary=True)
        # cursor.execute("SELECT producto_id, nombre, descripcion, velocidad_bajada_mbps, velocidad_subida_mbps, precio_mensual, beneficios FROM productos")
        # productos = cursor.fetchall()
        # cursor.close()
        # conn.close()

        # # Construir prompt para Ollama
        # necesidades = tracker.latest_message.get("text", "")
        # productos_str = "\n".join([
        #     f"ID: {p['producto_id']}, Nombre: {p['nombre']}, Descripción: {p['descripcion']}, Bajada: {p['velocidad_bajada_mbps']} Mbps, Subida: {p['velocidad_subida_mbps']} Mbps, Precio: {p['precio_mensual']}, Beneficios: {p['beneficios']}"
        #     for p in productos
        # ])
        # prompt = (
        #     f"El cliente tiene las siguientes necesidades: {necesidades}\n"
        #     f"Estos son los productos disponibles:\n{productos_str}\n"
        #     "¿Cuál de estos productos se acomoda mejor a las necesidades del cliente? Responde solo con el nombre y el motivo."
        # )

        # # Consulta a Ollama
        # respuesta = ollama.chat(model="tu_modelo_ollama", messages=[{"role": "user", "content": prompt}])
        # recomendacion = respuesta['message']['content']

        # dispatcher.utter_message(text=f"Según tus necesidades, te recomiendo: {recomendacion}")
        
        dispatcher.utter_message(text="Consultando planes...")
        
        return []