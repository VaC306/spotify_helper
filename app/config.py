from dataclasses import dataclass
from pathlib import Path
from typing import Final

import os
from dotenv import load_dotenv

from app.exceptions import ConfigurationError


TOKEN_CACHE_FILE: Final[str] = "token_cache.json"


@dataclass(frozen=True)
class AppConfig:
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str
    base_dir: Path
    data_dir: Path
    exports_dir: Path
    liked_songs_path: Path
    token_cache_path: Path


def load_config() -> AppConfig:
    """Load environment configuration and local data paths."""
    base_dir = Path(__file__).resolve().parent.parent
    load_dotenv(base_dir / ".env")

    data_dir = base_dir / "data"
    exports_dir = data_dir / "exports"
    liked_songs_path = data_dir / "liked_songs.json"
    token_cache_path = data_dir / TOKEN_CACHE_FILE

    client_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "").strip()

    missing = []
    if not client_id:
        missing.append("SPOTIFY_CLIENT_ID")
    if not client_secret:
        missing.append("SPOTIFY_CLIENT_SECRET")
    if not redirect_uri:
        missing.append("SPOTIFY_REDIRECT_URI")

    if missing:
        joined = ", ".join(missing)
        raise ConfigurationError(
            "Faltan variables de entorno requeridas: "
            f"{joined}. Configura tu archivo .env antes de continuar."
        )

    data_dir.mkdir(parents=True, exist_ok=True)
    exports_dir.mkdir(parents=True, exist_ok=True)

    return AppConfig(
        spotify_client_id=client_id,
        spotify_client_secret=client_secret,
        spotify_redirect_uri=redirect_uri,
        base_dir=base_dir,
        data_dir=data_dir,
        exports_dir=exports_dir,
        liked_songs_path=liked_songs_path,
        token_cache_path=token_cache_path,
    )
