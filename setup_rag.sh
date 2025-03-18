#!/bin/bash
echo "Setting up RAG AI Assistant..."

# Create virtual environment if it doesn't exist
if [ ! -d "rag_venv" ]; then
    echo "Creating virtual environment..."
    python -m venv rag_venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source rag_venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r rag_agent/requirements.txt

echo "RAG AI Assistant setup complete!"
echo "You can now run:"
echo "- python rag_agent/index_documents.py (to index your documentation)"
echo "- python rag_agent/chat_rag.py (to start the chat interface)"