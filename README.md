# AI Code Engineering Agent

A repository-level code review platform combining deterministic static analysis with optional AI-assisted engineering review.

## What it does

- Secure ZIP repository ingestion with size, file-count and path-traversal protections
- Public GitHub repository review
- Python and Java source scanning
- Security, reliability and maintainability findings
- Rule IDs, severity, category, source location and remediation guidance
- Optional OpenAI engineering review with graceful local fallback
- SQLite persistence and analysis history
- Health score, severity dashboard, search and filtering
- REST endpoints for review, health and history

## Run on Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Or double-click `start.bat` after dependencies are installed.

Open:

`http://127.0.0.1:8000/dashboard`

## Enable AI review

Create `backend/.env`:

```text
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.6-luna
```

Without a working API key/model, the application still returns an evidence-based local engineering review instead of showing a broken AI section.

## API

- `GET /health`
- `POST /review`
- `POST /review/github`
- `GET /history`
- `GET /history/{repository_id}`

## Test

```powershell
python -m pytest -q
```

The included test repository intentionally contains bad examples so the analyzer can be demonstrated locally.
