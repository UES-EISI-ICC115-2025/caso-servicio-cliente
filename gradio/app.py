import gradio as gr
import requests

# --- Configuration ---
API_URL = "http://localhost:5005/webhooks/rest/webhook"  # Rasa API endpoint


# --- The API Bridge Function with Streaming ---
def get_bot_response_streaming(message, history):
    # 1. Format the conversation history (Gradio to API format)
    formatted_messages = []
    for human, assistant in history:
        formatted_messages.append({"role": "user", "content": human})
        formatted_messages.append({"role": "assistant", "content": assistant})
    formatted_messages.append({"role": "user", "content": message})

    payload = {"sender": "user", "message": message}  # A unique identifier for the user

    try:
        # 3. Call API and stream response
        # Rasa's default /webhooks/rest/webhook does not stream responses in chunks.
        # It returns a list of responses at once.
        response_stream = requests.post(API_URL, json=payload, timeout=60)
        response_stream.raise_for_status()

        rasa_responses = response_stream.json()
        bot_messages = [r.get("text") for r in rasa_responses if r.get("text")]
        yield "\n".join(bot_messages)  # Join multiple Rasa responses if any

    except requests.exceptions.RequestException as e:
        yield f"Error: Failed to connect to API or request timed out: {e}"


app = gr.ChatInterface(
    fn=get_bot_response_streaming,
    title="Servicio al cliente",
    description="Chat de atención al cliente automatizado. Escribe tu consulta y recibe respuestas en tiempo real.",
    theme="gradio/soft",
    submit_btn="Enviar",
)

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",
        server_port=8081,  # MUST match the port NGINX targets (8081)
        show_api=True,  # Opcional, limpia la interfaz
    )
