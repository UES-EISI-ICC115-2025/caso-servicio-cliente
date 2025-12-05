import re
from rasa_sdk.events import ActiveLoop, SlotSet
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from rasa_sdk.types import DomainDict
import os
from dotenv import load_dotenv, find_dotenv

from actions.contrataciones.fetch_product_plans import fetch_product_plans, find_product

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

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


class ActionDeactivateContratoForm(Action):
    def name(self) -> Text:
        return "action_deactivate_contrato_form"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:
        # dispatcher.utter_message(text="Has cancelado el proceso de contratación.")
        return [
            ActiveLoop(None),
            SlotSet("plan", None),
            SlotSet("producto_id", None),
            SlotSet("nombre_producto", None),
            SlotSet("precio_producto", None),
            SlotSet("nombre", None),
            SlotSet("email", None),
            SlotSet("dui", None),
            SlotSet("telefono", None),
            SlotSet("direccion", None),
            SlotSet("apellido", None),
            SlotSet("requested_slot", None),
        ]


class ValidateContratoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_contrato_form"

    def validate_plan(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validar que el producto seleccionado esté en nuestra lista de productos válidos."""
        raw_product = None
        # Verificar si el último intento fue 'choose_plan' o 'negociacion_aceptar_oferta'
        last_intent = tracker.latest_message.get("intent", {}).get("name")

        if last_intent == "choose_plan":
            # Buscar la entidad 'plan' en el mensaje
            plan_entity = next(
                (
                    e.get("value")
                    for e in tracker.latest_message.get("entities", [])
                    if e.get("entity") == "plan"
                ),
                None,
            )

            if plan_entity:
                raw_product = plan_entity

        elif last_intent == "negociacion_aceptar_oferta":
            # Obtener las últimas 3 mensajes que el bot envió
            last_bot_utterances = [
                event
                for event in reversed(tracker.events)
                if event.get("event") == "bot"
            ]
            last_five_texts = [u.get("text", "") for u in last_bot_utterances[:5]]
            print(f"Últimas 5 utterances del bot: {last_five_texts}")

            # Intentar extraer el nombre del producto buscando coincidencias en esas 5 utterances
            productos_disponibles = fetch_product_plans()
            raw_product = None
            for texto in last_five_texts:
                if not texto:
                    continue
                for producto in productos_disponibles:
                    print(
                        f"Buscando '{producto['nombre'].lower()}' en '{texto.lower()}'"
                    )
                    producto_nombre = producto["nombre"].lower()
                    if producto_nombre in texto.lower():
                        print(
                            f"¡Coincidencia encontrada! '{producto_nombre}' está en el texto."
                        )
                        raw_product = producto["nombre"]
                        break
                if raw_product:
                    return {
                        "plan": raw_product,
                        "producto_id": producto["producto_id"],
                        "nombre_producto": producto["nombre"],
                        "precio_producto": producto["precio_mensual"],
                    }
        elif (
            last_intent == "negociacion_cancelar_desistir"
            or last_intent == "negociacion_postponer_decision"
        ):
            # Si el usuario decide cancelar o postergar, no validamos el plan
            # TODO: Manejar con otra acción si se desea cancelar el proceso como interrupción
            return {"plan": None}
        if not raw_product:
            # Si no pudimos extraer el producto, retornar sin validar
            return {"plan": None}

        # Normalizamos el valor a minúsculas para la comparación
        product_target = str(raw_product).lower()

        try:
            resultado_busqueda_producto = find_product(product_target)

            if (
                len(resultado_busqueda_producto) == 0
                or len(resultado_busqueda_producto) > 1
            ):
                # dispatcher.utter_message(
                #     text=f"Disculpa, el plan '{raw_product}' no lo tengo disponible."
                # )
                print(f"Producto no encontrado: '{raw_product}'")
                return {
                    "plan": None,
                    "producto_id": None,
                    "nombre_producto": None,
                    "precio_producto": None,
                }
            else:
                # DictCursor returns a mapping; access columns by name instead of by index
                print(
                    f"Producto encontrado: {resultado_busqueda_producto['producto_id']} - {resultado_busqueda_producto['nombre']}"
                )
                return {
                    "plan": raw_product,
                    "producto_id": resultado_busqueda_producto["producto_id"],
                    "nombre_producto": resultado_busqueda_producto["nombre"],
                    "precio_producto": resultado_busqueda_producto["precio_mensual"],
                }

        except Exception as e:
            print(f"Error al validar producto: {e}")
            dispatcher.utter_message(
                text="Lo siento, estoy teniendo problemas para verificar el producto en este momento. Por favor, intenta más tarde."
            )
            return {"plan": None}

    def validate_dui(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        # 1. Definir el patrón RegEx de DUI (8 dígitos, guion opcional, 1 dígito)
        dui_pattern = r"^\d{8}-?\d$"

        # 2. El valor que recibimos aquí es la entidad extraída (ej: "01234567-8" o "012345678")
        match = re.search(dui_pattern, value)

        if match:
            # 3. Limpiar y almacenar (remover el guion para guardar un valor consistente)
            dui_clean = value.replace("-", "")
            return {"dui": dui_clean}
        else:
            if tracker.get_slot("requested_slot") == "dui":
                # 4. Falla la validación del formato (debe ser el usuario quien lo ingrese)
                dispatcher.utter_message(
                    text="El formato del DUI no es válido. Por favor, ingresa los 9 dígitos correctamente."
                )
            return {"dui": None}

    def validate_telefono(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        # Patrón RegEx para teléfono de 8 dígitos.
        # Acepta: XXXXXXXX, XXXX-XXXX, +503XXXXXXXX, 503 XXXX XXXX, +503 XXXX-XXXX
        telefono_pattern = r"^(?:\+?503)?(\d{4}-?\d{4})$"
        # intentar extraer desde el texto del mensaje si coincide con el patrón
        msg_text = tracker.latest_message.get("text", "")
        text_match = re.search(telefono_pattern, msg_text.replace(" ", ""))
        if not value and text_match:
            value = text_match.group(0)

        # intentar extraer desde entidades si existe alguna coincidencia con el patrón
        if not value:
            for ent in tracker.latest_message.get("entities", []):
                ent_val = ent.get("value", "")
                ent_match = re.search(telefono_pattern, ent_val.replace(" ", ""))
                if ent_match:
                    value = ent_match.group(0)
                    break

        # El valor (value) aquí es la entidad extraída por NLU/from_entity.
        match = re.search(telefono_pattern, value.replace(" ", ""))

        if match:
            # El grupo 1 de la expresión captura los 8 dígitos (sin el código 503 ni el guion final).
            # Esto reduce drásticamente el riesgo de un falso positivo con el DUI (9 dígitos).

            # Obtenemos solo los 8 dígitos, eliminando cualquier separador interno
            ocho_digitos = match.group(1).replace("-", "")

            # Verificación final de longitud (seguridad extra)
            if len(ocho_digitos) == 8:
                return {"telefono": ocho_digitos}

        # Si la validación falla (no es un patrón de 8 dígitos de teléfono)
        if tracker.get_slot("requested_slot") == "telefono":
            dispatcher.utter_message(
                text="El formato del teléfono no es válido. Por favor, ingresa los 8 dígitos (ej. 7777-8888) o usa el formato +503."
            )

        return {"telefono": None}

    def validate_nombre(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        # Intentar obtener la entidad nombre desde el mensaje más reciente
        nombre_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "nombre"
            ),
            None,
        )

        apellido_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "apellido"
            ),
            None,
        )

        # el nombre debe ser diferente al apellido
        if value in [apellido_entity]:
            return {"nombre": None}

        # Si se encontró la entidad nombre y es válida, usarla; de lo contrario, usar el slot actual
        if nombre_entity and len(nombre_entity.split()) > 1:
            return {"nombre": nombre_entity.title()}

        print(f"Validando nombre recibido: '{value}'")

        palabras = value.split()
        # Remover palabras no deseadas cuando aparecen aisladas
        palabras_a_remover = {
            "claro",
            "si",
            "sí",
            "no",
            "por",
            "supuesto",
            "aqui",
            "aquí",
            "tienes",
            "sipi",
            "mi",
            "apellido",
            "es",
            "nombre",
            ",",
            "me",
            "llamo",
            "yo",
            "soy",
            "buenos",
            "dias",
            "buenas",
            "tardes",
            "noches",
            "mi",
        }
        palabras = [p for p in palabras if p.lower() not in palabras_a_remover]

        if len(palabras) == 0:
            dispatcher.utter_message(
                text="Necesito tu nombre. ¿Podrías ingresarlo de nuevo?"
            )
            return {"nombre": None}

        if len(palabras) > 5:
            dispatcher.utter_message(
                text="El nombre parece tener demasiadas palabras. Por favor, ingrésalo nuevamente."
            )
            return {"nombre": None}

        return {"nombre": value.title()}

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        print(f"Validando email recibido: '{value}'")

        # Intentar obtener la entidad email desde el mensaje más reciente
        email_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "email"
            ),
            None,
        )
        if (
            email_entity is not None
            and "@" in email_entity
            and "." in email_entity.split("@")[-1]
        ):
            return {"email": email_entity}

        # Validación básica de email
        # Extraer email del value usando regex
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        email_match = re.search(email_pattern, value)
        if email_match:
            value = email_match.group(0)
        if "@" not in value or "." not in value.split("@")[-1]:
            if tracker.get_slot("requested_slot") == "email":
                dispatcher.utter_message(
                    text="El email no parece válido. Por favor, ingrésalo nuevamente (ejemplo: usuario@dominio.com)."
                )
            return {"email": None}

        return {"email": value.lower()}

    def validate_direccion(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        print(f"Validando dirección recibida: '{value}'")

        direccion_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "direccion"
            ),
            None,
        )

        # Si se encontró la entidad dirección y es válida, usarla; de lo contrario, usar el slot actual
        if direccion_entity and len(direccion_entity.split()) >= 4:
            return {"direccion": direccion_entity.strip()}

        # Remover palabras de relleno comunes
        palabras = value.split()
        palabras_relleno = {
            "claro",
            "si",
            "sí",
            "no",
            "por",
            "supuesto",
            "aqui",
            "aquí",
            "tienes",
            "sipi",
            "mi",
            "es",
            "direccion",
            "dirección",
            "vivo",
            "resido",
            "estoy",
            "me",
            "encuentro",
            "ubicado",
        }
        palabras = [p for p in palabras if p.lower() not in palabras_relleno]
        value = " ".join(palabras)

        # Validar longitud mínima
        if len(value.strip().split()) < 4:
            if tracker.get_slot("requested_slot") == "direccion":
                dispatcher.utter_message(
                    text="La dirección parece muy corta. Por favor, proporciona una dirección completa."
                )
            return {"direccion": None}

        return {"direccion": value.strip()}

    def validate_apellido(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        # Intentar obtener la entidad apellido desde el mensaje más reciente
        nombre_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "nombre"
            ),
            None,
        )

        apellido_entity = next(
            (
                e.get("value")
                for e in tracker.latest_message.get("entities", [])
                if e.get("entity") == "apellido"
            ),
            None,
        )

        # el apellido debe ser diferente al nombre
        if value in [nombre_entity]:
            return {"apellido": None}

        # Si se encontró la entidad apellido y es válida, usarla; de lo contrario, usar el slot actual
        if apellido_entity and len(apellido_entity.split()) > 1:
            return {"apellido": apellido_entity.title()}

        print(f"Validando apellido recibido: '{value}'")

        palabras = value.split()
        # Remover palabras no deseadas cuando aparecen aisladas
        palabras_a_remover = {
            "claro",
            "si",
            "sí",
            "no",
            "por",
            "supuesto",
            "aqui",
            "aquí",
            "tienes",
            "sipi",
            "mi",
            "apellido",
            "es",
            "apellido",
            ",",
            "me",
            "llamo",
            "yo",
            "soy",
            "buenos",
            "dias",
            "buenas",
            "tardes",
            "noches",
            "mi",
        }
        palabras = [p for p in palabras if p.lower() not in palabras_a_remover]

        if len(palabras) == 0:
            dispatcher.utter_message(
                text="Necesito tu nombre. ¿Podrías ingresarlo de nuevo?"
            )
            return {"apellido": None}

        if len(palabras) > 5:
            dispatcher.utter_message(
                text="El apellido parece tener demasiadas palabras. Por favor, ingrésalo nuevamente."
            )
            return {"apellido": None}

        return {"apellido": value.title()}
