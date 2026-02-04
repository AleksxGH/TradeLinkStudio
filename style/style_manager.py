import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt5.QtCore import QFile, QTextStream


def load_styles(app, style_path="style/style.qss"):
    """Загружает стили из указанного пути"""

    # Получаем абсолютный путь
    if not os.path.isabs(style_path):
        # Если путь относительный, делаем абсолютным относительно директории скрипта
        base_dir = os.path.dirname(os.path.abspath(__file__))
        style_path = os.path.join(base_dir, style_path)

    print(f"Ищу файл стилей: {style_path}")
    print(f"Существует ли файл: {os.path.exists(style_path)}")

    # Проверяем существование файла
    if not os.path.exists(style_path):
        print(f"Файл не найден!")
        print(f"   Проверьте что файл существует по пути: {style_path}")

        # Покажем содержимое папки
        style_dir = os.path.dirname(style_path)
        if os.path.exists(style_dir):
            print(f"Содержимое папки {style_dir}:")
            for item in os.listdir(style_dir):
                print(f"   - {item}")
        else:
            print(f"Папка {style_dir} не существует!")

        return False

    try:
        # Открываем и читаем файл
        file = QFile(style_path)

        if not file.open(QFile.ReadOnly | QFile.Text):
            print(f"Не удалось открыть файл {style_path}")
            return False

        # Читаем стили
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()

        # Применяем стили
        app.setStyleSheet(stylesheet)
        print(f"Стили загружены из {style_path}")
        return True

    except Exception as e:
        print(f"Ошибка при загрузке стилей: {e}")
        import traceback
        traceback.print_exc()
        return False