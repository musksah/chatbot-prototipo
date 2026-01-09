import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initialize embeddings
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

def load_and_index_docs(docs_dir: str):
    """
    Loads PDFs from the directory, splits them, and creates a FAISS index.
    In a real system, you might want separate indexes or metadata filtering.
    Here we will create 3 separate retrievers for simplicity and strict separation.
    """
    
    associado_docs = []
    nominas_docs = []
    vivienda_docs = []
    
    # Load specific files
    if os.path.exists(os.path.join(docs_dir, "atencion al asociado.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "atencion al asociado.pdf"))
        associado_docs.extend(loader.load())

    if os.path.exists(os.path.join(docs_dir, "nominas.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "nominas.pdf"))
        nominas_docs.extend(loader.load())
        
    if os.path.exists(os.path.join(docs_dir, "vivienda.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "vivienda.pdf"))
        vivienda_docs.extend(loader.load())
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    retrievers = {}
    
    if associado_docs:
        splits = text_splitter.split_documents(associado_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        retrievers["atencion_asociado"] = vectorstore.as_retriever()
        print("Indexed 'Atencion al Asociado'")
        
    if nominas_docs:
        splits = text_splitter.split_documents(nominas_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        retrievers["nominas"] = vectorstore.as_retriever()
        print("Indexed 'Nominas'")

    if vivienda_docs:
        splits = text_splitter.split_documents(vivienda_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        retrievers["vivienda"] = vectorstore.as_retriever()
        print("Indexed 'Vivienda'")
        
    return retrievers

# Global retrievers instance (lazy loaded)
_retrievers = None

def get_retrievers():
    global _retrievers
    if _retrievers is None:
        docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
        _retrievers = load_and_index_docs(docs_path)
    return _retrievers
