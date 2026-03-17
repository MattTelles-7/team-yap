from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _parse_allowed_origins(raw: str | None) -> tuple[str, ...]:
    if not raw:
        return ()
    return tuple(origin.strip() for origin in raw.split(",") if origin.strip())


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    data_dir: Path
    database_path: Path
    log_level: str
    session_ttl_hours: int
    allowed_origins: tuple[str, ...]

    def ensure_paths(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


def load_settings() -> Settings:
    default_data_dir = Path.cwd() / "data"
    data_dir = Path(os.getenv("TEAM_YAP_DATA_DIR", str(default_data_dir))).expanduser()
    database_path = Path(
        os.getenv("TEAM_YAP_DATABASE_PATH", str(data_dir / "team-yap.db"))
    ).expanduser()

    return Settings(
        host=os.getenv("TEAM_YAP_HOST", "127.0.0.1"),
        port=int(os.getenv("TEAM_YAP_PORT", "8080")),
        data_dir=data_dir,
        database_path=database_path,
        log_level=os.getenv("TEAM_YAP_LOG_LEVEL", "INFO"),
        session_ttl_hours=int(os.getenv("TEAM_YAP_SESSION_TTL_HOURS", "720")),
        allowed_origins=_parse_allowed_origins(os.getenv("TEAM_YAP_ALLOWED_ORIGINS")),
    )

