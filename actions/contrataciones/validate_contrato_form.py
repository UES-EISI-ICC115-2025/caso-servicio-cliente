import re
from rasa_sdk.events import ActiveLoop, SlotSet
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from rasa_sdk.types import DomainDict
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
        
        # Normalizamos el valor a minúsculas para la comparación
        product_normalized = str(slot_value).lower()

        # Leer credenciales desde variables de entorno
        pg_host = os.getenv("PG_HOST", "localhost")
        pg_port = os.getenv("PG_PORT", "5432")
        pg_db = os.getenv("PG_DB", "mydb")
        pg_user = os.getenv("PG_USER", "postgres")
        pg_password = os.getenv("PG_PASSWORD", "")
        print(pg_host, pg_port, pg_db, pg_user, pg_password)

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
                # build a safe ILIKE pattern and use parameterized query correctly
                pattern = f"%{product_normalized}%"
                cur.execute(
                    """
                    SELECT
                        producto_id,
                        nombre,
                        descripcion,
                        velocidad_bajada_mbps,
                        velocidad_subida_mbps,
                        precio_mensual,
                        beneficios
                    FROM productos
                    WHERE
                        LOWER(
                            TRANSLATE(
                                nombre,
                                'áéíóúÁÉÍÓÚñÑ',
                                'aeiouAEIOUnN'
                            )
                        ) ILIKE LOWER(
                            TRANSLATE(
                                %s,
                                'áéíóúÁÉÍÓÚñÑ',
                                'aeiouAEIOUnN'
                            )
                        )
                    ORDER BY precio_mensual ASC
                    """,
                    (pattern,)
                )

                resultado_busqueda_producto = cur.fetchone()

                if not resultado_busqueda_producto:
                    dispatcher.utter_message(text=f"Disculpa, el plan '{slot_value}' no lo tengo disponible.")
                    dispatcher.utter_message(response="action_fetch_product_plans")
                    return {"plan": None, "producto_id": None, "nombre_producto": None, "precio_producto": None}
                else:
                    # DictCursor returns a mapping; access columns by name instead of by index
                    print(f"Producto encontrado: {resultado_busqueda_producto['producto_id']} - {resultado_busqueda_producto['nombre']}")
                    return {
                        "plan": slot_value,
                        "producto_id": resultado_busqueda_producto["producto_id"],
                        "nombre_producto": resultado_busqueda_producto["nombre"],
                        "precio_producto": resultado_busqueda_producto["precio_mensual"],
                    }
        
        except Exception as e:
            print(f"Error al conectar a la base de datos: {e}")
            dispatcher.utter_message(text="Lo siento, estoy teniendo problemas para verificar el producto en este momento. Por favor, intenta más tarde.")
            return {"plan": None}
        finally:
            if conn:
                conn.close()

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
            dui_clean = value.replace('-', '')
            return {"dui": dui_clean}
        else:
            if tracker.get_slot('requested_slot') == 'dui':
                # 4. Falla la validación del formato (debe ser el usuario quien lo ingrese)
                dispatcher.utter_message(text="El formato del DUI no es válido. Por favor, ingresa los 9 dígitos correctamente.")
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
        text_match = re.search(telefono_pattern, msg_text.replace(' ', ''))
        if not value and text_match:
            value = text_match.group(0)

        # intentar extraer desde entidades si existe alguna coincidencia con el patrón
        if not value:
            for ent in tracker.latest_message.get("entities", []):
                ent_val = ent.get("value", "")
                ent_match = re.search(telefono_pattern, ent_val.replace(' ', ''))
                if ent_match:
                    value = ent_match.group(0)
                    break
        
        # El valor (value) aquí es la entidad extraída por NLU/from_entity.
        match = re.search(telefono_pattern, value.replace(' ', ''))
        
        if match:
            # El grupo 1 de la expresión captura los 8 dígitos (sin el código 503 ni el guion final).
            # Esto reduce drásticamente el riesgo de un falso positivo con el DUI (9 dígitos).
            
            # Obtenemos solo los 8 dígitos, eliminando cualquier separador interno
            ocho_digitos = match.group(1).replace('-', '') 
            
            # Verificación final de longitud (seguridad extra)
            if len(ocho_digitos) == 8:
                return {"telefono": ocho_digitos}
            
        # Si la validación falla (no es un patrón de 8 dígitos de teléfono)
        if tracker.get_slot('requested_slot') == 'telefono':
            dispatcher.utter_message(text="El formato del teléfono no es válido. Por favor, ingresa los 8 dígitos (ej. 7777-8888) o usa el formato +503.")
                
        return {"telefono": None}

    # def validate_nombre(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: Dict,
    # ) -> Dict[Text, Any]:

    #     apellido = tracker.get_slot("apellido")
    #     telefono = tracker.get_slot("telefono")
    #     email = tracker.get_slot("email")
    #     dui = tracker.get_slot("dui")
    #     direccion = tracker.get_slot("direccion")

    #     print(f"Validando nombre recibido: '{value}'")

    #     palabras = value.split()

    #     if len(palabras) == 0:
    #         dispatcher.utter_message(
    #             text="Necesito tu nombre. ¿Podrías ingresarlo de nuevo?"
    #         )
    #         return {"nombre": None}

    #     if len(palabras) > 3:
    #         dispatcher.utter_message(
    #             text="El nombre parece tener demasiadas palabras. Por favor, ingrésalo nuevamente."
    #         )
    #         return {"nombre": None}

    #     if value in [apellido, telefono, email, dui, direccion]:
    #         return {"nombre": None}

    #     return {"nombre": value.title()}

    def validate_email(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        print(f"Validando email recibido: '{value}'")

        if (
            tracker.get_slot("email") is not None
            and "@" in tracker.get_slot("email")
            and "." in tracker.get_slot("email").split("@")[-1]
        ):
            return {"email": tracker.get_slot("email")}

        # Validación básica de email
        if "@" not in value or "." not in value.split("@")[-1]:
            if tracker.get_slot("requested_slot") == "email":
                dispatcher.utter_message(
                    text="El email no parece válido. Por favor, ingrésalo nuevamente (ejemplo: usuario@dominio.com)."
                )
            return {"email": None}

        return {"email": value.lower()}

    # def validate_direccion(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: Dict,
    # ) -> Dict[Text, Any]:

    #     print(f"Validando dirección recibida: '{value}'")

    #     if (
    #         tracker.get_slot("direccion") is not None
    #         and len(tracker.get_slot("direccion").strip().split()) >= 4
    #     ):
    #         return {"direccion": tracker.get_slot("direccion")}

    #     # Validar longitud mínima
    #     if len(value.strip().split()) < 4:
    #         if tracker.get_slot("requested_slot") == "direccion":
    #             dispatcher.utter_message(
    #                 text="La dirección parece muy corta. Por favor, proporciona una dirección completa."
    #             )
    #         return {"direccion": None}

    #     return {"direccion": value.strip()}

    # def validate_apellido(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: Dict,
    # ) -> Dict[Text, Any]:

    #     # Esta es la validación si se usó from_text:
    #     # Recuperar otros slots relevantes
    #     nombre = tracker.get_slot("nombre")
    #     telefono = tracker.get_slot("telefono")
    #     email = tracker.get_slot("email")
    #     dui = tracker.get_slot("dui")
    #     direccion = tracker.get_slot("direccion")
    #     print(f"Validando apellido recibido via from_text: '{value}'")
    #     print(f"Slot 'telefono' recuperado: {telefono}")
    #     print(f"Slot 'email' recuperado: {email}")
    #     print(f"Slot 'nombre' recuperado: {nombre}")
    #     print(f"Slot 'dui' recuperado: {dui}")
    #     print(f"Slot 'direccion' recuperado: {direccion}")

    #     palabras = value.split()

    #     # 2. Validación de Calidad: Se requiere al menos una o dos palabras
    #     if len(palabras) == 0:
    #         if tracker.get_slot("requested_slot") == "apellido":
    #             dispatcher.utter_message(
    #                 text="Necesito tu apellido. ¿Podrías ingresarlo de nuevo?"
    #             )
    #         return {"apellido": None}  # Falla la validación, pide de nuevo

    #     if len(palabras) > 3:
    #         if tracker.get_slot("requested_slot") == "apellido":
    #             dispatcher.utter_message(
    #                 text="El apellido parece tener demasiadas palabras. Por favor, ingrésalo nuevamente."
    #             )
    #         return {"apellido": None}  # Falla la validación, pide de nuevo
    #     if value in [nombre, telefono, email, dui, direccion]:
    #         # dispatcher.utter_message(
    #         #     text="Parece que has ingresado tu nombre en lugar de tu apellido. Por favor, ingresa solo tu apellido."
    #         # )
    #         return {"apellido": None}  # Falla la validación, pide de nuevo
    #     # 3. Éxito: El texto fue limpiado y se considera válido
    #     #    Se almacena el texto limpio y Rasa avanza al siguiente slot
    #     return {"apellido": value.title()}
