import logging

import structlog


def configure_logger(level: int, serialize: bool):
    if serialize:
        timestamp = structlog.processors.TimeStamper("iso")
    else:
        timestamp = structlog.processors.TimeStamper("%Y-%m-%d %H:%M:%S")

    processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        timestamp,
        structlog.stdlib.add_logger_name,
        structlog.processors.add_log_level,
    ]

    if serialize:
        processors.append(structlog.processors.format_exc_info)
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=[
            *processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    for name in ["uvicorn", "uvicorn.error", "uvicorn.asgi"]:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    logger = logging.getLogger("uvicorn.access")
    logger.handlers.clear()
    logger.propagate = False


logger = structlog.stdlib.get_logger()
