from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType


# Esta clase de formulario ahora maneja la recolección del user_id
class ValidateUserVerificationForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_user_verification_form"

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Text]:
        # Solo necesitamos user_id para este ejemplo
        if tracker.get_slot("user_id") is None:
            return ["user_id"]
        return []

    def validate_user_id(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:

        # Validar el ID (simulación: debe ser al menos 9 caracteres)
        if len(str(slot_value)) >= 9:
            # Verificar que el ID exista en tu DB.
            return {"user_id": slot_value}
        else:
            dispatcher.utter_message(
                text="El ID debe tener al menos 9 caracteres. ¿Me lo puedes dar de nuevo?"
            )
            return {"user_id": None}


# Esta acción consulta a la base de datos y establece el slot 'billing_status'
class ActionCheckBillingStatus(Action):
    def name(self) -> Text:
        return "action_check_billing_status"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        user_id = tracker.get_slot("user_id")

        # 1. Lógica de simulación para estado de facturación
        # En una aplicación real, aquí va la consulta a la DB de PostgreSQL.

        status_map = {
            "cliente123": "PAGADA",
            "mora": "VENCIDA",
            "pendiente": "PENDIENTE",
        }

        # Asigna un estado basado en el ID de simulación o usa un valor por defecto
        status = status_map.get(user_id, "PENDIENTE")

        # 2. Responde al usuario y establece el slot de estado de facturación
        if status == "VENCIDA":
            dispatcher.utter_message(response="utter_billing_overdue")
        elif status == "PAGADA":
            dispatcher.utter_message(response="utter_billing_paid")
        else:
            dispatcher.utter_message(response="utter_billing_pending")

        # 3. Retorna el estado para que el diálogo pueda continuar
        return [SlotSet("billing_status", status)]
