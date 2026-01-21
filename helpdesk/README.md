# AI Helpdesk (MVP)

This is a minimal AI helpdesk you can run without external tools. It:
- Answers user questions using a local knowledge base (`kb/`).
- Escalates to a "ticket" when confidence is low or policy requires human review.
- Stores tickets locally (`storage/tickets.json`).
- Grows the KB automatically by drafting new runbooks from solved questions.

## Quick start

1. Install dependencies in a virtualenv:
   ```bash
   pip install -r helpdesk/requirements.txt
   ```

2. Configure environment:
   - Copy `helpdesk/.env.example` to `helpdesk/.env` and fill values (model provider, API key).

3. Run the server:
   ```bash
   uvicorn helpdesk.app:app --reload
   ```

4. Test endpoints:
   - `POST /chat` with:
     ```json
     { "question": "VPN not connecting", "user": { "id": "u123", "email": "user@example.com" } }
     ```
   - `POST /ticket` with:
     ```json
     { "summary": "VPN issue", "details": "User u123 cannot connect", "user": { "id": "u123" } }
     ```

## Architecture

- `helpdesk/app.py`: FastAPI app providing `/chat` and `/ticket`.
- `helpdesk/prompts/helpdesk_system.md`: System prompt defining persona, rules, and style.
- `helpdesk/kb/`: Markdown docs used by retrieval (RAG-lite via simple text search initially).
- `helpdesk/storage/tickets.json`: Local ticket store.

## Generate-as-you-go workflow

1. User asks a question in `/chat`.
2. Assistant searches `kb/` and proposes step-by-step troubleshooting.
3. If confidence < 0.7 or policy requires human, it calls `/ticket` to escalate.
4. When resolved, assistant proposes a new KB doc summarizing the fix and references.

## Model choice

- Default: Anthropic Claude Sonnet (best for multi-step reasoning and policy-aware troubleshooting).
- You can switch to GPT‑5 or Opus by updating `LLM_PROVIDER` and `LLM_MODEL` in `.env`.

## Future integrations (optional, later)

- Ticketing: Zendesk/Jira/ServiceNow adapters
- Identity/Access: Okta/Azure AD
- Device/MDM: Intune/Jamf
- Monitoring: Datadog/New Relic
- Slack/Teams bot interface
