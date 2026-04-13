# ChatGPT Translation Service

A FastAPI web service that translates text into multiple languages using the OpenAI ChatGPT API. Translations are processed asynchronously via background tasks and stored in a PostgreSQL database.

## Features

- Submit text and receive translations in multiple languages
- Asynchronous processing with background tasks
- PostgreSQL storage for query tasks and results
- Simple web UI for submitting translation requests
- REST API with automatic OpenAPI docs

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL + SQLAlchemy
- **AI:** OpenAI ChatGPT API (gpt-4o-mini)
- **Server:** Uvicorn / Gunicorn
- **Frontend:** Bootstrap 5

## Project Structure

```
app/
+-- main.py        # FastAPI application and routes
+-- models.py      # SQLAlchemy database models
+-- schemas.py     # Pydantic request/response schemas
+-- crud.py        # Database CRUD operations
+-- database.py    # Database connection setup
+-- utily.py       # OpenAI translation logic
+-- templates/
    +-- index.html # Web UI
```

## Prerequisites

- Python 3.11+
- PostgreSQL
- OpenAI API key

## Setup

### Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/chatgpt_service
OPENAI_API_KEY=your-openai-api-key
```

### Local Development

```bash
# Clone the repository
git clone https://github.com/basit3000/ChatGPT-service.git
cd ChatGPT-service

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run the server
cd app
uvicorn main:app --reload
```

### Docker

```bash
# Start the application with PostgreSQL
docker compose up --build

# Stop
docker compose down
```

The app will be available at `http://localhost:8000`.

## API Endpoints

| Method | Path                      | Description                          |
|--------|---------------------------|--------------------------------------|
| GET    | `/index`                  | Web UI for submitting queries        |
| POST   | `/result`                 | Submit a translation request         |
| GET    | `/result/{task_id}`       | Check task status and results        |
| GET    | `/result/content/{task_id}` | Get full task record              |

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

FastAPI auto-generates interactive docs:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## Troubleshooting

- **ModuleNotFoundError** — Make sure all dependencies are installed by running `pip install -r requirements.txt` within the activated virtual environment.
- **InvalidRequestError** — Check your OpenAI API key and ensure you have the correct permissions.
- **RateLimitError** — You may have exceeded your API quota. Check your OpenAI account for usage details.
- **No module named 'openai'** — Verify that `openai` is in `requirements.txt` and installed: `pip install openai`.
- **Cannot import name 'RateLimitError' from 'openai'** — Ensure you are using a compatible version: `pip install --upgrade openai`.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request if you have suggestions or improvements.