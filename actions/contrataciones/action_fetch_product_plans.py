from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from dotenv import load_dotenv, find_dotenv

from actions.contrataciones.fetch_product_plans import fetch_product_plans
from actions.utils import _get_chat_history

# Cargar variables de entorno desde un archivo .env (si existe)
dotenv_path = find_dotenv()
print(f"Cargando variables de entorno desde: {dotenv_path}")
if dotenv_path:
    load_dotenv(dotenv_path)
else:
    # fallback: intenta cargar .env desde el directorio de trabajo actual
    load_dotenv()

import requests  # Necesario para la llamada HTTP

# --- CONFIGURACIÓN DE LA API RAG LOCAL ---
# Este es el puerto del servidor Gunicorn que corre rasa_rag_api_server.py
RAG_API_URL = "http://localhost:8000/rag/query"
RAG_API_REPHRASE_URL = "http://localhost:8000/rag/query_with_context"

class ActionFetchProductPlans(Action):
    def name(self) -> Text:
        return "action_fetch_product_plans"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        rows = fetch_product_plans()

        if not rows:
            dispatcher.utter_message(
                text="No hay planes activos disponibles en este momento."
            )
            return []

        # Construir lista de planes desde las filas y consultar la API RAG pasando este resultado como contexto
        plans_list = []
        for row in rows:
            plans_list.append(
                {
                    "producto_id": row.get("producto_id"),
                    "nombre": row.get("nombre"),
                    "descripcion": row.get("descripcion"),
                    "velocidad_bajada_mbps": row.get("velocidad_bajada_mbps"),
                    "velocidad_subida_mbps": row.get("velocidad_subida_mbps"),
                    "precio_mensual": (
                        float(row.get("precio_mensual"))
                        if row.get("precio_mensual") is not None
                        else None
                    ),
                    "beneficios": row.get("beneficios"),
                }
            )

        # Guardar planes en un slot para uso posterior
        # dispatcher.utter_message(
        #     text="He encontrado los planes disponibles. Consulto el asistente de conocimiento para darte una recomendación..."
        # )
        # Obtener la pregunta actual del usuario (si existe)
        user_question = (
            tracker.latest_message.get("text") or "¿Qué plan me recomiendas?"
        )

        # Preparar payload para la API RAG: enviamos la pregunta y el contexto (los planes)
        chat_history_rasa_format = _get_chat_history(tracker)
        payload = {
            "question": user_question,
            "context": repr(plans_list),
            "history": chat_history_rasa_format,
        }
        print(f"Payload RAG con contexto de planes: {payload}")

        try:
            resp = requests.post(RAG_API_REPHRASE_URL, json=payload, timeout=60)
            resp.raise_for_status()
            rag_json = resp.json()
            answer = rag_json.get(
                "answer", "Lo siento, no obtuve una recomendación clara."
            )
            dispatcher.utter_message(text=answer)
        except requests.exceptions.ConnectionError:
            print(f"ERROR RAG: conexión fallida a {RAG_API_URL}")
            dispatcher.utter_message(
                text="No puedo conectar con el motor de conocimiento ahora mismo. Te muestro la lista de planes disponibles."
            )
            # Fallback: mostrar resumen simple de planes
            lines = []
            for p in plans_list[:5]:
                lines.append(
                    f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
                )
            dispatcher.utter_message(
                text=(
                    "\n".join(lines) if lines else "No hay planes para mostrar."
                )
            )
        except requests.exceptions.HTTPError as e:
            print(f"ERROR RAG API: status {resp.status_code} - {e}")
            dispatcher.utter_message(
                text="El servicio de recomendaciones tuvo un error. Aquí están los planes encontrados:"
            )
            lines = [
                f"{p['nombre']} - ${p['precio_mensual']} - {p['velocidad_bajada_mbps']} Mbps"
                for p in plans_list[:5]
            ]
            dispatcher.utter_message(
                text=(
                    "\n".join(lines) if lines else "No hay planes para mostrar."
                )
            )
        except Exception as e:
            print(f"ERROR al consultar RAG o procesar planes: {e}")
            dispatcher.utter_message(
                text="Ocurrió un error inesperado al obtener la recomendación."
            )

        return []
