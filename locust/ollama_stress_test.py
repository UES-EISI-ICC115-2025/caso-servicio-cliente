
import random
from locust import HttpUser, task, between
MODELO_A_PROBAR = "deepseek-r1:1.5b"
preguntas = [
    "¿Cómo puedo reiniciar mi router?",
    "¿Qué debo hacer si mi conexión a internet es lenta?",
    "¿Cómo configuro una red Wi-Fi segura?",
    "¿Cuáles son los pasos para solucionar problemas de conectividad?",
    "¿Cómo puedo actualizar el firmware de mi router?",
    "¿Qué significan las luces indicadoras en mi router?",
    "¿Cómo puedo cambiar la contraseña de mi red Wi-Fi?",
    "¿Qué hago si olvido la contraseña de mi router?",
    "¿Cómo puedo mejorar la señal Wi-Fi en mi hogar?",
    "¿Qué es el modo puente en un router y cómo se configura?",
]

class OllamaInferenceUser(HttpUser):
    wait_time = between(0.5, 2)
    host = "http://localhost:8000"  # URL del servidor RAG
    @task
    def generate_content(self):
        payload = {
                    'question': random.choice(preguntas),
                    'history': []
                }
        print(f"Enviando payload RAG: {payload}")
        self.client.post('/rag/query', json=payload, name='/rag/query RAG', timeout = 120)

