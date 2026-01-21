import os
import json
import glob
import re
import uuid
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join("helpdesk", ".env"))

# --- Config ---
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.7"))
KB_PATH = "helpdesk/kb/**/*.md"
TICKETS_JSON = "helpdesk/storage/tickets.json"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
LLM_MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4")
LLM_API_KEY = os.getenv("LLM_API_KEY")

app = FastAPI(title="AI Helpdesk (MVP)")

# --- Models ---
class UserCtx(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    org: Optional[str] = None

class ChatRequest(BaseModel):
    question: str
    user: UserCtx

class TicketRequest(BaseModel):
    summary: str
    details: str
    user: UserCtx

# --- Simple RAG-lite over local KB ---
@dataclass
class DocHit:
    path: str
    title: str
    snippet: str
    score: float


def ensure_dirs():
    os.makedirs("helpdesk/storage", exist_ok=True)
    os.makedirs("helpdesk/kb", exist_ok=True)
    os.makedirs("helpdesk/prompts", exist_ok=True)


def read_markdown_files() -> List[Dict[str, str]]:
    files = glob.glob(KB_PATH, recursive=True)
    docs = []
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                content = fh.read()
        except FileNotFoundError:
            continue
        title = content.splitlines()[0].strip("# ").strip() if content else os.path.basename(f)
        docs.append({"path": f, "title": title, "content": content})
    return docs


def simple_search(question: str, docs: List[Dict[str, str]]) -> List[DocHit]:
    hits = []
    q = question.lower()
    q_tokens = re.findall(r"\w+", q)
    for d in docs:
        text = d["content"].lower()
        score = sum(text.count(token) for token in q_tokens)
        if score > 0:
            idx = max(0, min(len(text) - 1, text.find(q_tokens[0]) if q_tokens else 0))
            snippet = d["content"][max(0, idx - 160):idx + 160]
            hits.append(DocHit(path=d["path"], title=d["title"], snippet=snippet, score=float(score)))
    return sorted(hits, key=lambda h: h.score, reverse=True)[:5]


# --- LLM adapter (Anthropic by default, heuristic fallback) ---

def llm_complete(system_prompt: str, question: str, sources: List[DocHit]) -> Dict[str, Any]:
    kb_sources = [{"title": s.title, "path": s.path} for s in sources]

    # If Anthropic is configured, use it for answer text; keep heuristics for confidence/escalation
    if LLM_PROVIDER == "anthropic" and LLM_API_KEY:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=LLM_API_KEY)
            src_text = "\n".join([f"- {s.title} ({s.path})\n{s.snippet}" for s in sources]) or "(no sources found)"
            user_msg = (
                f"Question:\n{question}\n\n"
                f"Relevant KB sources:\n{src_text}\n\n"
                "Write a concise assessment and numbered steps. Include a 'Sources' section listing titles and paths."
            )
            resp = client.messages.create(
                model=LLM_MODEL,
                max_tokens=800,
                system=system_prompt,
                messages=[{"role": "user", "content": user_msg}],
            )
            # Extract text blocks
            answer_text = "".join([b.text for b in resp.content if getattr(b, "type", "text") == "text"]) or ""
        except Exception as e:
            answer_text = (
                "Assessment: Unable to call Anthropic API. Falling back to heuristic answer. "
                f"Error: {e}"
            )
    else:
        # Heuristic text if no provider configured
        if not sources:
            answer_text = (
                "Assessment: I don't have enough information in the KB. "
                "Please confirm if you'd like to escalate a ticket."
            )
        else:
            steps = []
            for s in sources:
                steps.append(f"- From {os.path.basename(s.path)}: {s.snippet.strip().replace('\n', ' ')}")
            answer_text = (
                "Assessment: Based on the KB, try the following steps:\n" + "\n".join(steps) +
                "\n\nIf this fails, please confirm to escalate a ticket."
            )

    # Confidence & escalation heuristics
    if not sources:
        confidence = 0.4
        escalate = True
    else:
        confidence = 0.75
        escalate = False

    return {
        "answer": answer_text,
        "confidence": confidence,
        "escalate": escalate,
        "kb_sources": kb_sources,
    }


# --- Ticket storage ---

def load_tickets() -> List[Dict[str, Any]]:
    ensure_dirs()
    if not os.path.exists(TICKETS_JSON):
        with open(TICKETS_JSON, "w", encoding="utf-8") as fh:
            json.dump([], fh)
    with open(TICKETS_JSON, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_ticket_locally(ticket: Dict[str, Any]) -> Dict[str, Any]:
    tickets = load_tickets()
    ticket["id"] = str(uuid.uuid4())
    tickets.append(ticket)
    with open(TICKETS_JSON, "w", encoding="utf-8") as fh:
        json.dump(tickets, fh, indent=2)
    return ticket


# --- Routes ---
@app.post("/chat")
def chat(req: ChatRequest):
    ensure_dirs()
    # Load KB & system prompt
    docs = read_markdown_files()
    hits = simple_search(req.question, docs)
    with open("helpdesk/prompts/helpdesk_system.md", "r", encoding="utf-8") as fh:
        system_prompt = fh.read()
    result = llm_complete(system_prompt, req.question, hits)

    suggest_escalation = result["confidence"] < CONFIDENCE_THRESHOLD or result["escalate"]
    return {
        "answer": result["answer"],
        "confidence": result["confidence"],
        "suggest_escalation": suggest_escalation,
        "sources": result["kb_sources"],
    }


@app.post("/ticket")
def ticket(req: TicketRequest):
    ensure_dirs()
    labels = ["helpdesk", "triage"]
    t = save_ticket_locally({
        "summary": req.summary,
        "details": req.details,
        "user": req.user.model_dump(),
        "labels": labels
    })
    return {"id": t["id"], "provider": "local", "path": TICKETS_JSON}
