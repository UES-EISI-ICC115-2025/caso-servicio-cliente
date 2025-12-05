from typing import List, Tuple
from rasa_sdk import Tracker


def _get_chat_history(tracker: Tracker, retrieval: int = 4) -> List[Tuple[str, str]]:
    """Extrae el historial reciente en formato (user_msg, bot_msg) para la API RAG."""
    history: List[Tuple[str, str]] = []
    current_user_message: str = None

    for event in tracker.events_after_latest_restart():
        if event.get("event") == "user" and event.get("text"):
            current_user_message = event.get("text")

        elif event.get("event") == "bot" and event.get("text") and current_user_message:
            history.append((current_user_message, event.get("text")))
            current_user_message = None  # Resetea después de emparejar
    return history[-retrieval:]
