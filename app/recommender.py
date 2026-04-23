from typing import Any

from app.spotify_client import SpotifyClient
from app.storage import LikedSongsStorage


class Recommender:
    """Handle recommendation flows by genre."""

    def __init__(self, spotify_client: SpotifyClient, storage: LikedSongsStorage) -> None:
        self.spotify_client = spotify_client
        self.storage = storage

    def get_suggested_genres(self, limit: int = 12) -> list[str]:
        genres = self.spotify_client.get_available_genre_seeds()
        return genres[:limit]

    def recommend_by_genre(self, genre: str, limit: int = 5) -> list[dict[str, Any]]:
        available_genres = self.spotify_client.get_available_genre_seeds()
        if genre in available_genres:
            tracks = self.spotify_client.get_recommendations_by_genre(genre, limit=limit)
            return self._deduplicate_tracks(tracks)

        artists = self.spotify_client.search_artists_by_genre(genre, limit=3)
        tracks: list[dict[str, Any]] = []
        for artist in artists:
            tracks.extend(self.spotify_client.get_artist_top_tracks(artist["id"]))
            if len(tracks) >= limit * 2:
                break
        return self._deduplicate_tracks(tracks)[:limit]

    def save_liked_song(self, track: dict[str, Any], genre_queried: str) -> bool:
        artists = ", ".join(item.get("name", "") for item in track.get("artists", []))
        song = {
            "title": track.get("name", ""),
            "artist": artists,
            "spotify_uri": track.get("uri", ""),
            "spotify_url": track.get("external_urls", {}).get("spotify", ""),
            "genre_queried": genre_queried,
        }
        return self.storage.add_song(song)

    @staticmethod
    def _deduplicate_tracks(tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
        seen: set[str] = set()
        unique_tracks: list[dict[str, Any]] = []
        for track in tracks:
            uri = track.get("uri")
            if not uri or uri in seen:
                continue
            seen.add(uri)
            unique_tracks.append(track)
        return unique_tracks
