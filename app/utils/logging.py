import os
import logging
import logging.config
from pathlib import Path

from app.common.const import get_settings

settings = get_settings()


def get_debug_mode():
    if os.getenv("API_ENV") != "production":
        return True
    return False


def get_logging_config_dict(
    logging_level: str,
    base_log_directory: str,
    console_logging_enabled: bool,
    file_logging_enabled: bool,
):
    MEGABYTES = 1024 * 1024

    handlers = {}
    textscope_logger_handlers = []
    prediction_logger_handlers = []
    feedback_logger_handlers = []
    if console_logging_enabled:
        handlers.update(
            {
                "console": {
                    "level": logging_level,
                    "formatter": "console",
                    "class": "rich.logging.RichHandler",
                    "rich_tracebacks": True,
                    "tracebacks_show_locals": True,
                    "show_path": get_debug_mode(),  # show log line # in debug mode
                }
            }
        )
        textscope_logger_handlers.append("console")
        prediction_logger_handlers.append("console")
        feedback_logger_handlers.append("console")
    if file_logging_enabled:
        handlers.update(
            {
                "local": {
                    "level": logging_level,
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": os.path.join(base_log_directory, "active.log"),
                    "maxBytes": 100 * MEGABYTES,
                    "backupCount": 2,
                },
                "prediction": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "filename": os.path.join(base_log_directory, "prediction.log"),
                    "maxBytes": 100 * MEGABYTES,
                    "backupCount": 10,
                },
                "feedback": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "filename": os.path.join(base_log_directory, "feedback.log"),
                    "maxBytes": 100 * MEGABYTES,
                    "backupCount": 10,
                },
            }
        )
        textscope_logger_handlers.append("local")
        prediction_logger_handlers.append("prediction")
        feedback_logger_handlers.append("feedback")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "console": {"format": "%(message)s", "datefmt": "[%X]"},
            "prediction": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(request_id)s %(request)s %(response)s",
            },
            "feedback": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(request_id)s %(data)s",
            },
        },
        "handlers": handlers,
        "loggers": {
            "textscope": {
                "handlers": textscope_logger_handlers,
                "level": logging_level,
                "propagate": False,
            },
            "textscope.prediction": {
                "handlers": prediction_logger_handlers,
                "level": "INFO",
                "propagate": False,
            },
            "textscope.feedback": {
                "handlers": feedback_logger_handlers,
                "level": "INFO",
                "propagate": False,
            },
        },
    }


def configure_logging(
    logging_level: str = logging.DEBUG if get_debug_mode() else logging.INFO,
    base_log_dir: str = settings.TEXTSCOPE_LOG_DIR_PATH,
    console_logging_enabled: bool = True,
    file_logging_enabled: bool = True,
    advanced_enabled: bool = False,
    advanced_config: dict = None,
):
    Path(base_log_dir).mkdir(parents=True, exist_ok=True)
    if advanced_enabled:
        logging.config.dictConfig(advanced_config)
        logging.getLogger("textscope").debug(
            "Configured logging with advanced configuration, config=%s", advanced_config
        )
    else:
        if get_debug_mode():
            # Override logging level in config when debug mode is on
            logging_level = logging.getLevelName(logging.DEBUG)

        logging_config = get_logging_config_dict(
            logging_level, base_log_dir, console_logging_enabled, file_logging_enabled
        )
        logging.config.dictConfig(logging_config)
        logging.getLogger("textscope").debug(
            "Configured logging with simple configuration, "
            "level=%s, directory=%s, console_enabled=%s, file_enabled=%s",
            logging_level,
            base_log_dir,
            console_logging_enabled,
            file_logging_enabled,
        )


configure_logging()

logger = logging.getLogger("textscope")
