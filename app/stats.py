from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.spotify_client import SpotifyClient
from app.storage import LikedSongsStorage


TIME_RANGE_LABELS = {
    "short_term": "Ultimas 4 semanas",
    "medium_term": "Ultimos 6 meses",
    "long_term": "Ultimo ano",
}


@dataclass
class StatsSnapshot:
    profile: dict[str, Any]
    summary: dict[str, Any]
    top_tracks: dict[str, list[dict[str, Any]]]
    top_artists: dict[str, list[dict[str, Any]]]
    recent_tracks: list[dict[str, Any]]
    local_stats: dict[str, Any]
    warnings: list[str]
    generated_at: str


class StatsService:
    """Build a stats snapshot for the HTML report."""

    def __init__(self, spotify_client: SpotifyClient, storage: LikedSongsStorage) -> None:
        self.spotify_client = spotify_client
        self.storage = storage
        self._artist_details_cache: dict[str, dict[str, Any]] = {}

    def build_snapshot(self) -> StatsSnapshot:
        warnings: list[str] = []
        profile = self.spotify_client.get_current_user()
        playlists = self._safe_fetch(lambda: self.spotify_client.get_user_playlists(), warnings, [])

        top_tracks = {
            key: self._safe_fetch(
                lambda key=key: self._normalize_top_tracks(self.spotify_client.get_top_tracks(key, limit=10)),
                warnings,
                [],
                f"No se pudieron cargar las canciones top para {TIME_RANGE_LABELS[key]}",
            )
            for key in TIME_RANGE_LABELS
        }

        top_artists = {
            key: self._safe_fetch(
                lambda key=key: self._normalize_top_artists(self.spotify_client.get_top_artists(key, limit=10)),
                warnings,
                [],
                f"No se pudieron cargar los artistas top para {TIME_RANGE_LABELS[key]}",
            )
            for key in TIME_RANGE_LABELS
        }

        recent_tracks = self._safe_fetch(
            lambda: self._normalize_recent_tracks(self.spotify_client.get_recently_played(limit=15)),
            warnings,
            [],
            "No se pudo cargar la actividad reciente.",
        )

        local_stats = self._build_local_stats()
        summary = self._build_summary(playlists, top_tracks, recent_tracks, local_stats)

        return StatsSnapshot(
            profile=self._normalize_profile(profile),
            summary=summary,
            top_tracks=top_tracks,
            top_artists=top_artists,
            recent_tracks=recent_tracks,
            local_stats=local_stats,
            warnings=warnings,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )

    @staticmethod
    def _safe_fetch(fetcher, warnings: list[str], fallback, warning_message: str | None = None):
        try:
            return fetcher()
        except Exception as exc:  # noqa: BLE001
            detail = str(exc).strip()
            if warning_message and detail:
                warnings.append(f"{warning_message}: {detail}")
            else:
                warnings.append(warning_message or detail or "No se pudo cargar una seccion del informe.")
            return fallback

    def _build_summary(
        self,
        playlists: list[dict[str, Any]],
        top_tracks: dict[str, list[dict[str, Any]]],
        recent_tracks: list[dict[str, Any]],
        local_stats: dict[str, Any],
    ) -> dict[str, Any]:
        top_track_total = sum(len(items) for items in top_tracks.values())
        return {
            "playlist_count": len(playlists),
            "recent_count": len(recent_tracks),
            "top_track_count": top_track_total,
            "liked_local_count": local_stats["liked_count"],
        }

    def _build_local_stats(self) -> dict[str, Any]:
        songs = self.storage.list_songs()
        genre_counter = Counter(song.get("genre_queried", "") for song in songs if song.get("genre_queried"))
        recent_saved = list(reversed(songs[-5:]))
        return {
            "liked_count": len(songs),
            "recent_saved": recent_saved,
            "top_genres": genre_counter.most_common(5),
        }

    def _get_artist_genres(self, artist: dict[str, Any]) -> list[str]:
        genres = artist.get("genres", []) or []
        if genres:
            return genres

        artist_id = artist.get("id", "")
        if not artist_id:
            return []

        if artist_id not in self._artist_details_cache:
            try:
                self._artist_details_cache[artist_id] = self.spotify_client.get_artist(artist_id)
            except Exception:  # noqa: BLE001
                self._artist_details_cache[artist_id] = {}

        return self._artist_details_cache[artist_id].get("genres", []) or []

    @staticmethod
    def _normalize_profile(profile: dict[str, Any]) -> dict[str, Any]:
        images = profile.get("images", []) or []
        avatar = images[0].get("url", "") if images else ""
        return {
            "display_name": profile.get("display_name") or profile.get("id") or "Usuario de Spotify",
            "user_id": profile.get("id", "spotify"),
            "avatar_url": avatar,
            "profile_url": profile.get("external_urls", {}).get("spotify", ""),
            "product": profile.get("product", ""),
        }

    @staticmethod
    def _normalize_top_tracks(tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for index, track in enumerate(tracks, start=1):
            album = track.get("album", {})
            images = album.get("images", []) or []
            normalized.append(
                {
                    "rank": index,
                    "name": track.get("name", "Sin titulo"),
                    "artists": ", ".join(artist.get("name", "") for artist in track.get("artists", [])),
                    "album": album.get("name", "Album desconocido"),
                    "image_url": images[0].get("url", "") if images else "",
                    "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                }
            )
        return normalized

    def _normalize_top_artists(self, artists: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for index, artist in enumerate(artists, start=1):
            images = artist.get("images", []) or []
            genres = self._get_artist_genres(artist)
            normalized.append(
                {
                    "rank": index,
                    "name": artist.get("name", "Artista desconocido"),
                    "genres": ", ".join(genres[:3]) or "Genero no disponible en la API",
                    "image_url": images[0].get("url", "") if images else "",
                    "spotify_url": artist.get("external_urls", {}).get("spotify", ""),
                }
            )
        return normalized

    @staticmethod
    def _normalize_recent_tracks(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized = []
        for item in items:
            track = item.get("track") or {}
            album = track.get("album", {})
            images = album.get("images", []) or []
            normalized.append(
                {
                    "name": track.get("name", "Sin titulo"),
                    "artists": ", ".join(artist.get("name", "") for artist in track.get("artists", [])),
                    "played_at": item.get("played_at", ""),
                    "context_type": (item.get("context") or {}).get("type", ""),
                    "image_url": images[0].get("url", "") if images else "",
                    "spotify_url": track.get("external_urls", {}).get("spotify", ""),
                }
            )
        return normalized
