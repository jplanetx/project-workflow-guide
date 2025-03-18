#!/usr/bin/env python
"""
Document Ingestion for RAG AI Assistant
This script loads documents from docs/, logs/, and scripts/ folders
and stores them in Mem0 for knowledge retrieval.
"""

import os
import sys
import glob
import logging
from datetime import datetime
from typing import List, Dict, Any

try:
    from mem0 import Mem0
except ImportError:
    print("Error: Mem0 is not installed. Please run setup_rag.bat or setup_rag.sh first.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"rag_indexing_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_indexer")

# Path to project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories to scan for documents
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
SCRIPTS_DIR = os.path.join(ROOT_DIR, "scripts")

# Path to Mem0 database
MEM0_DB_PATH = os.path.join(ROOT_DIR, "rag_agent", "mem0_db")

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
                "text": content,
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
                "text": content,
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
            "text": content,
            "metadata": {
                "source": rel_path,
                "type": "log",
                "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat(),
                "modified": datetime.fromtimestamp(os.path.getmtime(filepath)).isoformat()
            }
        })
    
    return documents

def chunk_document(document: Dict[str, Any], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Split a document into smaller chunks with overlap."""
    text = document["text"]
    if len(text) <= chunk_size:
        return [document]
    
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk_text = text[i:i + chunk_size]
        if len(chunk_text) < 100:  # Skip very small chunks
            continue
            
        chunk_doc = {
            "text": chunk_text,
            "metadata": {
                **document["metadata"],
                "chunk_index": i // (chunk_size - overlap),
                "is_chunk": True
            }
        }
        chunks.append(chunk_doc)
    
    return chunks

def main():
    """Index documents and store them in Mem0."""
    logger.info("Starting document indexing process...")
    
    # Create Mem0 database directory if it doesn't exist
    ensure_dir_exists(MEM0_DB_PATH)
    
    try:
        # Initialize Mem0
        logger.info(f"Initializing Mem0 at {MEM0_DB_PATH}")
        mem = Mem0(persist_dir=MEM0_DB_PATH)
        
        # Gather documents
        documents = gather_documents()
        logger.info(f"Found {len(documents)} documents to index")
        
        # Chunk documents and flatten
        chunked_docs = []
        for doc in documents:
            chunked_docs.extend(chunk_document(doc))
        
        logger.info(f"Created {len(chunked_docs)} chunks from {len(documents)} documents")
        
        # Add documents to Mem0
        mem.add_documents(chunked_docs)
        
        logger.info(f"Successfully indexed {len(chunked_docs)} document chunks in Mem0")
        print(f"✅ Indexed {len(documents)} documents ({len(chunked_docs)} chunks) in Mem0.")
        
    except Exception as e:
        logger.error(f"Error indexing documents: {e}")
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())