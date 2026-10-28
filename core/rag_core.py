# ==============================================================================
# MOTOR RAG - Sistema RAG
# Autor: Ing. Edeblangel Vanegas
# ==============================================================================

import os
from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate

import chromadb
from chromadb.config import Settings


class RAGCore:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API key required for Gemini Developer API. Provide api_key parameter or set GOOGLE_API_KEY/GEMINI_API_KEY environment variable.")
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/embedding-001", google_api_key=self.api_key
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key,
            temperature=0.2,
        )
        data_dir = os.getenv("DATA_DIR") or os.getenv("RAILWAY_VOLUME_MOUNT_PATH") or "/data"
        chroma_dir = os.path.join(data_dir, "chroma")
        os.makedirs(chroma_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(path=chroma_dir, settings=Settings(anonymized_telemetry=False))
        self.collection_name = "rag_collection"
        try:
            self.collection = self.client.get_or_create_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(self.collection_name)
        self.vectorstore = None
        self.qa_chain = None
        # Intentar reconstruir vectorstore si existe colección con datos
        try:
            from langchain_community.vectorstores import Chroma

            if self.collection.count() > 0:
                self.vectorstore = Chroma(
                    client=self.client,
                    collection_name=self.collection_name,
                    embedding_function=self.embeddings,
                )
                self._build_qa_chain()
        except Exception as e:
            print(f"[WARN] No se pudo reconstruir vectorstore desde persistencia: {e}")

    def load_documents(self, file_paths: List[str]) -> List[Document]:
        documents = []
        for file_path in file_paths:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
                documents.extend(loader.load())
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
                documents.extend(loader.load())
            else:
                raise ValueError(f"Formato no soportado: {ext}")
        return documents

    def split_documents(self, documents: List[Document]) -> List[Document]:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        return text_splitter.split_documents(documents)

    def build_vectorstore(self, documents: List[Document]):
        from langchain_community.vectorstores import Chroma

        chunks = self.split_documents(documents)
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            client=self.client,
            collection_name=self.collection_name,
        )
        self._build_qa_chain()
        return len(chunks)

    def _build_qa_chain(self):
        prompt_template = """Responde únicamente utilizando la información proporcionada en el siguiente contexto. 
Si la respuesta no está en el contexto, indica amablemente que no dispones de esa información en los documentos.

Contexto:
{context}

Pregunta: {question}

Respuesta (con cita de fuentes cuando aplique):"""

        PROMPT = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )

        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 4}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT},
        )

    def query(self, question: str):
        if not self.qa_chain:
            return {
                "answer": "No hay documentos cargados. Por favor, cargue documentos primero desde el panel de administración.",
                "sources": [],
            }
        result = self.qa_chain({"query": question})
        sources = []
        for doc in result.get("source_documents", []):
            source_info = {
                "source": doc.metadata.get("source", "Desconocido"),
                "page": doc.metadata.get("page", "N/A"),
            }
            sources.append(source_info)
        return {"answer": result["result"], "sources": sources}
