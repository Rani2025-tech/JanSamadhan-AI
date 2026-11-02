#!/bin/bash
# Single-service deployment: FastAPI (background) + Streamlit (foreground)
# FastAPI runs on port 8000 internally
# Streamlit runs on $PORT (assigned by Render) — this is the public port

echo "Starting FastAPI backend on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Wait for FastAPI to be ready before starting Streamlit
echo "Waiting for backend to start..."
sleep 5

echo "Starting Streamlit frontend on port $PORT..."
exec streamlit run frontend/app.py \
    --server.port $PORT \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false
