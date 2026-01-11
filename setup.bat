@echo off
REM Setup script for BaserowScripts (Windows)
REM This creates a virtual environment and installs all dependencies

echo ==================================================
echo BaserowScripts Setup
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo.
for /f "tokens=*" %%i in ('python --version') do echo - %%i found

REM Create virtual environment if it doesn't exist
if not exist "venv\" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    echo - Virtual environment created
) else (
    echo - Virtual environment already exists
)

REM Activate virtual environment and install dependencies
echo.
echo Installing dependencies...
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip setuptools wheel -q

REM Install required packages
pip install -r requirements.txt

echo.
echo - All dependencies installed
echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Activate the virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo 2. Copy and configure your environment file:
echo    copy .env.example .env
echo    REM Edit .env with your Baserow credentials
echo.
echo 3. Run the scripts:
echo    python update_contacts.py --excel-file your_file.xlsx --dry-run
echo    python deduplicate_table.py --identifying-field Email --dry-run
echo.
pause
