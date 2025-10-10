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
import os
import requests

CUSTOM_ERROR_MESSAGE = "¡Hey! Estoy atascado. Ya vengo voy por un café. En eso, inténta de nuevo, bien que ya estoy de vuelta."
# Parámetros de conexión MYSQL
config = {
    "user": "icc115",
    "password": "icc115",
    "host": "172.16.2.66",
    "database": "icc115",
}


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


def consultar_ollama(contexto: str, question: str, adicional: str) -> str:
    # Consulta a API REST (RAG)
    try:
        rag_api_url = os.getenv("RAG_API_URL", "http://localhost:8001/rephrase")
        payload = {"contexto": contexto, "question": question, "adicional": adicional}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(rag_api_url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()

        if "application/json" in (resp.headers.get("Content-Type") or ""):
            data = resp.json()
            respuesta = data.get("answer")

        if not respuesta:
            raise ValueError("No se recibió una respuesta válida de la API RAG.")
    except Exception as e:
        respuesta = CUSTOM_ERROR_MESSAGE
        print(f"Error al consultar la API RAG: {e}")
    return respuesta


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

        try:
            # Establecer la conexión con la base de datos
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT producto_id, nombre, descripcion, velocidad_bajada_mbps, velocidad_subida_mbps, precio_mensual, beneficios FROM productos"
                )
                productos = cursor.fetchall()
                # Construir prompt para Ollama
                productos_str = "\n".join(
                    [
                        f"ID: {p['producto_id']}, Nombre: {p['nombre']}, Descripción: {p['descripcion']}, Bajada: {p['velocidad_bajada_mbps']} Mbps, Subida: {p['velocidad_subida_mbps']} Mbps, Precio: {p['precio_mensual']}, Beneficios: {p['beneficios']}"
                        for p in productos
                    ]
                )

                # Obtener todos los mensajes del usuario
                mensajes_usuario = [
                    {
                        "message": e.get("text"),
                        "sender": e.get("event"),
                    }
                    for e in tracker.events
                    if (e.get("event") == "user" or e.get("event") == "bot")
                ]

                # Obtener las últimas 10 entradas
                ultimos = "\n".join(
                    [f"{msg['sender']}: {msg['message']}" for msg in mensajes_usuario[-10:]]
                )

                # Mostrar en consola (para debug)
                print("Historial de usuario:", ultimos)

                # Consulta a Ollama
                respuesta = consultar_ollama(
                    contexto=productos_str,
                    question=ultimos,
                    adicional="dile los planes disponibles, no repitas las frases"
                    "solo puedes hacerle una pregunta",
                )
                dispatcher.utter_message(text=respuesta)

        except Error as e:
            print(f"Error al consultar planes disponibles: {e}")

        finally:
            # Cerrar el cursor y la conexión
            if "conn" in locals() and conn.is_connected():
                cursor.close()
                conn.close()
                print("Conexión a MySQL cerrada.")

        return []


class ActionConsultarCerrarVenta(Action):
    def name(self) -> str:
        return "action_cerrar_venta"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        try:
            # Establecer la conexión con la base de datos
            conn = mysql.connector.connect(**config)

            if conn.is_connected():
                cursor = conn.cursor(dictionary=True)
                cursor.execute(
                    "SELECT producto_id, nombre, descripcion, velocidad_bajada_mbps, velocidad_subida_mbps, precio_mensual, beneficios FROM productos"
                )
                productos = cursor.fetchall()
                # Construir prompt para Ollama
                productos_str = "\n".join(
                    [
                        f"ID: {p['producto_id']}, Nombre: {p['nombre']}, Descripción: {p['descripcion']}, Bajada: {p['velocidad_bajada_mbps']} Mbps, Subida: {p['velocidad_subida_mbps']} Mbps, Precio: {p['precio_mensual']}, Beneficios: {p['beneficios']}"
                        for p in productos
                    ]
                )

                # Obtener todos los mensajes del usuario
                mensajes_usuario = [
                    {
                        "message": e.get("text"),
                        "sender": e.get("event"),
                    }
                    for e in tracker.events
                    if (e.get("event") == "user" or e.get("event") == "bot")
                ]

                # Obtener las últimas 10 entradas
                ultimos = "\n".join(
                    [f"{msg['sender']}: {msg['message']}" for msg in mensajes_usuario[-10:]]
                )

                # Mostrar en consola (para debug)
                print("Historial de usuario:", ultimos)
                # Recuperar la entidad 'plan_elegido' del último mensaje del usuario
                plan_elegido = next(
                    tracker.get_latest_entity_values("plan_elegido"), None
                )

                # Consulta a Ollama
                respuesta = consultar_ollama(
                    contexto=productos_str,
                    question=ultimos,
                    adicional=f"Cierra la venta, el cliente eligio el plan {plan_elegido}"
                    "Que te proporcione los datos de nombre completo, correo electrónico y teléfono uno a la vez."
                    "Una vez completado dile que le enviaras el contrato por correo",
                )
                dispatcher.utter_message(text=respuesta)

        except Error as e:
            print(f"Error al consultar cerrar la venta: {e}")

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
                case "elegir_plan":
                    necesidad_value = "cerrar_venta"
                case _:  # Default case (wildcard)
                    necesidad_value = None

        # Set the necesidad slot with the current document value
        return [SlotSet("necesidad", necesidad_value)]


def buscar_usuario(
    self,
    email: str = None,
    telefono: str = None,
    nombre_completo: str = None,
) -> Dict[Text, Any]:
    """Busca un usuario en la base de datos según email, teléfono o nombre completo."""
    try:
        conn = mysql.connector.connect(**config)
        if conn.is_connected():
            cursor = conn.cursor(dictionary=True)
            query = """
                SELECT BIN_TO_UUID(user_id) as user_id, nombre, email, telefono 
                FROM users
                WHERE 
                    (%s is null or email = %s)
                    AND (%s is null or telefono = %s)
                    AND (%s is null or %s  LIKE concat('%',nombre)  COLLATE utf8mb4_general_ci) 
                    or (%s LIKE concat(nombre, '%') COLLATE utf8mb4_general_ci)
                LIMIT 1
            """
            cursor.execute(
                query,
                (
                    email,
                    email,
                    telefono,
                    telefono,
                    nombre_completo,
                    nombre_completo,
                    nombre_completo,
                ),
            )
            usuario = cursor.fetchone()
            return usuario if usuario else {}
    except Error as e:
        print(f"Error al buscar usuario: {e}")
        return {}
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


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
        print(f"Validando nombre_completo: '{slot_value}'")

        # Captura el mensaje completo del usuario y lo usa como valor del slot
        full_text = tracker.latest_message.get("text", "")
        if isinstance(full_text, str) and full_text.strip():
            slot_value = " ".join(full_text.strip().split())

        if re.match(nombre_completo_regex, slot_value):
            # dispatcher.utter_message(text=f"El nombre '{slot_value}' es válido.")
            usuario = self.buscar_usuario(
                nombre_completo=slot_value or None,
                email=tracker.get_slot("email") or None,
                telefono=tracker.get_slot("telefono") or None,
            )
            if usuario:
                # dispatcher.utter_message(text=f"Usuario encontrado: {usuario}")
                print(f"Usuario encontrado: {usuario}")
                slot_value = usuario.get("nombre")
            return {
                "nombre_completo": slot_value,
            }
        else:
            # dispatcher.utter_message(response="utter_wrong_nombre_completo")
            return {"nombre_completo": None}


class ActionSetCliente(Action):
    def name(self) -> str:
        return "action_set_cliente"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        nombre_completo = tracker.get_slot("nombre_completo")

        usuario = self.buscar_usuario(nombre_completo=nombre_completo)
        if usuario:
            nombre_completo = usuario.get("nombre")
            dispatcher.utter_message(text=f"Cliente encontrado: {nombre_completo}")
            return [
                SlotSet("cliente", nombre_completo),
                SlotSet("user_id", usuario.get("user_id")),
            ]
        else:
            dispatcher.utter_message(text="No se encontró el cliente.")
            return []
