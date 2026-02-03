@echo off
echo Installing Python dependencies from requirements.txt...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo.
echo All packages installed.
pause
