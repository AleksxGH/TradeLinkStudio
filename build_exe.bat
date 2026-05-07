@echo off
REM Активируем виртуальное окружение
call .venv\Scripts\activate

REM Удаляем старые сборки
rmdir /s /q dist
rmdir /s /q build

REM Считываем версию из app\version.json и генерируем version file для PyInstaller
python - <<PY
import json, os
data = json.load(open('app/version.json', encoding='utf-8'))
v = data.get('version', '').strip()
if not os.path.exists('build'):
        os.makedirs('build')
exe_name = f"TradeLink Studio {v}" if v else 'TradeLink Studio'
vi = f'''# UTF-8
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1,0,0,0),
        prodvers=(1,0,0,0),
        mask=0x3f,
        flags=0x0,
        OS=0x4,
        fileType=0x1,
        subtype=0x0,
        date=(0,0)
        ),
    kids=[
        StringFileInfo([StringTable('040904b0',[
            StringPair('CompanyName','Alexander Mishchenko'),
            StringPair('FileDescription','TradeLink Studio'),
            StringPair('FileVersion','{v}'),
            StringPair('InternalName','{exe_name}'),
            StringPair('OriginalFilename','{exe_name}.exe'),
            StringPair('ProductName','TradeLink Studio'),
            StringPair('ProductVersion','{v}')
        ])]),
        VarFileInfo([VarPair('Translation', [1033, 1200])])
    ]
)
'''
open('build/version_file.txt','w',encoding='utf-8').write(vi)
open('build/exe_name.txt','w',encoding='utf-8').write(exe_name)
PY

set /p exe_name=<build\exe_name.txt

REM Создаём exe через PyInstaller с именем и metadata
pyinstaller --onefile --windowed --name "%exe_name%" --version-file build/version_file.txt --icon=resources\icons\app.ico ^
                        --add-data "resources;resources" ^
                        --add-data "style;style" ^
                        --add-data "app\version.json;app" ^
                        main.py

pause
