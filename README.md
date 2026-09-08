# Translation Service

A FastAPI web service that translates text into multiple languages via LLM
providers. Translations run asynchronously as background tasks and are stored in
PostgreSQL. Optional accounts add history and per-user provider/model/API-key
settings.

## Features

- Submit text and receive translations in multiple languages
- Asynchronous processing with FastAPI background tasks
- PostgreSQL storage for query tasks and results
- Web UI for submit, login/register, history, and LLM settings
- Multi-provider LLM support (OpenAI, Groq, Together, OpenRouter)
- REST API with automatic OpenAPI docs

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy
- **Auth:** Cookie session (`itsdangerous` signer) + bcrypt passwords
- **AI:** OpenAI-compatible providers (default model `gpt-4o-mini`)
- **Server:** Uvicorn / Gunicorn
- **Frontend:** Bootstrap 5 + Jinja2 templates

## Architecture

```
Browser / API client
        │
        ▼
FastAPI (app/main.py)
  ├── Cookie session → users (optional for /result)
  ├── Background task → util.perform_query (LLM provider)
  └── SQLAlchemy → PostgreSQL (users, query_tasks)
```

Anonymous users can still submit translations (server env API keys). Logged-in
users can attach tasks to their account, view `/history`, and override provider /
model / API key under `/settings` (API keys encrypted with Fernet).

## Project Structure

```text
├── .env.example          # Env template
├── docker-compose.yml    # App + Postgres 16
├── Dockerfile
├── requirements.txt
└── app/
    ├── main.py           # Routes (UI + API + auth)
    ├── models.py         # User, QueryTask
    ├── schemas.py        # Pydantic schemas
    ├── crud.py           # DB helpers, password + API-key crypto
    ├── database.py       # Engine / session
    ├── providers.py      # Provider registry + live /models cache
    ├── util.py           # Translation background job
    ├── static/
    └── templates/        # index, login, register, history, settings
```

## Prerequisites

- Python 3.11+
- PostgreSQL
- At least one provider API key (see below), unless every user supplies their own

## Setup

### Environment Variables

Copy `.env.example` to `.env` in the project root:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/translation_service
SECRET_KEY=replace-with-a-long-random-string
FERNET_KEY=   # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Server-default provider keys (used when the user has no personal key)
OPENAI_API_KEY=
GROQ_API_KEY=
TOGETHER_API_KEY=
OPENROUTER_API_KEY=
```

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | SQLAlchemy Postgres URI |
| `SECRET_KEY` | Signs the `session` cookie (default `change-me-in-production` if unset) |
| `FERNET_KEY` | Encrypts per-user API keys. If unset, a **new** key is generated each process start — stored keys become undecryptable after restart |
| `OPENAI_API_KEY` / `GROQ_API_KEY` / `TOGETHER_API_KEY` / `OPENROUTER_API_KEY` | Default keys for each provider |

### Local Development

```bash
git clone https://github.com/basit3000/Translation-Service.git
cd Translation-Service

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Ensure Postgres is running and DATABASE_URL is set
cd app
uvicorn main:app --reload
```

### Docker

```bash
# Requires a .env file (compose passes it via env_file)
docker compose up --build
docker compose down
```

App: `http://localhost:8000`. Compose overrides `DATABASE_URL` to the `db` service
(`postgresql://postgres:postgres@db:5432/translation_service`).

## Auth & accounts

| Method | Path | Notes |
|--------|------|-------|
| GET/POST | `/login` | Sets HttpOnly `session` cookie (7 days, `SameSite=Lax`) |
| GET/POST | `/register` | Username ≥ 3 chars, password ≥ 6; auto-login cookie |
| POST | `/logout` | Clears cookie; redirects to `/index` |
| GET | `/history` | Login required — user's past tasks |
| GET/POST | `/settings` | Login required — provider, model, optional personal API key |
| GET | `/api/models/{provider}` | Live model list for a provider (cached 5 minutes) |

Register / login JSON bodies: `{ "username", "password" }`.

## Providers

| Id | Default model | Env key |
|----|---------------|---------|
| `openai` | `gpt-4o-mini` | `OPENAI_API_KEY` |
| `groq` | `llama-3.3-70b-versatile` | `GROQ_API_KEY` |
| `together` | `meta-llama/Llama-3.3-70B-Instruct-Turbo` | `TOGETHER_API_KEY` |
| `openrouter` | `openai/gpt-4o-mini` | `OPENROUTER_API_KEY` |

Model lists are fetched from each provider's OpenAI-compatible `/v1/models`
endpoint and cached for **300 seconds**.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Redirects to `/index` |
| GET | `/index` | Web UI |
| POST | `/result` | Submit a translation request (optional session) |
| GET | `/result/{task_id}` | Task status and results |
| GET | `/result/content/{task_id}` | Full task record |

### Submit a Translation Request

```bash
curl -X POST http://localhost:8000/result \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "languages": ["German", "French", "Spanish"]}'
```

**Response:**
```json
{"task_id": 1}
```

If a valid session cookie is present, the task is linked to that user and uses
their LLM settings when configured.

### Check Task Status

```bash
curl http://localhost:8000/result/1
```

**Response:**
```json
{
  "task_id": 1,
  "status": "Completed",
  "results": {
    "German": "Hallo, Welt!",
    "French": "Bonjour, le monde!",
    "Spanish": "¡Hola, mundo!"
  }
}
```

## API Documentation

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Activate the venv and `pip install -r requirements.txt` |
| DB connection errors | Check Postgres and `DATABASE_URL` (use `db` host only inside Compose) |
| Auth / settings lost after restart | Set stable `SECRET_KEY` and `FERNET_KEY` in `.env` |
| Translation fails / invalid key | Configure a server env key or a personal key under `/settings` |
| Empty model dropdown | Provider key missing or `/v1/models` failed; check key and network |
| `RateLimitError` | Provider quota exceeded — wait or switch provider/model |

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.
