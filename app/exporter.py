from pathlib import Path
from typing import Any

from app.exceptions import PlaylistFileError
from app.spotify_client import SpotifyClient
from app.utils import sanitize_filename


class PlaylistExporter:
    """Export user playlists to TXT files."""

    def __init__(self, spotify_client: SpotifyClient, exports_dir: Path) -> None:
        self.spotify_client = spotify_client
        self.exports_dir = exports_dir

    def find_playlists(self, title: str) -> list[dict[str, Any]]:
        playlists = self.list_exportable_playlists()
        exact_matches: list[dict[str, Any]] = []
        partial_matches: list[dict[str, Any]] = []
        title_key = title.strip().lower()

        for playlist in playlists:
            playlist_name = playlist.get("name", "")
            playlist_key = playlist_name.lower()
            if playlist_key == title_key:
                exact_matches.append(playlist)
            elif title_key in playlist_key:
                partial_matches.append(playlist)

        return exact_matches or partial_matches

    def list_exportable_playlists(self) -> list[dict[str, Any]]:
        playlists = self.spotify_client.get_user_playlists()
        current_user = self.spotify_client.get_current_user()
        current_user_id = current_user.get("id", "")
        return [
            playlist
            for playlist in playlists
            if self._can_export_playlist(playlist, current_user_id)
        ]

    def export_playlist(self, playlist: dict[str, Any]) -> Path:
        tracks = self.spotify_client.get_playlist_tracks(playlist["id"])
        if not tracks:
            raise PlaylistFileError("La playlist no tiene canciones para exportar.")

        lines: list[str] = []
        index = 1
        for item in tracks:
            content_item = item.get("item") or item.get("track") or {}
            if not content_item or content_item.get("type") == "episode":
                continue
            title = content_item.get("name", "Cancion sin titulo")
            artist = ", ".join(artist.get("name", "") for artist in content_item.get("artists", []))
            lines.append(f"{index}. {title} - {artist}")
            index += 1

        if not lines:
            raise PlaylistFileError("No se pudieron leer canciones validas de la playlist.")

        filename = f"{sanitize_filename(playlist.get('name', 'playlist'))}.txt"
        output_path = self.exports_dir / filename
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    @staticmethod
    def _can_export_playlist(playlist: dict[str, Any], current_user_id: str) -> bool:
        owner_id = playlist.get("owner", {}).get("id", "")
        collaborative = bool(playlist.get("collaborative", False))
        return owner_id == current_user_id or collaborative
