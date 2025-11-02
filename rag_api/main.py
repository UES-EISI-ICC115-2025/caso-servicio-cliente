import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain.chains import RetrievalQA
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from fastapi.middleware.cors import CORSMiddleware
from langchain.prompts import PromptTemplate
import chromadb

# OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
# CHROMA_HOST = os.getenv("CHROMA_HOST", "172.16.2.66")  # IP of the remote Chroma DB
# CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))


# -------------------------------
# Configuration
# -------------------------------
OLLAMA_URL = "http://localhost:11434"
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000
COLLECTION_NAME = "manuales_y_procedimientos"

# -------------------------------
# FastAPI app
# -------------------------------
app = FastAPI(title="Ollama RAG API", version="1.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str


class Rephrase(BaseModel):
    question: str
    adicional: str
    contexto: str


# -------------------------------
# Initialize components
# -------------------------------
try:
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT, ssl=False)
    embeddings = OllamaEmbeddings(model="llama3.2:1b", base_url=OLLAMA_URL)

    vector_store = Chroma(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

    llm = OllamaLLM(model="llama3.2:1b", base_url=OLLAMA_URL, temperature=0.7)

    print("RAG components initialized")
except Exception as e:
    print("Error initializing components:", e)
    raise

retriever = vector_store.as_retriever(search_kwargs={"k": 5})

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="refine",
    return_source_documents=False,
)


# -------------------------------
# Endpoint: /ask
# -------------------------------
@app.post("/ask")
async def ask_question(payload: Question):
    try:
        pregunta = payload.question.strip()
        if not pregunta:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        qa_chain.retriever = retriever  # Update retriever to ensure latest data

        respuesta = qa_chain.invoke({"query": pregunta})
        return {"answer": respuesta["result"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


retriever = vector_store.as_retriever(search_kwargs={"k": 5})

rephrase_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff",
    return_source_documents=False,
)


# -------------------------------
# Endpoint: /rephrase
# -------------------------------
@app.post("/rephrase")
async def rephrase_answer(payload: Rephrase):
    try:
        pregunta_cliente = payload.question.strip()
        adicional = payload.adicional.strip()
        contexto = payload.contexto.strip()
        if not pregunta_cliente:
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        if not contexto:
            raise HTTPException(status_code=400, detail="Contexto cannot be empty")
        if not adicional:
            adicional = 'Ninguna'

        # Plantilla flexible
        prompt_template = """
        Eres un asistente de atención al cliente de una empresa en El Salvador. 
        Tu objetivo es responder de manera amigable, natural y clara, como lo haría un humano salvadoreño.
        No saludes al inicio porque el cliente ya te saludó.
        Se muy breve y directo al punto, no hagas preguntas muy técnicas

        Contexto / conocimiento disponible:
        {contexto}

        Pregunta original del cliente:
        {pregunta}

        Instrucciones adicionales:
        {instruccion_adicional}

        Si no sabes la respuesta, dile al cliente de manera educada que no tienes esa información.
        """

        prompt = PromptTemplate(
            input_variables=["contexto", "pregunta", "adicional"],
            template=prompt_template,
        )

        # Construir el prompt con los datos reales
        input_prompt = prompt.format(
            contexto=contexto, pregunta=pregunta_cliente, instruccion_adicional=adicional
        )
        print(input_prompt)
        # Generar la respuesta rephraseada
        rephraseada = llm.invoke(input_prompt)
        return {"answer": rephraseada}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
