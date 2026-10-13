@echo off
REM FieldLens startup: set the GEE Cloud project and run the backend.
set EE_PROJECT=seventh-acrobat-494312-s0
cd /d %~dp0
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
