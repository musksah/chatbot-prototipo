import os
import re
import logging
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def split_vivienda_by_project(docs):
    """
    Custom splitter for vivienda.pdf that keeps each project's information together.
    Projects are identified by their numbered headers in the PDF.
    """
    logger.info("RAG: Splitting vivienda docs into project chunks (pages=%s)", len(docs))
    full_text = "\n".join([doc.page_content for doc in docs])
    
    # Clean up the text - remove excessive whitespace
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # Split by project markers (1. EL PEDREGAL, 2. RANCHO GRANDE, 3. ARRAYANES)
    # Using regex to find project boundaries
    project_patterns = [
        (r'1\.\s*EL\s*PEDREGAL.*?(?=2\.\s*RANCHO\s*GRANDE|$)', 'EL PEDREGAL - FUSAGASUGÁ'),
        (r'2\.\s*RANCHO\s*GRANDE.*?(?=3\.\s*ARRAYANES|$)', 'RANCHO GRANDE - MELGAR'),
        (r'3\.\s*ARRAYANES.*', 'ARRAYANES DE PEÑALISA II - RICAURTE'),
    ]
    
    project_docs = []
    
    for pattern, project_name in project_patterns:
        match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(0).strip()
            # Add project name as prefix for clarity
            content = f"[PROYECTO: {project_name}]\n\n{content}"
            
            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    "source": "vivienda.pdf",
                    "project": project_name,
                    "type": "vivienda"
                }
            )
            project_docs.append(doc)
            logger.info("RAG: Extracted project '%s' (%s chars)", project_name, len(content))
    
    # If pattern matching failed, fall back to larger chunks
    if not project_docs:
        logger.warning("RAG: Project split failed, falling back to large chunks")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=3000, 
            chunk_overlap=500,
            separators=["\n\n", "\n", ". ", " "]
        )
        project_docs = text_splitter.split_documents(docs)
    
    return project_docs

def load_and_index_docs(docs_dir: str):
    """
    Loads PDFs from the directory, splits them, and creates a FAISS index.
    Uses specialized chunking for vivienda to keep project info together.
    """
    logger.info("RAG: Loading docs from %s", docs_dir)
    
    associado_docs = []
    nominas_docs = []
    vivienda_docs = []
    
    # Load specific files
    if os.path.exists(os.path.join(docs_dir, "atencion al asociado.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "atencion al asociado.pdf"))
        associado_docs.extend(loader.load())
        logger.info("RAG: Loaded atencion al asociado.pdf (pages=%s)", len(associado_docs))

    if os.path.exists(os.path.join(docs_dir, "nominas.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "nominas.pdf"))
        nominas_docs.extend(loader.load())
        logger.info("RAG: Loaded nominas.pdf (pages=%s)", len(nominas_docs))
        
    if os.path.exists(os.path.join(docs_dir, "vivienda.pdf")):
        loader = PyPDFLoader(os.path.join(docs_dir, "vivienda.pdf"))
        vivienda_docs.extend(loader.load())
        logger.info("RAG: Loaded vivienda.pdf (pages=%s)", len(vivienda_docs))
    
    # Standard text splitter for associado and nominas
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    retrievers = {}
    
    if associado_docs:
        splits = text_splitter.split_documents(associado_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        retrievers["atencion_asociado"] = vectorstore.as_retriever()
        logger.info("RAG: Indexed atencion_asociado (%s chunks)", len(splits))
        
    if nominas_docs:
        splits = text_splitter.split_documents(nominas_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        retrievers["nominas"] = vectorstore.as_retriever()
        logger.info("RAG: Indexed nominas (%s chunks)", len(splits))

    if vivienda_docs:
        # Use specialized splitting for vivienda to keep projects separate
        logger.info("RAG: Processing vivienda with project-aware chunking")
        splits = split_vivienda_by_project(vivienda_docs)
        vectorstore = FAISS.from_documents(splits, embeddings)
        # Increase k to get more relevant chunks since we have fewer, larger chunks
        retrievers["vivienda"] = vectorstore.as_retriever(search_kwargs={"k": 2})
        logger.info("RAG: Indexed vivienda (%s project chunks)", len(splits))
        
    if not retrievers:
        logger.warning("RAG: No documents indexed. Check PDF files and OCR/text extraction.")
    return retrievers

# Global retrievers instance (lazy loaded)
_retrievers = None

def get_retrievers():
    global _retrievers
    if _retrievers is None:
        docs_path = os.path.join(os.path.dirname(__file__), "..", "docs")
        logger.info("RAG: Initializing retrievers")
        _retrievers = load_and_index_docs(docs_path)
    return _retrievers

