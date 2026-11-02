@echo off
start "FastAPI" cmd /k "cd /d "%~dp0.." && rag_env\Scripts\activate && python -m uvicorn backend.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul
start "Streamlit" cmd /k "cd /d "%~dp0.." && rag_env\Scripts\activate && streamlit run frontend/app.py"
