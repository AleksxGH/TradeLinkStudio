import os
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtGui import QFontDatabase
from app.services.resource_utils import resource_path

def load_fonts():
    """Load Open Sans fonts from resources/Open_Sans directory"""
    font_dir = resource_path("resources", "Open_Sans", "static")
    
    if not os.path.exists(font_dir):
        print(f"Font directory not found: {font_dir}")
        return False
    
    try:
        font_files = [f for f in os.listdir(font_dir) if f.endswith('.ttf')]
        for font_file in font_files:
            font_path = os.path.join(font_dir, font_file)
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id == -1:
                print(f"Failed to load font: {font_file}")
            else:
                families = QFontDatabase.applicationFontFamilies(font_id)
        return True
    except Exception as e:
        print(f"Error loading fonts: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_styles(app, style_path="style/style.qss"):
    if not style_path:
        return False

    resolved_style_path = style_path
    if not resolved_style_path.endswith(".qss"):
        resolved_style_path = f"{resolved_style_path}.qss"

    if "/" in resolved_style_path or "\\" in resolved_style_path:
        style_path = resource_path(*resolved_style_path.replace("\\", "/").split("/"))
    else:
        style_path = resource_path("style", resolved_style_path)

    if not os.path.exists(style_path):
        return False

    try:
        file = QFile(style_path)

        if not file.open(QFile.ReadOnly | QFile.Text):
            print(f"Не удалось открыть файл {style_path}")
            return False

        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()

        app.setStyleSheet(stylesheet)
        return True

    except Exception as e:
        print(f"Ошибка при загрузке стилей: {e}")
        import traceback
        traceback.print_exc()
        return False