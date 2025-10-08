from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from langchain_chroma import Chroma
import chromadb
from langchain_ollama import OllamaEmbeddings
from fastapi import FastAPI
from pydantic import BaseModel

# Crear embeddings usando Ollama
embeddings = OllamaEmbeddings(
    model="llama3.2:1b", base_url="http://ollama-server:11434"
)

# -------------------------------
# Conexión a Chroma remoto (se ejecuta al iniciar el bot)
# -------------------------------
client = chromadb.HttpClient(host="chroma-server", port=8000, ssl=False)

vector_store = Chroma(
    collection_name="manuales_y_procedimientos",
    client=client,
    embedding_function=embeddings,
)

# Inicializa Ollama una sola vez
llm = OllamaLLM(model="llama3.2:1b", temperature=0.7)


class Query(BaseModel):
    question: str


app = FastAPI()

@app.post("/query")
def query(query: Query):
    # Recuperador desde Chroma
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})

    # Crear la cadena RAG
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="refine",
        retriever=retriever,
        return_source_documents=False,
    )

    # Generar respuesta
    respuesta = qa_chain.invoke(query.question)

    return {"answer": respuesta}
