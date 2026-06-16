from __future__ import annotations

from pathlib import Path
from typing import Any

from app.exporter import PlaylistExporter
from app.playlist_manager import PlaylistManager
from app.spotify_client import SpotifyClient
from app.storage import LikedSongsStorage
from app.utils import normalize_text, parse_song_line, sanitize_filename


class AdvancedTools:
    def __init__(
        self,
        spotify_client: SpotifyClient,
        playlist_manager: PlaylistManager,
        exporter: PlaylistExporter,
        storage: LikedSongsStorage,
    ) -> None:
        self.spotify_client = spotify_client
        self.playlist_manager = playlist_manager
        self.exporter = exporter
        self.storage = storage

    def build_smart_playlist(
        self,
        name: str,
        periods: list[str],
        include_recent: bool,
        max_per_artist: int,
        limit: int,
        excluded_artists: list[str],
    ) -> dict[str, Any]:
        excluded = {normalize_text(item) for item in excluded_artists if item.strip()}
        candidates: list[dict[str, Any]] = []
        for period in periods:
            candidates.extend(self.spotify_client.get_top_tracks(period, limit=10))
        if include_recent:
            for item in self.spotify_client.get_recently_played(limit=20):
                track = item.get("track") or {}
                if track:
                    candidates.append(track)

        artist_counts: dict[str, int] = {}
        selected: list[dict[str, Any]] = []
        seen_uris: set[str] = set()
        for track in candidates:
            uri = (track.get("uri") or "").strip()
            if not uri or uri in seen_uris:
                continue
            artist_names = [artist.get("name", "") for artist in track.get("artists", [])]
            normalized_artists = [normalize_text(name) for name in artist_names]
            if any(item in excluded for item in normalized_artists):
                continue
            primary_artist = normalized_artists[0] if normalized_artists else ""
            if primary_artist and artist_counts.get(primary_artist, 0) >= max_per_artist:
                continue
            selected.append(track)
            seen_uris.add(uri)
            if primary_artist:
                artist_counts[primary_artist] = artist_counts.get(primary_artist, 0) + 1
            if len(selected) >= limit:
                break

        playlist = self.spotify_client.create_playlist(
            name=name,
            description="Playlist creada por Smart Playlist Builder.",
        )
        uris = [item.get("uri", "") for item in selected if item.get("uri")]
        if uris:
            self.spotify_client.add_tracks_to_playlist(playlist["id"], uris)
        return {
            "playlist_name": playlist.get("name", name),
            "playlist_id": playlist.get("id", ""),
            "playlist_url": playlist.get("external_urls", {}).get("spotify", ""),
            "tracks_added": len(uris),
        }

    def sync_txt_playlist(self, txt_path: str, playlist: dict[str, Any], apply_changes: bool) -> dict[str, Any]:
        path = Path(txt_path).expanduser()
        lines = [line for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        desired_pairs: list[tuple[str, str]] = []
        for line in lines:
            title, artist = parse_song_line(line)
            desired_pairs.append((title, artist))

        tracks = self.spotify_client.get_playlist_tracks(playlist["id"])
        current_pairs: list[tuple[str, str]] = []
        for item in tracks:
            content = item.get("item") or item.get("track") or {}
            if not content:
                continue
            title = content.get("name", "")
            artist = ", ".join(artist.get("name", "") for artist in content.get("artists", []))
            current_pairs.append((title, artist))

        current_keys = {f"{normalize_text(t)}::{normalize_text(a)}" for t, a in current_pairs}
        desired_keys = {f"{normalize_text(t)}::{normalize_text(a)}" for t, a in desired_pairs}
        missing = [f"{t} - {a}" for t, a in desired_pairs if f"{normalize_text(t)}::{normalize_text(a)}" not in current_keys]
        extra = [f"{t} - {a}" for t, a in current_pairs if f"{normalize_text(t)}::{normalize_text(a)}" not in desired_keys]

        applied = False
        if apply_changes:
            uris: list[str] = []
            for title, artist in desired_pairs:
                matches = self.spotify_client.search_track(title, artist)
                best = self.spotify_client.choose_best_track_match(title, artist, matches)
                if best and best.get("uri"):
                    uris.append(best["uri"])
            self.spotify_client.replace_playlist_items(playlist["id"], uris)
            applied = True

        return {
            "missing_count": len(missing),
            "extra_count": len(extra),
            "missing": missing[:20],
            "extra": extra[:20],
            "applied": applied,
        }

    def batch_export_playlists(self, mode: str = "all", include_json: bool = True) -> list[Path]:
        playlists = self.exporter.list_exportable_playlists()
        user_id = self.spotify_client.get_current_user().get("id", "")
        if mode == "own":
            playlists = [item for item in playlists if item.get("owner", {}).get("id", "") == user_id]
        elif mode == "collab":
            playlists = [item for item in playlists if item.get("collaborative")]

        outputs: list[Path] = []
        for playlist in playlists:
            outputs.append(self.exporter.export_playlist(playlist))
            if include_json:
                outputs.append(self._export_playlist_json(playlist))
        return outputs

    def _export_playlist_json(self, playlist: dict[str, Any]) -> Path:
        import json

        tracks = self.spotify_client.get_playlist_tracks(playlist["id"])
        items: list[dict[str, str]] = []
        for track in tracks:
            content = track.get("item") or track.get("track") or {}
            if not content or content.get("type") == "episode":
                continue
            items.append(
                {
                    "title": content.get("name", ""),
                    "artist": ", ".join(artist.get("name", "") for artist in content.get("artists", [])),
                    "spotify_url": content.get("external_urls", {}).get("spotify", ""),
                    "uri": content.get("uri", ""),
                }
            )
        path = self.exporter.exports_dir / f"{sanitize_filename(playlist.get('name', 'playlist'))}.json"
        path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def search_liked_songs(self, query: str) -> list[dict[str, Any]]:
        query_key = normalize_text(query)
        return [
            item
            for item in self.storage.list_songs()
            if query_key in normalize_text(item.get("title", ""))
            or query_key in normalize_text(item.get("artist", ""))
            or query_key in normalize_text(item.get("genre_queried", ""))
        ]

    def find_liked_duplicates(self) -> list[list[dict[str, Any]]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for item in self.storage.list_songs():
            key = f"{normalize_text(item.get('title', ''))}::{normalize_text(item.get('artist', ''))}"
            groups.setdefault(key, []).append(item)
        return [items for items in groups.values() if len(items) > 1]

    def maintain_playlist(self, playlist: dict[str, Any], apply_fixes: bool) -> dict[str, Any]:
        tracks = self.spotify_client.get_playlist_tracks(playlist["id"])
        issues: list[dict[str, Any]] = []
        uris: list[str] = []
        for item in tracks:
            content = item.get("item") or item.get("track") or {}
            if not content:
                continue
            if content.get("is_local"):
                issues.append({"name": content.get("name", ""), "reason": "local"})
                continue
            uri = content.get("uri", "")
            if uri:
                uris.append(uri)
                continue
            name = content.get("name", "")
            artist = ", ".join(artist.get("name", "") for artist in content.get("artists", []))
            candidate = self.spotify_client.choose_best_track_match(name, artist, self.spotify_client.search_track(name, artist))
            if candidate and candidate.get("uri"):
                uris.append(candidate["uri"])
                issues.append({"name": name, "reason": "reemplazada"})
            else:
                issues.append({"name": name, "reason": "sin reemplazo"})

        if apply_fixes:
            self.spotify_client.replace_playlist_items(playlist["id"], uris)
        return {"issues": issues, "issues_count": len(issues), "applied": apply_fixes}
