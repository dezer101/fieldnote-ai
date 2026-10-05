from __future__ import annotations
import json, math, os, re
from collections import Counter
from pathlib import Path
from flask import Flask, jsonify, render_template, request
ROOT = Path(__file__).parent
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass
TOKEN_RE = re.compile(r"[a-z0-9]+")
app = Flask(__name__)
with (ROOT / "data" / "manuals.json").open(encoding="utf-8-sig") as f:
    DOCUMENTS = json.load(f)["documents"]

def tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())

def retrieve(query: str, limit: int = 3) -> list[dict]:
    """Rank handbook passages with a small, explainable BM25-style scorer."""
    q = tokens(query)
    if not q:
        return []
    docs = [(d, tokens(d["title"] + " " + d["section"] + " " + d["text"])) for d in DOCUMENTS]
    avg_len = sum(len(ts) for _, ts in docs) / max(len(docs), 1)
    doc_freq = Counter(term for term in set(q) for _, ts in docs if term in ts)
    scored = []
    for doc, words in docs:
        freqs = Counter(words)
        score = 0.0
        for term in set(q):
            tf = freqs[term]
            if not tf:
                continue
            idf = math.log(1 + (len(docs) - doc_freq[term] + .5) / (doc_freq[term] + .5))
            score += idf * (tf * 2.2) / (tf + 1.2 * (.25 + .75 * len(words) / max(avg_len, 1)))
            if term in tokens(doc["title"]):
                score += .65
        if score:
            scored.append((score, doc))
    return [d for _, d in sorted(scored, key=lambda row: row[0], reverse=True)[:limit]]

def answer_query(query: str) -> dict:
    hits = retrieve(query)
    # This floor deliberately prefers a refusal over a weak lexical match.
    if not hits or sum(1 for t in set(tokens(query)) if t in tokens(hits[0]["title"] + " " + hits[0]["text"])) < 2:
        return {"answer": "I couldn't find enough relevant information in the sample product guides to answer that. Try asking about workspace setup, source links, workflow approvals, evaluations, connectors, data handling or prompt design.", "sources": [], "mode": "grounded fallback"}
    source = hits[0]
    if os.getenv("OPENAI_API_KEY"):
        try:
            from openai import OpenAI
            context = "\n".join(f"[{d['id']}] {d['title']} — {d['text']}" for d in hits)
            result = OpenAI().responses.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                instructions=("Answer only from the supplied sample service handbook passages. "
                    "Cite every operational claim using the passage id in square brackets. "
                    "If the passages do not support an answer, say so and advise escalation. "
                    "Do not provide instructions that bypass safety protections or invent procedures."),
                input=f"Question: {query}\n\nHandbook passages:\n{context}",
                store=False, max_output_tokens=220,
            )
            answer = result.output_text.strip()
            if answer:
                return {"answer": answer, "sources": hits, "mode": "LLM with retrieved sources"}
        except Exception:
            pass
    # Keyless mode quotes the ranked source, so the demo remains useful offline.
    sentences = re.split(r"(?<=[.!?])\s+", source["text"])
    q_terms = set(tokens(query))
    selected = sorted(sentences, key=lambda s: sum(t in tokens(s) for t in q_terms), reverse=True)[:2]
    selected = [s for s in selected if any(t in tokens(s) for t in q_terms)]
    answer = " ".join(selected) if selected else source["text"]
    return {"answer": answer, "sources": [source], "mode": "source extract fallback"}

@app.get("/")
def home():
    return render_template("index.html", document_count=len(DOCUMENTS), documents=DOCUMENTS, llm_enabled=bool(os.getenv("OPENAI_API_KEY")))

@app.post("/api/ask")
def ask():
    payload = request.get_json(silent=True) or {}
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip() or len(question) > 700:
        return jsonify(error="Enter a question of up to 700 characters."), 400
    return jsonify(answer_query(question.strip()))

@app.get("/api/health")
def health():
    return jsonify(ok=True, documents=len(DOCUMENTS), llm_enabled=bool(os.getenv("OPENAI_API_KEY")))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5050")), debug=False)
