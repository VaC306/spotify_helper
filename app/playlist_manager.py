from pathlib import Path
from typing import Any

from app.exceptions import PlaylistFileError
from app.spotify_client import SpotifyClient
from app.utils import parse_song_line


class PlaylistManager:
    """Create Spotify playlists from TXT files."""

    def __init__(self, spotify_client: SpotifyClient) -> None:
        self.spotify_client = spotify_client

    def create_playlist_from_txt(self, playlist_name: str, txt_path: str) -> dict[str, Any]:
        path = Path(txt_path).expanduser()
        if not path.exists() or not path.is_file():
            raise PlaylistFileError("El archivo indicado no existe.")

        try:
            lines = path.read_text(encoding="utf-8-sig").splitlines()
        except OSError as exc:
            raise PlaylistFileError("No se pudo leer el archivo TXT.") from exc

        raw_lines = [line for line in lines if line.strip()]
        if not raw_lines:
            raise PlaylistFileError("El archivo TXT esta vacio.")

        found_tracks: list[dict[str, Any]] = []
        not_found: list[str] = []
        invalid_lines: list[str] = []

        for line in raw_lines:
            try:
                title, artist = parse_song_line(line)
            except ValueError:
                invalid_lines.append(line)
                continue

            candidates = self.spotify_client.search_track(title, artist)
            best_match = self.spotify_client.choose_best_track_match(title, artist, candidates)
            if best_match is None:
                not_found.append(line)
                continue
            found_tracks.append(best_match)

        playlist = self.spotify_client.create_playlist(
            name=playlist_name,
            description="Playlist creada desde Spotify CLI Playlist Manager.",
        )

        track_uris = [track["uri"] for track in found_tracks if track.get("uri")]
        if track_uris:
            self.spotify_client.add_tracks_to_playlist(playlist["id"], track_uris)

        return {
            "playlist_name": playlist.get("name", playlist_name),
            "playlist_id": playlist.get("id", ""),
            "lines_read": len(raw_lines),
            "found_count": len(found_tracks),
            "not_found_count": len(not_found),
            "invalid_count": len(invalid_lines),
            "not_found": not_found,
            "invalid_lines": invalid_lines,
        }
