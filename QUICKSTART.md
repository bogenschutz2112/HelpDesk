# Quick Reference Guide

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r helpdesk/requirements.txt

# Configure environment
cp helpdesk/.env.example helpdesk/.env
# Edit helpdesk/.env with your LLM provider credentials
```

## Running the Server

```bash
# Development mode (with auto-reload)
uvicorn helpdesk.app:app --reload

# Production mode
uvicorn helpdesk.app:app --host 0.0.0.0 --port 8000
```

## API Usage

### Chat Endpoint

Ask a question and get an AI-powered response with KB sources:

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "VPN not connecting",
    "user": {
      "id": "u123",
      "email": "user@example.com"
    }
  }'
```

Response:
```json
{
  "answer": "Assessment: Based on the KB...",
  "confidence": 0.75,
  "suggest_escalation": false,
  "sources": [
    {"title": "FAQ", "path": "helpdesk/kb/faq.md"}
  ]
}
```

### Ticket Endpoint

Create a ticket for human review:

```bash
curl -X POST http://localhost:8000/ticket \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "VPN connection issue",
    "details": "User cannot connect to corporate VPN",
    "user": {
      "id": "u123",
      "email": "user@example.com"
    }
  }'
```

Response:
```json
{
  "id": 1,
  "provider": "local",
  "path": "helpdesk/storage/tickets.json"
}
```

## Testing

```bash
# Run basic functionality tests
python test_helpdesk.py

# Check API documentation
# Navigate to http://localhost:8000/docs
```

## Adding Knowledge Base Content

Create new Markdown files in `helpdesk/kb/`:

```markdown
# New Topic

## Issue: Application crashes on startup

1. Check system requirements
2. Verify installation integrity
3. Review error logs
4. Contact support if issue persists

Sources: Internal KB, Support ticket #123
```

The system will automatically index new files on the next request.

## Configuration Options

Edit `helpdesk/.env`:

- `LLM_PROVIDER`: Choose `anthropic`, `openai`, or `google`
- `LLM_MODEL`: Model name (e.g., `claude-sonnet-4`)
- `LLM_API_KEY`: Your API key
- `CONFIDENCE_THRESHOLD`: Escalation threshold (0.0-1.0, default: 0.7)

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip list`
- Check for syntax errors: `python -m py_compile helpdesk/app.py`

### No KB sources found
- Ensure Markdown files exist in `helpdesk/kb/`
- Check file permissions
- Verify files have `.md` extension

### LLM API errors
- Verify API key is set correctly in `.env`
- Check API rate limits and quotas
- System falls back to heuristic mode if API is unavailable
