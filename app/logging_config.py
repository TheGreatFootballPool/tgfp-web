# logging_config.py — minimal, Seq-only
import logging
import seqlog
from config import Config


class PingFilter(logging.Filter):
    """Drop noisy /ping access logs (uvicorn.access only)."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name == "uvicorn.access":
            try:
                return "/ping" not in record.getMessage()
            except (AttributeError, TypeError):
                return True
        return True


def init_logging() -> None:
    """Initialize logging to Seq. No stdout/GELF handlers."""
    config = Config.get_config()
    server_url = config.SEQ_SERVER_URL
    api_key = config.SEQ_API_KEY
    level = config.LOG_LEVEL

    if not server_url:
        # Fallback so the app still logs somewhere if Seq isn't configured.
        logging.basicConfig(level=level)
        return

    seqlog.log_to_seq(
        server_url=server_url,
        api_key=api_key,
        level=level,  # e.g., DEBUG/INFO/WARNING
        batch_size=10,
        auto_flush_timeout=10,  # seconds
        override_root_logger=True,  # replace root handlers with Seq
        support_extra_properties=True,  # allow logging(..., extra={...})
    )

    # Attach the /ping filter to all current root handlers (Seq handler included).
    root = logging.getLogger()
    for h in root.handlers:
        h.addFilter(PingFilter())
