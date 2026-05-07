@echo off
setlocal

REM Активируем виртуальное окружение, если существует
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

REM Удаляем старые сборки
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

REM Считываем версию из app\version.json и генерируем metadata для PyInstaller
python generate_build_metadata.py
if errorlevel 1 goto :end

for /f "usebackq delims=" %%i in ("build\exe_name.txt") do set "exe_name=%%i"
if not defined exe_name set "exe_name=TradeLink Studio"

REM Создаём exe через PyInstaller с именем и metadata
pyinstaller --onefile --windowed --name "%exe_name%" --version-file build/version_file.txt --icon=resources\icons\app.ico ^
                        --add-data "resources;resources" ^
                        --add-data "style;style" ^
                        --add-data "app\version.json;app" ^
                        main.py

:end
pause
endlocal