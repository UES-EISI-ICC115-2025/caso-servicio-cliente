from rasa_sdk import Action
import requests


class ActionGenerarRespuestaRag(Action):
    def name(self):
        return "action_generar_respuesta_rag"

    def run(self, dispatcher, tracker, domain):
        pregunta = tracker.latest_message.get("text")
        resp = requests.post("http://localhost:8000/query", json={"question": pregunta})
        dispatcher.utter_message(text=resp.json().get("answer"))
        return []
