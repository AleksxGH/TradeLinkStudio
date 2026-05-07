import os
import threading
from datetime import datetime
from app.services.app_paths import AppPaths

_instance = None


class LoggingService:
    def __init__(self, base_dir=None):
        self._lock = threading.Lock()
        base = base_dir or AppPaths().base_dir
        user_dir = os.path.join(base, "UserData")
        try:
            os.makedirs(user_dir, exist_ok=True)
        except Exception:
            pass

        self.log_path = os.path.join(user_dir, "app_actions.log")
        self.flag_path = os.path.join(user_dir, "log_active.flag")
        self.legacy_log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_actions.log")
        self.legacy_flag_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "log_active.flag")

        # remove legacy files from app folder so logs live only in UserData
        for legacy_path in [self.legacy_log_path, self.legacy_flag_path]:
            if os.path.exists(legacy_path):
                try:
                    os.remove(legacy_path)
                except Exception:
                    pass

        # If active flag exists from previous run, previous run didn't clean up — remove old log
        try:
            if os.path.exists(self.flag_path) and os.path.exists(self.log_path):
                try:
                    os.remove(self.log_path)
                except Exception:
                    pass
            # also remove leftover legacy files in app folder and stale UserData files when needed
            if os.path.exists(self.legacy_log_path):
                try:
                    os.remove(self.legacy_log_path)
                except Exception:
                    pass
            if os.path.exists(self.legacy_flag_path):
                try:
                    os.remove(self.legacy_flag_path)
                except Exception:
                    pass
        except Exception:
            pass

        # open log file for append
        try:
            self._fh = open(self.log_path, "a", encoding="utf-8")
        except Exception:
            self._fh = None

        # mark active
        try:
            open(self.flag_path, "w", encoding="utf-8").close()
        except Exception:
            pass

    def _write(self, level, message):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{level}] {message} ({ts})\n"
        with self._lock:
            if self._fh:
                try:
                    self._fh.write(line)
                    self._fh.flush()
                except Exception:
                    pass

    def debug(self, message):
        self._write("DEBUG", message)

    def error(self, message):
        self._write("ERROR", message)

    def cleanup(self):
        # Close and remove flag and log on normal exit
        try:
            if self._fh:
                try:
                    self._fh.close()
                except Exception:
                    pass
            # remove log file and flag
            try:
                if os.path.exists(self.log_path):
                    os.remove(self.log_path)
            except Exception:
                pass
            try:
                if os.path.exists(self.flag_path):
                    os.remove(self.flag_path)
            except Exception:
                pass
        except Exception:
            pass


def init_logging(base_dir=None):
    global _instance
    try:
        _instance = LoggingService(base_dir)
        _instance.debug("Logging initialized")
    except Exception:
        _instance = None


def get_logger():
    return _instance


def log_debug(msg):
    logger = get_logger()
    if logger:
        logger.debug(msg)


def log_error(msg):
    logger = get_logger()
    if logger:
        logger.error(msg)


def cleanup():
    logger = get_logger()
    if logger:
        logger.cleanup()
