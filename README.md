# Smart QA System

Smart QA System is a local document question-answering tool. You upload files or paste text, and the system indexes them. When you ask a question, it finds the most relevant text chunks and returns them as an answer.

No API keys required. No internet required. Works completely offline.

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Pydantic
- **Frontend**: Streamlit
- **Document parsing**: pypdf, python-docx
- **HTTP client**: HTTPX
- **Testing**: Pytest, FastAPI TestClient

## Features

- Upload and index `.txt`, `.md`, `.pdf`, `.docx` files
- Paste raw text directly in the UI without creating a file
- Ask questions against all indexed content
- Get answers with source document references and matching chunk excerpts
- Persist indexed content between sessions in `data/documents/index.json`
- REST API for integration with other tools

## Prerequisites

- Python 3.11 or higher
- pip
- A virtual environment is recommended

## Installation

```powershell
git clone https://github.com/neuralbroker/smart-qa-system.git
cd smart-qa-system
python -m venv venv
.\/venv/Scripts/Activate.ps1
pip install -r requirements.txt
```

## Usage

### Start the backend

```powershell
.\/venv/Scripts/python.exe -m uvicorn app.main:app --reload
```

Backend runs at: `http://127.0.0.1:8000`

API docs at: `http://127.0.0.1:8000/docs`

### Start the frontend

In a new terminal:

```powershell
.\/venv/Scripts/python.exe -m streamlit run frontend/streamlit_app.py
```

Frontend runs at: `http://127.0.0.1:8501`

### API examples

Ingest text:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/documents/ingest-text -ContentType application/json -Body @'
{
  \"source\": \"notes.txt\",
  \"text\": \"FastAPI is a Python web framework. Streamlit is useful for building internal tools quickly.\"
}'
'@
```

Ask a question:
```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/qa/ask -ContentType application/json -Body @'
{
  \"question\": \"What is FastAPI?\"
}'
'@
```

Example response:
```json
{
  \"question\": \"What is FastAPI?\",
  \"answer\": \"FastAPI is a Python web framework.\",
  \"sources\": [{ \"source\": \"notes.txt\", \"chunk_id\": \"notes.txt:0\", \"score\": 3.214 }],
  \"matches\": [{ \"source\": \"notes.txt\", \"score\": 3.214, \"text\": \"FastAPI is a Python web framework. Streamlit is useful for building internal tools quickly.\" }]
}
```

### Run tests

```powershell
.\/venv/Scripts/python.exe -m pytest tests/ -q
```

## Project Structure

```
smart-qa-system/
├── app/                  # Backend application code
│   ├── config.py         # Application settings
│   ├── document_processor.py  # File parsing and text extraction
│   ├── main.py           # FastAPI app and API routes
│   ├── rag_pipeline.py   # Retrieval and answer composition logic
│   └── vector_store.py   # Chunk storage and scoring
├── frontend/             # Streamlit UI
│   └── streamlit_app.py  # Frontend application
├── tests/                # Test suite
│   └── test_api.py       # API integration tests
├── data/                 # Runtime data (created on first run)
│   ├── documents/        # Indexed chunks (index.json)
│   └── uploads/          # Uploaded files
├── .env.example          # Environment variable template
├── requirements.txt      # Python dependencies
└── README.md
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Reserved for future LLM integration. Not used currently. | (empty) |
| `SMART_QA_API_URL` | Base URL for the backend API | `http://127.0.0.1:8000` |

To override defaults, copy `.env.example` to `.env` and set values there.

## Contributing

Contributions welcome. Open an issue or submit a pull request.

## License

MIT