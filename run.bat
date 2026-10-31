@echo off
cd /d "%~dp0"
set PY=
where python >nul 2>nul && set PY=python
if not defined PY where py >nul 2>nul && set PY=py
if not defined PY goto nopython

echo Step 1 of 3: creating Python environment...
if not exist .venv\Scripts\python.exe %PY% -m venv .venv
if errorlevel 1 goto fail

echo Installing packages. You will see download progress below. This can take 5-10 minutes the first time.
echo Do NOT click inside this window. If it looks frozen, press Enter once.
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto fail

echo Step 2 of 3: preparing data...
if not exist data\students.csv .venv\Scripts\python.exe generate_data.py
if errorlevel 1 goto fail

echo Step 3 of 3: starting the dashboard. Your browser will open. Close this window to stop it.
.venv\Scripts\python.exe -m streamlit run app.py
goto end

:nopython
echo Python is not installed. Install it from python.org and tick "Add Python to PATH", then run this file again.
pause
exit /b 1

:fail
echo Something failed. Copy the message above and send it to Claude.
pause
exit /b 1

:end
