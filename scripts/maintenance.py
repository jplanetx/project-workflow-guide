#!/usr/bin/env python
"""
Maintenance Script for RAG AI Assistant
Provides utilities to manage the ChromaDB database and rebuild the document index.
"""

import os
import sys
import shutil
import argparse
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"rag_maintenance_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_maintenance")

# Path to project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to ChromaDB database
CHROMA_DB_PATH = os.path.join(ROOT_DIR, "rag_agent", "chroma_db")

def clear_vector_db():
    """Clear the ChromaDB database by deleting and recreating the directory."""
    logger.info(f"Clearing ChromaDB database at {CHROMA_DB_PATH}")
    
    try:
        if os.path.exists(CHROMA_DB_PATH):
            # Create backup first
            backup_dir = f"{CHROMA_DB_PATH}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Creating backup at {backup_dir}")
            shutil.copytree(CHROMA_DB_PATH, backup_dir)
            
            # Remove existing database
            shutil.rmtree(CHROMA_DB_PATH)
        
        # Create fresh directory
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        logger.info("ChromaDB database cleared successfully")
        print("✅ Vector database cleared.")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing vector database: {e}")
        print(f"❌ Error clearing vector database: {e}")
        return False

def rebuild_vector_db():
    """Rebuild the vector database by running the indexing script."""
    logger.info("Rebuilding vector database")
    
    try:
        # Get path to index_documents.py
        index_script = os.path.join(ROOT_DIR, "rag_agent", "index_documents.py")
        
        if not os.path.exists(index_script):
            logger.error(f"Indexing script not found at {index_script}")
            print(f"❌ Error: Indexing script not found at {index_script}")
            return False
        
        # Get Python executable path
        python_exe = sys.executable
        
        # Run the indexing script
        logger.info(f"Running {python_exe} {index_script}")
        print(f"Running indexing script...")
        result = os.system(f'"{python_exe}" "{index_script}"')
        
        if result == 0:
            logger.info("Vector database rebuilt successfully")
            print("✅ Vector database rebuilt successfully.")
            return True
        else:
            logger.error(f"Error rebuilding vector database. Exit code: {result}")
            print(f"❌ Error rebuilding vector database. See logs for details.")
            return False
    
    except Exception as e:
        logger.error(f"Error rebuilding vector database: {e}")
        print(f"❌ Error: {e}")
        return False

def check_vector_db_status():
    """Check the status of the vector database."""
    logger.info("Checking vector database status")
    
    try:
        # Check if database directory exists
        if not os.path.exists(CHROMA_DB_PATH):
            logger.warning(f"Vector database not found at {CHROMA_DB_PATH}")
            print(f"⚠️ Vector database not found at {CHROMA_DB_PATH}")
            return False
        
        # Check for essential files
        files = os.listdir(CHROMA_DB_PATH)
        
        if not files:
            logger.warning("Vector database directory is empty")
            print("⚠️ Vector database directory is empty.")
            return False
        
        # Check database size
        total_size = sum(os.path.getsize(os.path.join(CHROMA_DB_PATH, f)) 
                         for f in files if os.path.isfile(os.path.join(CHROMA_DB_PATH, f)))
        
        logger.info(f"Vector database contains {len(files)} files, total size: {total_size / (1024*1024):.2f} MB")
        print(f"✅ Vector database status: {len(files)} files, {total_size / (1024*1024):.2f} MB")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking vector database status: {e}")
        print(f"❌ Error: {e}")
        return False

def main():
    """Main entry point for the maintenance script."""
    parser = argparse.ArgumentParser(description="Maintenance tools for RAG AI Assistant")
    
    # Add command line arguments
    parser.add_argument('--clear', action='store_true', help="Clear the vector database")
    parser.add_argument('--rebuild', action='store_true', help="Rebuild the vector database")
    parser.add_argument('--status', action='store_true', help="Check the status of the vector database")
    parser.add_argument('--reset', action='store_true', help="Clear and rebuild the vector database")
    
    args = parser.parse_args()
    
    # If no arguments specified, show help
    if not any([args.clear, args.rebuild, args.status, args.reset]):
        parser.print_help()
        return 0
    
    # Check status
    if args.status:
        check_vector_db_status()
    
    # Clear database
    if args.clear or args.reset:
        clear_vector_db()
    
    # Rebuild database
    if args.rebuild or args.reset:
        rebuild_vector_db()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())