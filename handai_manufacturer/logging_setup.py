from __future__ import annotations

import logging
from pathlib import Path

from handai_manufacturer.config import Config


def configure_logging(config: Config) -> None:
    level = getattr(logging, config.app.log_level.upper(), logging.INFO)
    log_dir = config.data_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path(log_dir) / "handai-manufacturer.log", encoding="utf-8"),
        ],
    )
