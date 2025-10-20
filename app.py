import gradio as gr
import requests
import os

# --- Configuration (Replace with your actual API details) ---
API_URL = "http://localhost:5005/webhooks/rest/webhook"
API_KEY = os.getenv("CHAT_API_KEY") 
# IMPORTANT: Set the environment variable 'CHAT_API_KEY' in your terminal
# e.g., export CHAT_API_KEY="sk-xxxxxxxxxxxxxxxx" 

# --- The API Bridge Function with Streaming ---
def get_bot_response_streaming(message, history):
    # 1. Format the conversation history (Gradio to API format)
    formatted_messages = []
    for human, assistant in history:
        formatted_messages.append({"role": "user", "content": human})
        formatted_messages.append({"role": "assistant", "content": assistant})
    formatted_messages.append({"role": "user", "content": message})

    # 2. Prepare the request (replace with your API's specific JSON structure)
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "messages": formatted_messages,
        "model": "your_api_model_name",
        "stream": True # Important for real-time display
    }

    try:
        # 3. Call API and stream response
        response_stream = requests.post(API_URL, headers=headers, json=payload, stream=True, timeout=60)
        response_stream.raise_for_status()

        partial_message = ""
        for chunk in response_stream.iter_content(chunk_size=1024):
            # --- REPLACE THIS SECTION WITH YOUR API'S STREAMING PARSING ---
            # You need to correctly extract the new text from each 'chunk'
            # e.g., if it's Server-Sent Events (SSE), you'd parse the 'data:' lines.
            
            # Simplified placeholder:
            new_text = chunk.decode("utf-8")
            partial_message += new_text
            yield partial_message
            # -------------------------------------------------------------

    except requests.exceptions.RequestException as e:
        yield f"Error: Failed to connect to API or request timed out: {e}"


# --- Create and Customize the Interface ---
app = gr.ChatInterface(
    fn=get_bot_response_streaming,
    title="Servicio al cliente",
    description="Chat de atención al cliente automatizado. Escribe tu consulta y recibe respuestas en tiempo real.",
    theme="gradio/soft",
    submit_btn="Enviar"
)

if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0", 
        server_port=8081, # MUST match the port NGINX targets (8080)
        show_api=False,  # Opcional, limpia la interfaz
    )