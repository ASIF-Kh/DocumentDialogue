import os
import re
import uuid
import logging
from werkzeug.utils import secure_filename
from langchain_openai import OpenAIEmbeddings
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader, 
    TextLoader, 
    Docx2txtLoader
)
from langchain_community.retrievers import BM25Retriever
from config import UPLOAD_FOLDER, ALLOWED_EXTENSIONS, CHROMA_PERSIST_DIRECTORY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

embeddings = OllamaEmbeddings(
    model="nomic-embed-text:latest",
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, user_id):
    """Save an uploaded file and return metadata for database storage"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Create secure unique filename
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    
    # Ensure user directory exists
    user_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(user_dir, unique_filename)
    file.save(file_path)
    
    return {
        'filename': unique_filename,
        'original_filename': original_filename,
        'file_path': file_path,
        'file_type': ext,
        'file_size': os.path.getsize(file_path)
    }


def load_document(file_path, file_type):
    """Load a document based on its file type"""
    if file_type == 'pdf':
        loader = PyPDFLoader(file_path)
    elif file_type == 'txt':
        loader = TextLoader(file_path)
    elif file_type == 'docx':
        loader = Docx2txtLoader(file_path)
    else:
        logger.error(f"Unsupported file type: {file_type}")
        return None
    
    # Load document content
    doc_content = loader.load()
    
    return doc_content


def process_document(document):
    """Process a document and create embeddings in ChromaDB"""
    try:
        # Load document based on file type
        file_path = document.file_path
        file_type = document.file_type.lower()
        
        if file_type == 'pdf':
            loader = PyPDFLoader(file_path)
        elif file_type == 'txt':
            loader = TextLoader(file_path)
        elif file_type == 'docx':
            loader = Docx2txtLoader(file_path)
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return False
        
        # Load document content
        doc_content = loader.load()
        
        # Split text into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        docs = text_splitter.split_documents(doc_content)
        
        # Clean text in documents
        for doc in docs:
            # Replace multiple spaces and newlines with single space
            doc.page_content = re.sub(r'\s+', ' ', doc.page_content).strip()
            
            # Add document metadata
            doc.metadata["document_id"] = document.id
            doc.metadata["user_id"] = document.user_id
            doc.metadata["filename"] = document.original_filename
            
        # Create vector store
        collection_name = f"user_{document.user_id}_doc_{document.id}"
        # embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Store embeddings in ChromaDB
        Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            collection_name=collection_name
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return False

def get_document_chroma(document_id, user_id):
    """Get the ChromaDB collection for a document"""
    try:
        collection_name = f"user_{user_id}_doc_{document_id}"
        # embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        
        # Load the existing ChromaDB collection
        db = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY
        )
        
        return db
    except Exception as e:
        logger.error(f"Error loading ChromaDB: {str(e)}")
        return None
    

def get_bm25_retriever(document_path,document_type):
    """Get the BM25 index for a document"""
    try:
        # Load the document based on its type
        doc = load_document(document_path, document_type)
        if not doc:
            return None
        # Create a text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # Split the document into chunks
        docs = text_splitter.split_documents(doc)
        
        keyword_retriever = BM25Retriever.from_documents(docs)
        keyword_retriever.k =  3


        
        
        return keyword_retriever
    except Exception as e:
        logger.error(f"Error loading BM25 index: {str(e)}")
        return None

def delete_document_embeddings(collection_name):
    """Delete a document collection from ChromaDB"""
    try:
        # embeddings = OpenAIEmbeddings()
        
        # Load the collection
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name=collection_name
        )
        
        # Delete the collection
        vectorstore.delete_collection()
        
        return True
    except Exception as e:
        logger.error(f"Error deleting document embeddings: {e}")
        return False