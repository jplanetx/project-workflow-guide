#!/usr/bin/env python
"""
Maintenance Script for RAG AI Assistant
Provides utilities to manage the Mem0 database and rebuild the document index.
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

# Path to Mem0 database
MEM0_DB_PATH = os.path.join(ROOT_DIR, "rag_agent", "mem0_db")

def clear_mem0_db():
    """Clear the Mem0 database by deleting and recreating the directory."""
    logger.info(f"Clearing Mem0 database at {MEM0_DB_PATH}")
    
    try:
        if os.path.exists(MEM0_DB_PATH):
            # Create backup first
            backup_dir = f"{MEM0_DB_PATH}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Creating backup at {backup_dir}")
            shutil.copytree(MEM0_DB_PATH, backup_dir)
            
            # Remove existing database
            shutil.rmtree(MEM0_DB_PATH)
        
        # Create fresh directory
        os.makedirs(MEM0_DB_PATH, exist_ok=True)
        logger.info("Mem0 database cleared successfully")
        print("✅ Mem0 database cleared.")
        return True
    
    except Exception as e:
        logger.error(f"Error clearing Mem0 database: {e}")
        print(f"❌ Error clearing Mem0 database: {e}")
        return False

def rebuild_mem0_db():
    """Rebuild the Mem0 database by running the indexing script."""
    logger.info("Rebuilding Mem0 database")
    
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
            logger.info("Mem0 database rebuilt successfully")
            print("✅ Mem0 database rebuilt successfully.")
            return True
        else:
            logger.error(f"Error rebuilding Mem0 database. Exit code: {result}")
            print(f"❌ Error rebuilding Mem0 database. See logs for details.")
            return False
    
    except Exception as e:
        logger.error(f"Error rebuilding Mem0 database: {e}")
        print(f"❌ Error: {e}")
        return False

def check_mem0_status():
    """Check the status of the Mem0 database."""
    logger.info("Checking Mem0 database status")
    
    try:
        # Check if database directory exists
        if not os.path.exists(MEM0_DB_PATH):
            logger.warning(f"Mem0 database not found at {MEM0_DB_PATH}")
            print(f"⚠️ Mem0 database not found at {MEM0_DB_PATH}")
            return False
        
        # Check for essential files
        files = os.listdir(MEM0_DB_PATH)
        
        if not files:
            logger.warning("Mem0 database directory is empty")
            print("⚠️ Mem0 database directory is empty.")
            return False
        
        # Check database size
        total_size = sum(os.path.getsize(os.path.join(MEM0_DB_PATH, f)) for f in files if os.path.isfile(os.path.join(MEM0_DB_PATH, f)))
        
        logger.info(f"Mem0 database contains {len(files)} files, total size: {total_size / (1024*1024):.2f} MB")
        print(f"✅ Mem0 database status: {len(files)} files, {total_size / (1024*1024):.2f} MB")
        
        return True
    
    except Exception as e:
        logger.error(f"Error checking Mem0 database status: {e}")
        print(f"❌ Error: {e}")
        return False

def main():
    """Main entry point for the maintenance script."""
    parser = argparse.ArgumentParser(description="Maintenance tools for RAG AI Assistant")
    
    # Add command line arguments
    parser.add_argument('--clear', action='store_true', help="Clear the Mem0 database")
    parser.add_argument('--rebuild', action='store_true', help="Rebuild the Mem0 database")
    parser.add_argument('--status', action='store_true', help="Check the status of the Mem0 database")
    parser.add_argument('--reset', action='store_true', help="Clear and rebuild the Mem0 database")
    
    args = parser.parse_args()
    
    # If no arguments specified, show help
    if not any([args.clear, args.rebuild, args.status, args.reset]):
        parser.print_help()
        return 0
    
    # Check status
    if args.status:
        check_mem0_status()
    
    # Clear database
    if args.clear or args.reset:
        clear_mem0_db()
    
    # Rebuild database
    if args.rebuild or args.reset:
        rebuild_mem0_db()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())