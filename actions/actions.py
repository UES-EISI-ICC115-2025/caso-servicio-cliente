# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

from typing import Any, Text, Dict, List
from rasa_sdk.types import DomainDict
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.events import SlotSet, ActiveLoop
from rasa_sdk.executor import CollectingDispatcher
import re
import mysql.connector
from mysql.connector import Error

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
        dispatcher.utter_message(text="Consultando planes...")
        # Parámetros de conexión MYSQL
        config = {
            "user": "icc115",
            "password": "icc115",
            "host": "172.16.2.66",
            "database": "icc115",
        }
        try:
            # Establecer la conexión con la base de datos
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT producto_id, nombre, descripcion, velocidad_bajada_mbps, velocidad_subida_mbps, precio_mensual, beneficios FROM productos")
                productos = cursor.fetchall()
                # Construir prompt para Ollama
                necesidades = tracker.latest_message.get("text", "")
                productos_str = "\n".join([
                    f"ID: {p['producto_id']}, Nombre: {p['nombre']}, Descripción: {p['descripcion']}, Bajada: {p['velocidad_bajada_mbps']} Mbps, Subida: {p['velocidad_subida_mbps']} Mbps, Precio: {p['precio_mensual']}, Beneficios: {p['beneficios']}"
                    for p in productos
                ])
                prompt = (
                    f"El cliente pregunta: {necesidades}\n"
                    f"Estos son los productos disponibles:\n{productos_str}\n"
                    "¿Cuál de estos productos se acomoda mejor a las necesidades del cliente? Responde solo con el nombre, motivo y precio, sino solicita ninguno en especifico dale todos en formato de tabla."
                )

                # Consulta a Ollama
                respuesta = ollama.chat(model="tu_modelo_ollama", messages=[{"role": "user", "content": prompt}])
                recomendacion = respuesta['message']['content']

                dispatcher.utter_message(text=f"Según tus necesidades, te recomiendo: {recomendacion}")

                print(f"{cursor.rowcount} registros insertados correctamente.")

        except Error as e:
            print(f"Error al insertar múltiples registros: {e}")

        finally:
            # Cerrar el cursor y la conexión
            if "conn" in locals() and conn.is_connected():
                cursor.close()
                conn.close()
                print("Conexión a MySQL cerrada.")

        return []

class ActionSetNecesidad(Action):
    def name(self) -> str:
        return "action_set_necesidad"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        # Get the current user message as the necesidad value
        # Get the intent name from the latest message
        intent_name = tracker.latest_message.get("intent", {}).get("name", "")
        if intent_name:
            match intent_name:
                case "interes_planes":
                    necesidad_value = "contratacion"
                case "problema_facturacion":
                    necesidad_value = "facturacion"
                case "problema_tecnico":
                    necesidad_value = "asistencia_tecnica"
                case _:  # Default case (wildcard)
                    necesidad_value = None

        # Set the necesidad slot with the current document value
        return [SlotSet("necesidad", necesidad_value)]

class ActionConfirmNombreCompleto(Action):
    def name(self) -> Text:
        return "action_confirm_nombre_completo"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # Obtiene el nombre temporalmente almacenado
        nombre_confirmado = tracker.get_slot("temp_nombre_completo")

        if nombre_confirmado:
            dispatcher.utter_message(
                text=f"Gracias, {nombre_confirmado}. Tu nombre completo ha sido registrado."
            )
            # Si el usuario confirma, mueve el nombre al slot final
            return [SlotSet("nombre_completo", nombre_confirmado)]
        else:
            return []


class ValidateInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_login_form"

    def validate_email(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida el valor del slot 'email'."""
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

        if re.match(email_regex, slot_value):
            # dispatcher.utter_message(
            #     text=f"El correo electrónico '{slot_value}' es válido."
            # )
            return {"email": slot_value}
        else:
            # dispatcher.utter_message(response="utter_wrong_email")
            return {"email": None}

    def validate_dui(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida el valor del slot 'dui'."""

        # Validación del formato y dígito verificador para el DUI de El Salvador
        if re.match(r"^\d{8}-\d$", slot_value):
            digits, digit_veri = slot_value.split("-")
            suma = 0
            for i in range(len(digits)):
                suma += (9 - i) * int(digits[i])

            if int(digit_veri) == (10 - (suma % 10)) % 10:
                # dispatcher.utter_message(text=f"El DUI '{slot_value}' es válido.")
                return {"dui": slot_value}
            else:
                # dispatcher.utter_message(response="utter_wrong_dui")
                return {"dui": None}
        else:
            # dispatcher.utter_message(response="utter_wrong_dui")
            return {"dui": None}

    def validate_telefono(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida el valor del slot 'telefono'."""
        telefono_regex = r"^(?:\+503)?[\s-]?\d{4}[\s-]?\d{4}$"

        if re.match(telefono_regex, slot_value):
            # dispatcher.utter_message(
            #     text=f"El número de teléfono '{slot_value}' es válido."
            # )
            return {"telefono": slot_value}
        else:
            # dispatcher.utter_message(response="utter_wrong_telefono")
            return {"telefono": None}

    def validate_nombre_completo(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Valida el valor del slot 'nombre_completo'."""
        nombre_completo_regex = r"^\s*(?:\S+\s+){2,9}\S+\s*$"

        # Captura el mensaje completo del usuario y lo usa como valor del slot
        full_text = tracker.latest_message.get("text", "")
        if isinstance(full_text, str) and full_text.strip():
            slot_value = " ".join(full_text.strip().split())

        if re.match(nombre_completo_regex, slot_value):
            # dispatcher.utter_message(text=f"El nombre '{slot_value}' es válido.")

            return {"nombre_completo": slot_value}
        else:
            # dispatcher.utter_message(response="utter_wrong_nombre_completo")
            return {"nombre_completo": None}