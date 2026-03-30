# Smart QA System

Minimal document question-answering system with a FastAPI backend and a Streamlit frontend.

## Screenshots

### Main dashboard

![Smart QA System dashboard](assets/screenshots/dashboard-overview.png)

### Question input area

![Smart QA System question section](assets/screenshots/dashboard-qa.png)

## Run the backend

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Run the frontend

```powershell
.\venv\Scripts\python.exe -m streamlit run frontend/streamlit_app.py
```

## Run tests

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

## Supported document types

- `.txt`
- `.md`
- `.pdf`
- `.docx`

The app works offline with extractive answers. If you later want to layer in an LLM, keep `OPENAI_API_KEY` in `.env`.
