import uuid
import structlog
import logging
import logging.handlers
from pathlib import Path
from easyproxy.config import load_config


def setup_logging(config_override: dict | None = None) -> None:
    cfg = config_override or load_config()
    log_cfg = cfg["logging"]

    log_file = Path(log_cfg["file"])
    log_file.parent.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, log_cfg["level"].upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=[
            logging.StreamHandler(),
            logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,
                backupCount=5,
            ),
        ],
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name or __name__)


def bind_request_id(logger: structlog.stdlib.BoundLogger) -> structlog.stdlib.BoundLogger:
    return logger.bind(request_id=str(uuid.uuid4())[:8])
