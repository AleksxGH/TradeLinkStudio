import sys
import atexit
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QIcon
from app.ui.home_window import HomeWindow
from style.style_manager import load_styles, load_fonts
from app.services.resource_utils import icon_path
from app.services.logging_service import init_logging, log_error, log_debug, cleanup


def _excepthook(type_, value, tb):
    # Log unhandled exceptions and show a message box if app exists
    try:
        err = ''.join(traceback.format_exception(type_, value, tb))
        log_error(f"Unhandled exception:\n{err}")
        # If a QApplication exists, show a message box
        try:
            if QApplication.instance() is not None:
                QMessageBox.critical(None, "Unhandled Error", str(value))
        except Exception:
            pass
    except Exception:
        pass


def main():
    # Initialize logging (log file placed in ProgramData/TradeLink Studio/UserData)
    init_logging()
    log_debug("Application starting")

    # Ensure cleanup on normal exit
    atexit.register(cleanup)

    # Make sure uncaught exceptions are logged
    sys.excepthook = _excepthook

    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(icon_path("app.ico")))
    load_fonts()  # Load custom fonts first
    load_styles(app, "style/style.qss")

    try:
        window = HomeWindow()
        window.show()
        result = app.exec_()
        log_debug("Application exiting normally")
        sys.exit(result)
    except Exception as e:
        log_error(f"Fatal error in main loop: {e}")
        try:
            QMessageBox.critical(None, "Fatal Error", str(e))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()