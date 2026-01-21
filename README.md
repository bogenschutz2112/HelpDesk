# HelpDesk

An AI-powered helpdesk system that runs locally without external dependencies.

## Features

- 🤖 AI-powered chat interface with local knowledge base
- 📝 Local ticket storage (no external systems required)
- 🔍 Simple RAG-lite search over Markdown documentation
- 🎯 Smart escalation based on confidence thresholds
- 🔌 Pluggable LLM providers (Anthropic Claude Sonnet by default)

## Quick Start

See the [helpdesk README](helpdesk/README.md) for detailed setup instructions.

```bash
# Install dependencies
pip install -r helpdesk/requirements.txt

# Configure environment (copy .env.example to .env)
cp helpdesk/.env.example helpdesk/.env

# Run the server
uvicorn helpdesk.app:app --reload

# Test the system
python test_helpdesk.py
```

## Architecture

- **FastAPI Application**: REST API with `/chat` and `/ticket` endpoints
- **Knowledge Base**: Local Markdown files in `helpdesk/kb/`
- **Ticket Storage**: JSON file at `helpdesk/storage/tickets.json`
- **LLM Integration**: Anthropic Claude Sonnet with heuristic fallback

## Documentation

- [Helpdesk README](helpdesk/README.md) - Full documentation
- [System Prompt](helpdesk/prompts/helpdesk_system.md) - AI assistant persona
- [FAQ](helpdesk/kb/faq.md) - Seed knowledge base
