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

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Hello World!")

        return []


class ActionIdentificarCliente(Action):
    def name(self) -> str:
        return "action_identificar_cliente"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ):

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
            dispatcher.utter_message(
                text=f"Lo siento, {plan_usuario} no está disponible."
            )
            return [
                SlotSet("plan_valido", False),
                SlotSet("planes_disponibles", planes_disponibles),
            ]


class ActionEnviarContrato(Action):
    def name(self) -> str:
        return "action_enviar_contrato"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Enviando el contrato al cliente...")
        # Aquí podrías agregar lógica para enviar el contrato por email, etc.
        return []


class ActionEnd(Action):
    def name(self) -> str:
        return "action_end"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        dispatcher.utter_message(text="Gracias por contactarnos. ¡Hasta luego!")
        return []


class ActionConsultarPlanesDisponibles(Action):
    def name(self) -> str:
        return "action_mostrar_planes_disponibles"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
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


def validar_telefono(telefono: str) -> bool:
    """
    Valida si el teléfono es un número válido.
    Debe contener solo dígitos y tener al menos 8 caracteres.
    """
    return telefono is not None and telefono.isdigit() and len(telefono) >= 8


def validar_email(email: str) -> bool:
    """
    Valida si el email es válido.
    Debe contener un "@" y un ".".
    """
    return email is not None and "@" in email and "." in email


def validar_dui(dui: str) -> bool:
    """
    Valida si el DUI es válido.
    Debe contener entre 6 y 12 caracteres.
    """
    return dui is not None and len(dui) >= 6 and len(dui) <= 12


def validar_nombre(nombre: str) -> bool:
    """
    Valida si el nombre es válido.
    Debe tener al menos 3 caracteres y solo letras y espacios.
    """
    return (
        nombre is not None
        and isinstance(nombre, str)
        and len(nombre.strip()) >= 3
        and all(c.isalpha() or c.isspace() for c in nombre)
    )


def obtener_datos_cliente(tracker: Tracker) -> Dict[str, Any]:
    nombre = next(tracker.get_latest_entity_values("nombre"), None)
    dui = next(tracker.get_latest_entity_values("dui"), None)
    telefono = next(tracker.get_latest_entity_values("telefono"), None)
    email = next(tracker.get_latest_entity_values("email"), None)

    campos_faltantes = []
    campos_invalidos = []

    if not validar_nombre(nombre):
        campos_invalidos.append("nombre")
    if not nombre:
        campos_faltantes.append("nombre")

    if not validar_email(email):
        campos_invalidos.append("email")
    if not email:
        campos_faltantes.append("email")

    if not validar_telefono(telefono):
        campos_invalidos.append("teléfono")
    if not telefono:
        campos_faltantes.append("teléfono")

    if not validar_dui(dui):
        campos_invalidos.append("DUI")
    if not dui:
        campos_faltantes.append("DUI")

    return {
        "nombre": nombre,
        "email": email,
        "telefono": telefono,
        "dui": dui,
        "campos_faltantes": campos_faltantes,
        "campos_invalidos": campos_invalidos,
    }


class ActionModificarDatosCliente(Action):
    def name(self) -> str:
        return "action_modificar_datos_cliente"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        datos = obtener_datos_cliente(tracker)

        updates = []
        if datos["nombre"] and datos["nombre"] != tracker.get_slot("nombre"):
            updates.append(SlotSet("nombre", datos["nombre"]))
        if datos["email"] and datos["email"] != tracker.get_slot("email"):
            updates.append(SlotSet("email", datos["email"]))
        if datos["telefono"] and datos["telefono"] != tracker.get_slot("telefono"):
            updates.append(SlotSet("telefono", datos["telefono"]))
        if datos["dui"] and datos["dui"] != tracker.get_slot("dui"):
            updates.append(SlotSet("dui", datos["dui"]))
        if updates:
            dispatcher.utter_message(
                text="Los siguientes datos han sido modificados: " + ", ".join(updates)
            )
        return updates


class ActionValidarDatosCliente(Action):
    def name(self) -> str:
        return "action_validar_datos_cliente"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        datos = obtener_datos_cliente(tracker)
        campos_invalidos = datos["campos_invalidos"]
        campos_faltantes = datos["campos_faltantes"]
        slots = []
        if len(campos_invalidos) > 0:
            slots.append(SlotSet("datos_validos", False))
            if "nombre" in campos_faltantes:
                dispatcher.utter_message(text="Por favor, indícame tu nombre.")
                slots.append(SlotSet("nombre", None))
            elif "nombre" in campos_invalidos:
                dispatcher.utter_message(
                    text=f"El nombre {datos['nombre']} no es válido. Debe tener al menos 3 caracteres y solo letras y espacios."
                )
                slots.append(SlotSet("nombre", None))
            slots.append(SlotSet("nombre", datos["nombre"]))

            if "email" in campos_faltantes:
                dispatcher.utter_message(text="Por favor, indícame tu email.")
                slots.append(SlotSet("email", None))
            elif "email" in campos_invalidos:
                dispatcher.utter_message(
                    text=f"El email {datos['email']} no es válido. Debe contener un '@' y un '.'."
                )
                slots.append(SlotSet("email", None))
                slots.append(SlotSet("datos_validos", False))
            slots.append(SlotSet("email", datos["email"]))
            
            if "teléfono" in campos_faltantes:
                dispatcher.utter_message(text="Por favor, indícame tu teléfono.")
                slots.append(SlotSet("telefono", None))
                slots.append(SlotSet("datos_validos", False))
            elif "teléfono" in campos_invalidos:
                dispatcher.utter_message(
                    text=f"El teléfono {datos['telefono']} no es válido. Debe contener solo dígitos y tener al menos 8 caracteres."
                )
                slots.append(SlotSet("telefono", None))
                slots.append(SlotSet("datos_validos", False))
            slots.append(SlotSet("telefono", datos["telefono"]))

            if "DUI" in campos_faltantes:
                dispatcher.utter_message(text="Por favor, indícame tu DUI.")
                slots.append(SlotSet("dui", None))
                slots.append(SlotSet("datos_validos", False))
            elif "DUI" in campos_invalidos:
                dispatcher.utter_message(
                    text=f"El DUI {datos['dui']} no es válido. Debe contener entre 6 y 12 caracteres."
                )
                slots.append(SlotSet("dui", None))
                slots.append(SlotSet("datos_validos", False))
            slots.append(SlotSet("dui", datos["dui"]))
        else:
            # Todos los campos son válidos
            slots.append(SlotSet("datos_validos", True))
            slots.append(SlotSet("nombre", datos["nombre"]))
            slots.append(SlotSet("email", datos["email"]))
            slots.append(SlotSet("telefono", datos["telefono"]))
            slots.append(SlotSet("dui", datos["dui"]))
            mensaje = f"Por favor confirma que los siguientes datos son correctos:\nNombre: {datos['nombre']}\nEmail: {datos['email']}\nTeléfono: {datos['telefono']}\nDUI: {datos['dui']}"
            dispatcher.utter_message(text=mensaje)

        return slots
