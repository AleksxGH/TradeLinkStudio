@echo off
REM Активируем виртуальное окружение
call .venv\Scripts\activate

REM Удаляем старые сборки
rmdir /s /q dist
rmdir /s /q build

REM Создаём exe через PyInstaller
pyinstaller --onefile ^
            --windowed ^
            --icon=resources\icons\app.ico ^
            --add-data "resources;resources" ^
            main.py

pause
