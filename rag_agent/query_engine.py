#!/usr/bin/env python
"""
Query Engine for RAG AI Assistant
This module provides functionality to query the Mem0 knowledge base
and generate AI-powered responses using retrieved information.
"""

import os
import sys
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

try:
    from mem0 import Mem0
    import openai
except ImportError:
    print("Error: Required dependencies not installed. Please run setup_rag.bat or setup_rag.sh first.")
    sys.exit(1)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"rag_query_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("rag_query")

# Path to project root directory
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to Mem0 database
MEM0_DB_PATH = os.path.join(ROOT_DIR, "rag_agent", "mem0_db")

# Default AI model
DEFAULT_MODEL = "gpt-3.5-turbo"

class RAGQueryEngine:
    """RAG Query Engine for retrieving information and generating AI responses."""
    
    def __init__(self, model: str = None):
        """Initialize the query engine with Mem0 and OpenAI."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("RAG_MODEL", DEFAULT_MODEL)
        
        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found in environment. Responses will be generated without AI.")
        
        # Initialize Mem0
        try:
            logger.info(f"Initializing Mem0 from {MEM0_DB_PATH}")
            self.mem = Mem0(persist_dir=MEM0_DB_PATH)
            self.mem_initialized = True
        except Exception as e:
            logger.error(f"Error initializing Mem0: {e}")
            self.mem_initialized = False
    
    def retrieve_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant documents from Mem0 based on the query."""
        if not self.mem_initialized:
            logger.error("Cannot retrieve documents: Mem0 not initialized")
            return []
        
        try:
            logger.info(f"Retrieving documents for query: '{query}'")
            results = self.mem.query(query, top_k=top_k)
            logger.info(f"Retrieved {len(results)} documents")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents: {e}")
            return []
    
    def format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into a context string for the AI."""
        if not documents:
            return "No relevant documents found."
        
        context = "RELEVANT DOCUMENTS:\n\n"
        
        for i, doc in enumerate(documents, 1):
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown source")
            doc_type = metadata.get("type", "document")
            text = doc.get("text", "")
            
            # Limit text length to avoid context overflow
            if len(text) > 1000:
                text = text[:1000] + "...[truncated]"
            
            context += f"[Document {i}] {source} (Type: {doc_type})\n"
            context += f"{text}\n\n"
        
        return context
    
    def generate_ai_response(self, query: str, context: str) -> str:
        """Generate an AI response using OpenAI based on the query and context."""
        if not self.api_key:
            logger.warning("Generating response without AI due to missing API key")
            return self._generate_fallback_response(query, context)
        
        try:
            prompt = f"""You are an AI assistant for a software project workflow management system.
You have access to the following documents from the project:

{context}

Based only on the information provided above, please answer the following question.
If the information is not available in the documents, say "I don't have enough information about that in my knowledge base."

User Question: {query}

Answer:"""
            
            logger.info(f"Generating AI response using model: {self.model}")
            
            # Call OpenAI API
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant for a software project workflow system."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.info("AI response generated successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_fallback_response(query, context)
    
    def _generate_fallback_response(self, query: str, context: str) -> str:
        """Generate a fallback response when AI is unavailable."""
        # Extract snippets from context that might be relevant
        lines = context.split('\n')
        relevant_lines = []
        
        for line in lines:
            # Look for lines that might contain keywords from the query
            if any(keyword.lower() in line.lower() for keyword in query.split()):
                relevant_lines.append(line)
        
        response = "Based on the retrieved documents:\n\n"
        
        if relevant_lines:
            response += "\n".join(relevant_lines[:10])  # Limit to 10 relevant lines
        else:
            response += "I found some relevant documents, but couldn't pinpoint the exact answer. " \
                       "Here are the document sources:\n"
            
            # Extract document sources from context
            for line in lines:
                if line.startswith("[Document ") and "]" in line:
                    response += line + "\n"
        
        return response
    
    def ask(self, query: str) -> Dict[str, Any]:
        """Main method to ask a question and get an AI-powered response."""
        logger.info(f"Processing query: '{query}'")
        
        # Record start time for performance tracking
        start_time = datetime.now()
        
        # Retrieve relevant documents
        documents = self.retrieve_documents(query)
        
        # If no documents found, return early
        if not documents:
            logger.warning("No relevant documents found")
            return {
                "answer": "I don't have information about that in my knowledge base.",
                "sources": [],
                "retrieval_time": (datetime.now() - start_time).total_seconds()
            }
        
        # Format retrieved documents into context
        context = self.format_context(documents)
        
        # Generate AI response
        answer = self.generate_ai_response(query, context)
        
        # Extract source information for attribution
        sources = []
        for doc in documents:
            metadata = doc.get("metadata", {})
            source = metadata.get("source", "Unknown")
            
            # Skip duplicates
            if source not in [s["source"] for s in sources]:
                sources.append({
                    "source": source,
                    "type": metadata.get("type", "document")
                })
        
        # Calculate total processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"Query processed in {processing_time:.2f} seconds")
        
        return {
            "answer": answer,
            "sources": sources,
            "retrieval_time": processing_time
        }

# Global instance for easy imports
query_engine = RAGQueryEngine()

def ask_rag_agent(question: str) -> str:
    """Helper function to query the RAG agent."""
    result = query_engine.ask(question)
    
    answer = result["answer"]
    sources = result["sources"]
    time_taken = result["retrieval_time"]
    
    # Format the response with source attribution
    response = f"{answer}\n\n"
    
    if sources:
        response += "Sources:\n"
        for src in sources:
            response += f"- {src['source']} ({src['type']})\n"
    
    response += f"\n[Response generated in {time_taken:.2f} seconds]"
    
    return response