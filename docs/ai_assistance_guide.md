# AI Assistance Guide

This guide covers the AI-powered features available in the Project Workflow system to enhance productivity and knowledge management.

## Table of Contents

1. [RAG AI Assistant](#rag-ai-assistant)
2. [Slash Commands](#slash-commands)
3. [GitHub Issue Integration](#github-issue-integration)
4. [Token Usage Tracking](#token-usage-tracking)
5. [Troubleshooting](#troubleshooting)

## RAG AI Assistant

The RAG (Retrieval-Augmented Generation) AI Assistant provides intelligent answers to questions about your project by retrieving relevant information from your project documentation, logs, and scripts.

### Setup

1. Run the setup script to install dependencies:
   ```bash
   # Windows
   setup_rag.bat
   
   # Linux/Mac
   ./setup_rag.sh
   ```

2. Index your project documents:
   ```bash
   python rag_agent/index_documents.py
   ```

3. Start the chat interface:
   ```bash
   python rag_agent/chat_rag.py
   ```

### How It Works

1. The AI assistant uses **Mem0** for knowledge storage and retrieval.
2. When you ask a question, it searches for the most relevant documents in your project.
3. It then combines the retrieved information with AI capabilities to generate accurate answers.
4. All sources are cited so you know where the information comes from.

### Available Commands

In the chat interface, you can use these commands:
- `/help` - Show help information
- `/clear` - Clear the chat history
- `/debug` - Toggle debug information (shows retrieval details)
- `/exit` or `quit` - Exit the assistant

### Maintenance

To maintain the knowledge base:

```bash
# Check database status
python scripts/maintenance.py --status

# Clear and rebuild the knowledge base
python scripts/maintenance.py --reset

# Just rebuild without clearing
python scripts/maintenance.py --rebuild
```

## Slash Commands

The system provides AI-powered slash commands for common tasks:

- `/check-bugs`: Fetch unresolved GitHub issues, highlighting ones labeled as bugs
  ```bash
  python scripts/slash_commands.py /check-bugs
  ```

- `/summarize-docs`: Generate an AI summary of the README
  ```bash
  python scripts/slash_commands.py /summarize-docs
  ```

- `/generate-tests`: AI generates unit tests for recent code changes
  ```bash
  python scripts/slash_commands.py /generate-tests
  ```

To reduce token consumption, add the `--brief_mode` flag:
```bash
python scripts/slash_commands.py /check-bugs --brief_mode
```

For more details, see [Slash Commands Guide](slash_commands_guide.md).

## GitHub Issue Integration

The system provides intelligent GitHub issue management with:

- **Fuzzy matching** to find similar issues
- **Smart linking** to avoid duplicate issues
- **Automatic context collection** for AI assistance

When creating a new task, the system will:
1. Check for similar existing issues
2. Show match percentages
3. Let you link to existing issues instead of creating duplicates

## Token Usage Tracking

All AI interactions are tracked for cost optimization:

```bash
# View monthly token usage
python scripts/token_tracker.py report month

# View task-specific token usage
python scripts/token_tracker.py report task TASK_ID

# Get token saving recommendations
python scripts/token_tracker.py report tips
```

## Troubleshooting

### RAG Assistant Issues

- **Missing dependencies**: Run the setup script again
- **No results returned**: Make sure you've indexed your documents
- **Slow responses**: Try rebuilding your knowledge base
- **Missing API key**: Set the OPENAI_API_KEY environment variable

### Slash Commands Issues

- **Command not found**: Ensure you're using the correct command format
- **GitHub API issues**: Check your GitHub token in the .env file

### GitHub Integration Issues

- **Authorization errors**: Update your GitHub token
- **Rate limiting**: Wait and try again later
- **Connection issues**: Check your internet connection