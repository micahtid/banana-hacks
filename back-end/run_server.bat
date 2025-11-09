@echo off
REM Banana Coin Trading API Server Startup Script (Windows)

echo 🍌 Starting Banana Coin Trading API Server...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo Checking dependencies...
pip install -q -r ..\requirements.txt

REM Load environment variables (if .env exists)
if exist ".env" (
    for /f "tokens=*" %%a in (.env) do set %%a
)

REM Start the server
echo ✅ Starting FastAPI server on http://0.0.0.0:8000
echo 📊 View API docs at http://localhost:8000/docs
echo.

uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload

