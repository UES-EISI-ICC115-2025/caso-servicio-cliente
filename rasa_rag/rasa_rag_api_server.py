from flask import Flask, request, jsonify
import requests

# --- Dependencias Modulares ---
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
import chromadb
from langchain.chains import RetrievalQA
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

# --- CONFIGURACIÓN RAG LOCAL ---
# OLLAMA_MODEL_NAME = "phi3"
OLLAMA_MODEL_NAME = "deepseek-r1:1.5b"
# OLLAMA_MODEL_NAME = "deepseek-r1:1.5b-qwen-distill-fp16"
# OLLAMA_MODEL_NAME = "deepseek-r1:1.5b-qwen-distill-q8_0"
OLLAMA_BASE_URL = "http://localhost:11434"
RAG_API_PORT = 8000
# -------------------------------------

app = Flask(__name__)
RAG_CHAIN = None

"""
Construye la cadena RAG usando LLM y Embeddings del mismo servidor Ollama.
"""
print("Inicializando LLM Local (Ollama) y Base Vectorial...")

# 1. Conectores LLM y Embeddings (Ambos usan Ollama y phi3)
try:
    requests.get(OLLAMA_BASE_URL)

    # GENERACIÓN: Usa el modelo Phi-3 para crear la respuesta
    llm = OllamaLLM(model=OLLAMA_MODEL_NAME, base_url=OLLAMA_BASE_URL, temperature=0.1)

    # EMBEDDINGS: Usa el mismo modelo Phi-3 (o un modelo compatible) para vectorizar los documentos.
    embeddings = OllamaEmbeddings(model=OLLAMA_MODEL_NAME, base_url=OLLAMA_BASE_URL)
    print(f"Inicialización RAG Local completa. LLM: {OLLAMA_MODEL_NAME}")

    # -------------------------------
    # Conexión a Chroma remoto (se ejecuta al iniciar el bot)
    # -------------------------------
    client = chromadb.HttpClient(host="localhost", port=3000, ssl=False)

    vector_store = Chroma(
        collection_name="qa_servicio_internet_manuales",  # tu colección
        client=client,
        embedding_function=embeddings,  # crucial for remote queries!
    )

    print(f"Inicialización RAG Local completa. LLM: {OLLAMA_MODEL_NAME}")

except Exception as e:
    print(f"Error al conectar a Ollama: {e}")
    raise ConnectionError(
        "Fallo al conectar con el servidor Ollama. Asegúrate de que esté corriendo."
    )


# --- Inicialización de la Cadena RAG ---
def initialize_rag_chain():

    # 2. Base de Conocimiento de Ejemplo
    # docs = [
    #     {
    #         "page_content": "Para reiniciar tu router, desconecta el cable de alimentación por 30 segundos y vuelve a conectarlo. Espera 2 minutos para que se estabilice la conexión."
    #     },
    #     {
    #         "page_content": "Si el internet está lento, verifica las luces. Si la luz 'Internet' está roja, hay una falla en la línea."
    #     },
    # ]
    # documents = [Document(page_content=t["page_content"]) for t in docs]
    # vectorstore = Chroma.from_documents(documents, embeddings)
    retriever = vector_store.as_retriever()

    # 3. PROMTPTS y CADENAS MODULARES

    # Prompt 1: Genera la consulta de búsqueda
    query_generator_prompt = ChatPromptTemplate.from_messages(
        [
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            (
                "user",
                "Basado en la conversación, genera una consulta de búsqueda en español que resuelva la duda.",
            ),
        ]
    )

    # Cadena 1: Recuperador consciente del historial
    retriever_chain = create_history_aware_retriever(
        llm, retriever, query_generator_prompt
    )

    # Prompt 2: Genera la respuesta final con el contexto
    answer_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "Eres un agente de soporte técnico de El Salvador. Responde la pregunta del usuario basándote solo en el siguiente contexto:\n\n{context}\nSi el contexto no proporciona la respuesta, indica que no la sabes. Utiliza un tono amigable y salvadoreño.",
            ),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ]
    )

    # Cadena 2: Combina los documentos y el LLM para generar la respuesta
    document_chain = create_stuff_documents_chain(llm, answer_prompt)

    # 4. Cadena Final: Combina la recuperación y la generación (Resuelve el AttributeError)
    qa_chain = create_retrieval_chain(retriever_chain, document_chain)

    return qa_chain


try:
    RAG_CHAIN = initialize_rag_chain()
except ConnectionError as e:
    # Si la conexión falla, se detiene la carga del servidor
    print(e)

    # --- Cadena RAG que usa un contexto de texto plano en lugar de la base vectorial ---
    RAG_CHAIN_CONTEXT = None


# --- ENDPOINT API DE RASA ---
@app.route("/rag/query", methods=["POST"])
def rag_query():
    global RAG_CHAIN

    if RAG_CHAIN is None:
        return (
            jsonify({"answer": "Error: El servidor RAG no pudo iniciar la cadena."}),
            503,
        )

    # ... (El resto de la lógica de API permanece igual) ...

    data = request.get_json()
    question = data.get("question")
    history_data = data.get("history", [])

    if not question:
        return jsonify({"error": "Parámetro 'question' faltante"}), 400

    chat_history_messages = []
    for user_msg, bot_msg in history_data:
        if user_msg:
            chat_history_messages.append(HumanMessage(content=user_msg))
        if bot_msg:
            chat_history_messages.append(AIMessage(content=bot_msg))

    try:
        result = RAG_CHAIN.invoke(
            {"input": question, "chat_history": chat_history_messages}
        )

        response_text = result["answer"]

        return jsonify({"answer": response_text})

    except Exception as e:
        print(f"ERROR RAG al procesar la consulta: {e}")
        return (
            jsonify(
                {
                    "answer": "Lo siento, la consulta a la base de conocimiento local falló."
                }
            ),
            500,
        )


@app.route("/rag/query_with_context", methods=["POST"])
def rag_query_with_context():
    # GENERACIÓN: Usa el modelo Phi-3 para crear la respuesta
    llm = OllamaLLM(model=OLLAMA_MODEL_NAME, base_url=OLLAMA_BASE_URL, temperature=0.1)

    data = request.get_json()
    context = data.get("context")
    question = data.get("question")
    history_data = data.get("history", [])

    # print(f"RAG Consulta con contexto recibido. Pregunta: {question}, Contexto: {context}, Historial: {history_data}")

    if not question or context is None:
        return (
            jsonify({"error": "Parámetros 'context' y 'question' son requeridos"}),
            400,
        )

    chat_history_messages = []
    # Inyecta el contexto como primer mensaje humano en el historial
    chat_history_messages.append(
        HumanMessage(content=f"Contexto proporcionado por el usuario:\n{context}")
    )

    for user_msg, bot_msg in history_data:
        if user_msg:
            chat_history_messages.append(HumanMessage(content=user_msg))
        if bot_msg:
            chat_history_messages.append(AIMessage(content=bot_msg))

    try:
        # Prompt: recibe explícitamente {context} y usa el historial si aplica
        answer_prompt_with_context = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "Eres un agente de soporte técnico de El Salvador. Responde la pregunta del usuario basándote solo en el siguiente contexto:\n\n{context}\nSi el contexto no proporciona la respuesta, indica que no la sabes. Utiliza un tono amigable y salvadoreño.",
                ),
                MessagesPlaceholder(variable_name="history"),
                ("user", "{input}"),
            ]
        )
        print(
            answer_prompt_with_context.format_prompt(
                input=question,
                history=chat_history_messages,
                context=context,
            ).to_messages()
        )
        response = llm.invoke(
            answer_prompt_with_context.format_prompt(
                input=question,
                history=chat_history_messages,
                context=context,
            ).to_messages()
        )

        return jsonify({"answer": response})
    except Exception as e:
        print(f"ERROR RAG al procesar consulta con contexto: {e}")
        return jsonify({"answer": "Lo siento, la consulta con contexto falló."}), 500
