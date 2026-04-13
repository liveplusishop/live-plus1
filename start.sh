#!/bin/bash
# Railway 啟動腳本
cd backend
export FLASK_ENV=production
python -m gunicorn app:app --host 0.0.0.0 --port $PORT
