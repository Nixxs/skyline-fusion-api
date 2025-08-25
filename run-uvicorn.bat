@echo off
setlocal
cd /d C:\apps\skyline-fusion-api

REM Ensure .env is loaded by your config module; if not, uncomment next line:
REM call .venv\Scripts\activate && python -c "import dotenv; dotenv.load_dotenv()"

call .venv\Scripts\activate

REM Workers: 2 is fine to start. Add --proxy-headers for IIS/ARR.
uvicorn api.main:app ^
  --host 127.0.0.1 ^
  --port 8000 ^
  --workers 2 ^
  --proxy-headers ^
  --timeout-keep-alive 30
