import re
import unicodedata
from pathlib import Path


def normalize_text(value: str) -> str:
    """Return a simplified string for comparisons."""
    normalized = unicodedata.normalize("NFKD", value or "")
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.lower().strip()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"[^a-z0-9 ]", "", normalized)
    return normalized


def parse_song_line(line: str) -> tuple[str, str]:
    """Parse a TXT line in the format 'Title - Artist'."""
    cleaned = line.strip()
    if not cleaned:
        raise ValueError("La linea esta vacia.")

    parts = cleaned.split(" - ", 1)
    if len(parts) != 2:
        raise ValueError("Formato invalido. Usa 'Titulo - Artista'.")

    title, artist = parts[0].strip(), parts[1].strip()
    if not title or not artist:
        raise ValueError("Titulo o artista vacio.")
    return title, artist


def sanitize_filename(value: str) -> str:
    """Create a safe filename from a playlist title."""
    base = normalize_text(value).replace(" ", "_")
    base = base.strip("_")
    return base or "playlist"


def ensure_parent_dir(file_path: Path) -> None:
    """Ensure the parent directory for a file exists."""
    file_path.parent.mkdir(parents=True, exist_ok=True)


def ask_yes_no(prompt: str) -> bool:
    """Prompt the user for a yes/no answer."""
    while True:
        answer = input(f"{prompt} (s/n): ").strip().lower()
        if answer in {"s", "si", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print("Respuesta invalida. Escribe 's' o 'n'.")


def truncate_text(value: str, limit: int = 60) -> str:
    """Trim long text for CLI display."""
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."
