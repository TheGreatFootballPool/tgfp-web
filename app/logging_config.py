# logging_config.py
import os


class PingFilter:
    @staticmethod
    def filter(record):
        return "/ping" not in record.getMessage()


log_level = os.getenv("LOG_LEVEL", "INFO")
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
    },
    "filters": {
        "no_ping": {
            "()": "logging_config.PingFilter",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "default",
            "level": log_level,
        },
    },
    "root": {
        "handlers": ["stdout"],
        "level": log_level,
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["stdout"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.error": {
            "handlers": ["stdout"],
            "level": log_level,
            "propagate": False,
        },
        "uvicorn.access": {
            "handlers": ["stdout"],
            "level": log_level,
            "propagate": False,
            "filters": ["no_ping"],
        },
        "alembic": {
            "handlers": ["stdout"],
            "level": log_level,
            "propagate": False,
        },
        "sqlalchemy": {
            "handlers": ["stdout"],
            "level": log_level,
            "propagate": False,
        },
    },
}
