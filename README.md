# Fieldnote AI — Product Knowledge Assistant

I built Fieldnote as a small applied AI project: a question-and-answer assistant for a fictional AI software workspace called Relay. Its sample product guides cover knowledge search, workflow approvals, evaluation, integrations, prompt design and data handling. The material is fictional and contains no real customer or company data.

## Try it

Start the app and ask one of the suggested questions, or try:

- Why might an answer have no source links?
- When should a workflow ask for human approval?
- How do I evaluate a new AI workflow?
- What should I check when a knowledge connector stops returning current documents?
- What information should I avoid putting into a prompt?

Fieldnote searches the included guides, shows the source behind an answer, and says when it cannot find enough information. It is a document-grounded demo, not a general chatbot or live Relay product documentation.

## Run locally

Requires Python 3.10 or newer.

```powershell
cd fieldnote-ai
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5050`. The app works without an API key: it returns relevant source text directly. To try model-generated answers, copy `.env.example` to `.env`, set `OPENAI_API_KEY`, and restart. The browser never receives the key. Keep `.env` private and out of Git.

## How it works

1. The browser sends a question to Flask at `/api/ask`.
2. A compact BM25-style search ranks passages in `data/manuals.json`.
3. If there is not enough evidence, Fieldnote abstains.
4. Without a model key, it quotes the best-matching passage. With a key, it can ask the OpenAI Responses API to answer using retrieved passages and cite them.
5. The interface displays the answer mode and source titles so a person can review the result.

The project also includes `evaluate.py` and a small set of expected source matches and out-of-scope questions in `data/evaluation.json`. I have not yet reviewed benchmark results, so I do not claim a score.

## What I learned and what I would improve

This project let me practise connecting a Python web service to a retrieval flow and a simple browser interface. It also helped me explore how source links, a fallback response and an abstention path can make an AI feature easier to inspect.

The retriever uses lexical matching rather than embeddings, so it can miss related questions that use different words. The evidence threshold is a heuristic and the evaluation set is small and self-authored. Before using a system like this with real information, I would expand and review the evaluation data, test answer support and citation quality, add security and privacy controls, and have subject matter experts review its behaviour.

## Main files

- `app.py` — Flask routes, retrieval, fallback, abstention and optional model call.
- `data/manuals.json` — fictional Relay AI Workspace product guides.
- `data/evaluation.json` — example questions, expected sources and out-of-scope prompts.
- `evaluate.py` — repeatable retrieval and abstention evaluation script.
- `templates/index.html`, `static/style.css` — responsive question interface and source display.
