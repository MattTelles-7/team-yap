from __future__ import annotations

import uvicorn

from .config import load_settings
from .db import init_db


def main() -> None:
    settings = load_settings()
    init_db(settings)
    uvicorn.run(
        "team_yap.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    main()

