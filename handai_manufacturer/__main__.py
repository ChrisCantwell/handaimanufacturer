from __future__ import annotations

import uvicorn

from handai_manufacturer.config import load_config
from handai_manufacturer.logging_setup import configure_logging


def main() -> None:
    config = load_config()
    configure_logging(config)
    uvicorn.run(
        "handai_manufacturer.app:create_app",
        host=config.server.host,
        port=config.server.port,
        factory=True,
        reload=config.server.debug,
    )


if __name__ == "__main__":
    main()
