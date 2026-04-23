import json
from pathlib import Path
from typing import Any

from app.exceptions import StorageError
from app.utils import ensure_parent_dir, normalize_text


class LikedSongsStorage:
    """Simple JSON storage for liked songs."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        ensure_parent_dir(self.file_path)
        if not self.file_path.exists():
            self.file_path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict[str, Any]]:
        try:
            content = self.file_path.read_text(encoding="utf-8").strip() or "[]"
            data = json.loads(content)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(
                f"No se pudo leer el almacenamiento local: {self.file_path}"
            ) from exc

        if not isinstance(data, list):
            raise StorageError("El archivo de canciones guardadas tiene un formato invalido.")
        return data

    def _save(self, items: list[dict[str, Any]]) -> None:
        try:
            self.file_path.write_text(
                json.dumps(items, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise StorageError("No se pudo guardar el archivo de canciones gustadas.") from exc

    def add_song(self, song: dict[str, Any]) -> bool:
        """Add a song if it is not already stored."""
        items = self._load()

        song_uri = (song.get("spotify_uri") or "").strip()
        song_key = self._build_text_key(song.get("title", ""), song.get("artist", ""))

        for item in items:
            if song_uri and item.get("spotify_uri") == song_uri:
                return False
            existing_key = self._build_text_key(item.get("title", ""), item.get("artist", ""))
            if existing_key == song_key:
                return False

        items.append(song)
        self._save(items)
        return True

    @staticmethod
    def _build_text_key(title: str, artist: str) -> str:
        return f"{normalize_text(title)}::{normalize_text(artist)}"
