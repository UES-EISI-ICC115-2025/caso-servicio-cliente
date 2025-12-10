# Importar librerías
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
import chromadb

OLLAMA_MODEL_NAME = "deepseek-r1:1.5b"
# OLLAMA_MODEL_NAME = "deepseek-r1:1.5b-qwen-distill-fp16"
# OLLAMA_MODEL_NAME = "deepseek-r1:1.5b-qwen-distill-q8_0"
OLLAMA_BASE_URL = "http://localhost:11434"

# Cargar documentos
# Puedes cargar PDFs o TXT
pdf_loader = DirectoryLoader("../documentos/pdfs/manuales", glob="*.pdf", loader_cls=PyPDFLoader)  # carpeta con PDFs
# txt_loader = DirectoryLoader("documentos", glob="*.txt", loader_cls=TextLoader)

# docs = pdf_loader.load() + txt_loader.load()
docs = pdf_loader.load()

# Dividir en fragmentos
text_splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
chunks = text_splitter.split_documents(docs)
embeddings = OllamaEmbeddings(model=OLLAMA_MODEL_NAME, base_url=OLLAMA_BASE_URL)

client = chromadb.HttpClient(host="localhost", port=3000, ssl=False)

# Conectar al Chroma remoto
vector_store = Chroma(
    client=client,
    embedding_function=embeddings,
    collection_name="qa_servicio_internet_manuales"  # nombre de la colección en Chroma DB remoto,
)

# Indexar los fragmentos
vector_store.add_documents(chunks)

# Listo, ahora tus vectores están en Chroma remoto
print("Vector store creado y poblado en Chroma DB remoto.")