#!/bin/bash

# Kill existing
lsof -ti:8000 | xargs -r kill -9
lsof -ti:8501 | xargs -r kill -9

pip install -r requirements.txt

# Start backend and log output
nohup uvicorn app.main:app --reload --port 8000 > backend.log 2>&1 &

# Start UI and log output
#nohup streamlit run ui/app.py --server.port=8501 --server.enableCORS false > ui.log 2>&1 &

tail -f backend.log