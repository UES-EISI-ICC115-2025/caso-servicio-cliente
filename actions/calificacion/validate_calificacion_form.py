from typing import Any, Text, Dict, List
from rasa_sdk import Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher


class ValidateCalificacionForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_calificacion_form"
    
    def validate_rating(
        self,
        value: Text,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict,
    ) -> Dict[Text, Any]:

        try:
            rating = float(value)
            if 1.0 <= rating <= 5.0:
                return {"rating": rating}
            else:
                dispatcher.utter_message(
                    text="La calificación debe estar entre 1 y 5. Por favor, ingrésala nuevamente."
                )
                return {"rating": None}
        except ValueError:
            dispatcher.utter_message(
                text="No entendí la calificación. Por favor, ingrésala como un número entre 1 y 5."
            )
            return {"rating": None}