#!/usr/bin/env python
"""
Document Ingestion for RAG AI Assistant
This script loads documents from docs/, logs/, and scripts/ folders
and stores them in ChromaDB for knowledge retrieval.
"""

import os
import sys
import glob
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Try to install required packages if they're missing
print("Checking and installing required dependencies...")
try:
    # Attempt to install dependencies automatically
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "chromadb", "sentence-transformers", "langchain"])
    print("Dependencies installed successfully.")
except Exception as e:
    print(f"Warning: Could not automatically install dependencies: {e}")
    print("Please manually install the required packages:")
    print("pip install chromadb sentence-transformers langchain")

# Now try to import the required packages
try:
    import chromadb
    from chromadb.utils import embedding_functions
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    print("All required packages imported successfully.")
except ImportError as e:
    print(f"Error: Required dependency not available: {e}")
    print("Please install the missing packages manually using:")
    print("pip install chromadb sentence-transformers langchain")
    sys.exit(1)

# Configure logging
try:
    os.makedirs("logs", exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join("logs", f"rag_indexing_{datetime.now().strftime('%Y%m%d')}.log")),
            logging.StreamHandler()
        ]
    )
except Exception as e:
    print(f"Warning: Could not set up logging: {e}")
    # Fallback to simple logging
    logging.basicConfig(level=logging.INFO)

logger = logging.getLogger("rag_indexer")

# Path to project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories to scan for documents
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

# Path to ChromaDB database
CHROMA_DB_PATH = os.path.join(ROOT_DIR, "rag_agent", "chroma_db")

def ensure_dir_exists(path: str) -> None:
    """Create directory if it doesn't exist."""
    os.makedirs(path, exist_ok=True)

def is_text_file(filename: str) -> bool:
    """Check if a file is a text file based on extension."""
    text_extensions = {'.md', '.txt', '.py', '.log', '.json', '.ini', '.bat', '.sh', '.ps1'}
    return os.path.splitext(filename)[1].lower() in text_extensions

def read_text_file(filepath: str) -> str:
    """Read content of a text file safely."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {filepath}: {e}")
        return f"Error reading file: {e}"

def gather_documents() -> List[Dict[str, Any]]:
    """Gather documents from docs, logs, and scripts directories."""
    documents = []
    
    # Process docs directory
    logger.info(f"Scanning docs directory: {DOCS_DIR}")
    for filepath in glob.glob(os.path.join(DOCS_DIR, "**", "*"), recursive=True):
        if os.path.isfile(filepath) and is_text_file(filepath):
            rel_path = os.path.relpath(filepath, ROOT_DIR)
            logger.debug(f"Processing document: {rel_path}")
            content = read_text_file(filepath)
            documents.append({
                "content": content,
                "metadata": {
                    "source": rel_path,
                    "type": "documentation",
                    "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                }
            })
    
    # Process scripts directory
    logger.info(f"Scanning scripts directory: {SCRIPTS_DIR}")
    for filepath in glob.glob(os.path.join(SCRIPTS_DIR, "*.py")):
        if os.path.isfile(filepath):
            rel_path = os.path.relpath(filepath, ROOT_DIR)
            logger.debug(f"Processing script: {rel_path}")
            content = read_text_file(filepath)
            documents.append({
                "content": content,
                "metadata": {
                    "source": rel_path,
                    "type": "script",
                    "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                    "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
                }
            })
    
    # Process logs directory (recent logs only)
    logger.info(f"Scanning logs directory: {LOGS_DIR}")
    log_files = []
    for filepath in glob.glob(os.path.join(LOGS_DIR, "*.log")):
        if os.path.isfile(filepath):
            log_files.append((filepath, os.path.getmtime(filepath)))
    
    # Sort by modification time (newest first) and take only 5 most recent
    log_files.sort(key=lambda x: x[1], reverse=True)
    for filepath, _ in log_files[:5]:
        rel_path = os.path.relpath(filepath, ROOT_DIR)
        logger.debug(f"Processing log: {rel_path}")
        content = read_text_file(filepath)
        documents.append({
            "content": content,
            "metadata": {
                "source": rel_path,
                "type": "log",
                "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            }
        })
    
    return documents

def chunk_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Split documents into smaller chunks for better retrieval."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    chunked_docs = []
    
    for doc in documents:
        content = doc["content"]
        metadata = doc["metadata"]
        
        # Skip tiny documents
        if len(content) < 100:
            chunked_docs.append(doc)
            continue
        
        # Split content into chunks
        texts = text_splitter.split_text(content)
        
        # Create new document for each chunk
        for i, chunk_text in enumerate(texts):
            chunk_doc = {
                "content": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": i,
                    "is_chunk": True,
                    "chunk_count": len(texts)
                }
            }
            chunked_docs.append(chunk_doc)
    
    return chunked_docs

def main():
    """Index documents and store them in ChromaDB."""
    logger.info("Starting document indexing process...")
    
    # Create ChromaDB directory if it doesn't exist
    ensure_dir_exists(CHROMA_DB_PATH)
    
    try:
        # Initialize sentence transformers embedding function
        logger.info("Initializing embedding function")
        print("Initializing sentence transformer embedding function...")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at {CHROMA_DB_PATH}")
        print(f"Initializing ChromaDB at {CHROMA_DB_PATH}...")
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        
        # Delete the old collection and create a new one
        client.delete_collection("project_knowledge")
        collection = client.create_collection(
            name="project_knowledge",
            embedding_function=ef
        )

        # Gather and process documents
        print("Gathering documents from project directories...")
        documents = gather_documents()
        chunks = chunk_documents(documents)
        
        # Clear existing documents from the collection
        print("Clearing existing documents from the collection...")
        try:
            # Try to get all document IDs first
            result = collection.get()
            if result and result['ids']:
                # Delete all documents by their IDs
                collection.delete(ids=result['ids'])
                print(f"Deleted {len(result['ids'])} existing documents")
            else:
                print("No existing documents to delete")
        except Exception as e:
            # If collection is empty or doesn't exist yet, this is fine
            print(f"Note: Could not retrieve existing documents: {e}")
        
        # Add chunks to collection
        print(f"Adding {len(chunks)} chunks to the collection...")
        collection.add(
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[chunk["metadata"] for chunk in chunks],
            ids=[f"chunk-{i}" for i in range(len(chunks))]
        )
        
        print("✅ Successfully indexed all documents!")
        return True

    except Exception as e:
        logger.error(f"Error indexing documents: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    sys.exit(main())
