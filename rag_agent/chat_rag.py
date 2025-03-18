#!/usr/bin/env python
"""
RAG AI Assistant Chat Interface
Interactive command-line chatbot that uses the RAG query engine to answer questions
about the project workflow system with knowledge retrieval.
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List, Dict, Any

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.progress import Progress
except ImportError:
    print("Error: Rich is not installed. Please run setup_rag.bat or setup_rag.sh first.")
    sys.exit(1)

# Add parent directory to path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from query_engine import ask_rag_agent
except ImportError:
    print("Error: Could not import query_engine. Make sure all files are in place.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", f"rag_chat_{datetime.now().strftime('%Y%m%d')}.log")),
        logging.StreamHandler(sys.stderr)  # Log to stderr to avoid interfering with the UI
    ]
)
logger = logging.getLogger("rag_chat")

# Initialize Rich console
console = Console()

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def display_welcome_message():
    """Display the welcome message and help information."""
    console.print(Panel.fit(
        "🤖 [bold blue]Project Workflow RAG Assistant[/bold blue]\n\n"
        "Ask questions about your project, and I'll use my knowledge base to help you.\n"
        "Type [bold green]/help[/bold green] for command list or [bold red]/exit[/bold red] to quit.",
        title="Welcome",
        border_style="blue"
    ))

def display_help():
    """Display help information about available commands."""
    help_text = """
# Available Commands

- Type your question normally to get an answer
- `/help` - Show this help message
- `/clear` - Clear the chat history
- `/debug` - Toggle debug information
- `/exit` or `quit` - Exit the assistant

# Example Questions

- "What are the key features of this project?"
- "How do I use the slash commands in this system?"
- "Where are log files stored?"
- "Explain the GitHub issue tracking workflow"
    """
    console.print(Markdown(help_text))

def handle_command(command: str, show_debug: bool) -> tuple:
    """Handle special commands and return (continue_chat, show_debug) flags."""
    if command.lower() in ['/exit', 'exit', 'quit', '/quit']:
        console.print("[yellow]Goodbye! Have a great day![/yellow]")
        return False, show_debug
    
    if command.lower() == '/help':
        display_help()
        return True, show_debug
    
    if command.lower() == '/clear':
        clear_screen()
        display_welcome_message()
        return True, show_debug
    
    if command.lower() == '/debug':
        new_debug_setting = not show_debug
        status = "enabled" if new_debug_setting else "disabled"
        console.print(f"[blue]Debug information {status}[/blue]")
        return True, new_debug_setting
    
    return True, show_debug

def format_sources(sources: List[Dict[str, str]]) -> str:
    """Format source information for display."""
    if not sources:
        return ""
    
    result = "\n\n[dim]Sources:[/dim]\n"
    for src in sources:
        result += f"[dim]- {src['source']} ({src['type']})[/dim]\n"
    
    return result

def main():
    """Main chat loop for the RAG assistant."""
    clear_screen()
    display_welcome_message()
    
    show_debug = False
    continue_chat = True
    
    while continue_chat:
        try:
            # Get user input
            user_input = console.input("\n[bold green]You:[/bold green] ")
            
            # Skip empty inputs
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.startswith('/'):
                continue_chat, show_debug = handle_command(user_input, show_debug)
                continue
            
            # Process the query
            logger.info(f"User query: {user_input}")
            
            # Show thinking animation
            with Progress(transient=True) as progress:
                task = progress.add_task("[cyan]Thinking...", total=None)
                
                # Process the query in the background
                response = ask_rag_agent(user_input)
                
                # Make sure the animation shows for at least a moment
                time.sleep(0.5)
            
            # Split response into answer and sources
            parts = response.split("\nSources:")
            answer = parts[0]
            sources_text = "\nSources:" + parts[1] if len(parts) > 1 else ""
            
            # Display the answer
            console.print("\n[bold blue]AI:[/bold blue]", end=" ")
            console.print(Markdown(answer.strip()))
            
            # Display sources if available
            if sources_text and not show_debug:
                # Extract sources in a cleaner format for display
                source_lines = [line.strip() for line in sources_text.split('\n') if line.strip().startswith('-')]
                for line in source_lines:
                    console.print(f"[dim]{line}[/dim]")
            
            # Show debug information if enabled
            if show_debug and sources_text:
                console.print(Markdown(sources_text))
                
                # Show timing information if available
                if "[Response generated in" in response:
                    timing = response.split("[Response generated in")[1].split("]")[0].strip()
                    console.print(f"[dim]Response time: {timing} seconds[/dim]")
        
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /exit to quit.[/yellow]")
        
        except Exception as e:
            logger.error(f"Error in chat loop: {e}")
            console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())