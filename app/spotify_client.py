import base64
import http.server
import json
import socketserver
import threading
import time
import webbrowser
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

import requests

from app.config import AppConfig
from app.exceptions import AuthenticationError, SpotifyAPIError
from app.utils import normalize_text


class SpotifyClient:
    """Small wrapper around the Spotify Web API."""

    API_BASE_URL = "https://api.spotify.com/v1"
    AUTH_URL = "https://accounts.spotify.com/authorize"
    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SCOPES = [
        "playlist-modify-public",
        "playlist-modify-private",
        "playlist-read-private",
        "playlist-read-collaborative",
    ]

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self._session = requests.Session()
        self._token_data: dict[str, Any] | None = self._load_token_cache()
        self._current_user: dict[str, Any] | None = None

    def get_available_genre_seeds(self) -> list[str]:
        data = self._request("GET", "/recommendations/available-genre-seeds")
        return data.get("genres", [])

    def get_recommendations_by_genre(self, genre: str, limit: int = 5) -> list[dict[str, Any]]:
        params = {"seed_genres": genre, "limit": limit}
        data = self._request("GET", "/recommendations", params=params)
        return data.get("tracks", [])

    def search_artists_by_genre(self, genre: str, limit: int = 5) -> list[dict[str, Any]]:
        params = {
            "q": f'genre:"{genre}"',
            "type": "artist",
            "limit": limit,
        }
        data = self._request("GET", "/search", params=params)
        return data.get("artists", {}).get("items", [])

    def get_artist_top_tracks(self, artist_id: str, market: str = "US") -> list[dict[str, Any]]:
        params = {"market": market}
        data = self._request("GET", f"/artists/{artist_id}/top-tracks", params=params)
        return data.get("tracks", [])

    def search_track(self, title: str, artist: str, limit: int = 5) -> list[dict[str, Any]]:
        query = f'track:"{title}" artist:"{artist}"'
        params = {"q": query, "type": "track", "limit": limit}
        data = self._request("GET", "/search", params=params)
        return data.get("tracks", {}).get("items", [])

    def get_current_user(self) -> dict[str, Any]:
        if self._current_user is None:
            self._current_user = self._request("GET", "/me")
        return self._current_user

    def get_current_user_if_authenticated(self) -> dict[str, Any] | None:
        """Return the current user only when a local session exists."""
        if self._current_user is not None:
            return self._current_user
        if not self._token_data:
            return None
        try:
            self._current_user = self._request("GET", "/me")
        except (AuthenticationError, SpotifyAPIError):
            return None
        return self._current_user

    def clear_cached_session(self) -> bool:
        """Remove the local token cache and in-memory session."""
        self._token_data = None
        self._current_user = None
        try:
            if self.config.token_cache_path.exists():
                self.config.token_cache_path.unlink()
                return True
        except OSError as exc:
            raise AuthenticationError("No se pudo borrar la sesion local de Spotify.") from exc
        return False

    def create_playlist(self, name: str, description: str = "") -> dict[str, Any]:
        user = self.get_current_user()
        payload = {"name": name, "description": description, "public": False}
        return self._request("POST", f"/users/{user['id']}/playlists", json_body=payload)

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: list[str]) -> None:
        for start in range(0, len(track_uris), 100):
            chunk = track_uris[start : start + 100]
            self._request("POST", f"/playlists/{playlist_id}/tracks", json_body={"uris": chunk})

    def get_user_playlists(self) -> list[dict[str, Any]]:
        playlists: list[dict[str, Any]] = []
        endpoint = "/me/playlists"
        params: dict[str, Any] | None = {"limit": 50}

        while endpoint:
            data = self._request("GET", endpoint, params=params)
            playlists.extend(data.get("items", []))
            next_url = data.get("next")
            if not next_url:
                break
            endpoint = next_url.replace(self.API_BASE_URL, "")
            params = None
        return playlists

    def get_playlist_tracks(self, playlist_id: str) -> list[dict[str, Any]]:
        tracks: list[dict[str, Any]] = []
        endpoint = f"/playlists/{playlist_id}/tracks"
        params: dict[str, Any] | None = {"limit": 100}

        while endpoint:
            data = self._request("GET", endpoint, params=params)
            tracks.extend(data.get("items", []))
            next_url = data.get("next")
            if not next_url:
                break
            endpoint = next_url.replace(self.API_BASE_URL, "")
            params = None
        return tracks

    def choose_best_track_match(
        self,
        title: str,
        artist: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        best_candidate = None
        best_score = -1
        title_key = normalize_text(title)
        artist_key = normalize_text(artist)

        for candidate in candidates:
            candidate_title = normalize_text(candidate.get("name", ""))
            candidate_artists = [normalize_text(item.get("name", "")) for item in candidate.get("artists", [])]

            score = 0
            if candidate_title == title_key:
                score += 3
            elif title_key in candidate_title or candidate_title in title_key:
                score += 1

            if artist_key in candidate_artists:
                score += 3
            elif any(artist_key in item or item in artist_key for item in candidate_artists):
                score += 1

            if score > best_score:
                best_score = score
                best_candidate = candidate

        return best_candidate

    def _request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        token = self._get_access_token()
        url = endpoint if endpoint.startswith("http") else f"{self.API_BASE_URL}{endpoint}"
        headers = {"Authorization": f"Bearer {token}"}

        response = self._perform_api_request(method, url, headers, params, json_body)

        if response.status_code == 401:
            self._refresh_access_token()
            headers["Authorization"] = f"Bearer {self._get_access_token()}"
            response = self._perform_api_request(method, url, headers, params, json_body)

        if response.status_code >= 400:
            self._raise_api_error(response, endpoint)

        if not response.text:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise SpotifyAPIError("Spotify devolvio una respuesta invalida.") from exc

    def _perform_api_request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        params: dict[str, Any] | None,
        json_body: dict[str, Any] | None,
    ) -> requests.Response:
        try:
            return self._session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise SpotifyAPIError("No se pudo conectar con Spotify.") from exc

    def _get_access_token(self) -> str:
        if self._token_data and not self._is_token_expired(self._token_data):
            return self._token_data["access_token"]

        if self._token_data and self._token_data.get("refresh_token"):
            self._refresh_access_token()
            return self._token_data["access_token"]

        self._authenticate_user()
        if not self._token_data:
            raise AuthenticationError("No se pudo completar la autenticacion con Spotify.")
        return self._token_data["access_token"]

    def _authenticate_user(self) -> None:
        auth_url = self._build_authorization_url()
        print("\nSe abrira el navegador para autorizar el acceso a Spotify.")
        print("Si no se abre automaticamente, copia esta URL en tu navegador:")
        print(auth_url)
        auto_code = self._wait_for_authorization_code(auth_url)
        if auto_code:
            code = auto_code
        else:
            webbrowser.open(auth_url)
            redirected_url = input("\nPega aqui la URL final despues de autorizar la aplicacion: ").strip()
            code = self._extract_authorization_code(redirected_url)
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.spotify_redirect_uri,
        }
        self._token_data = self._request_token(payload)
        self._save_token_cache(self._token_data)

    def _wait_for_authorization_code(self, auth_url: str) -> str | None:
        parsed_redirect = urlparse(self.config.spotify_redirect_uri)
        if parsed_redirect.scheme != "http":
            return None
        if parsed_redirect.hostname not in {"127.0.0.1", "localhost"}:
            return None
        if not parsed_redirect.port:
            return None

        code_container: dict[str, str] = {}
        error_container: dict[str, str] = {}
        completed = threading.Event()
        callback_path = parsed_redirect.path or "/"

        class SpotifyAuthHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # type: ignore[override]
                parsed_request = urlparse(self.path)
                if parsed_request.path != callback_path:
                    self.send_response(404)
                    self.end_headers()
                    return

                query = parse_qs(parsed_request.query)
                code = query.get("code", [""])[0]
                error = query.get("error", [""])[0]

                if code:
                    code_container["code"] = code
                    self._send_html_response(
                        200,
                        "Autorizacion completada. Ya puedes volver a la terminal.",
                    )
                else:
                    if error:
                        error_container["error"] = error
                    self._send_html_response(
                        400,
                        "No se pudo completar la autorizacion. Puedes cerrar esta ventana.",
                    )
                completed.set()

            def log_message(self, format: str, *args: object) -> None:
                return

            def _send_html_response(self, status_code: int, message: str) -> None:
                html = (
                    "<html><body style='font-family: Arial; padding: 24px;'>"
                    f"<h2>{message}</h2>"
                    "</body></html>"
                )
                encoded = html.encode("utf-8")
                self.send_response(status_code)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.end_headers()
                self.wfile.write(encoded)

        class ReusableTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        try:
            with ReusableTCPServer((parsed_redirect.hostname, parsed_redirect.port), SpotifyAuthHandler) as server:
                server.timeout = 0.5
                started_at = time.time()
                print(
                    f"\nEsperando autorizacion automatica en {self.config.spotify_redirect_uri}..."
                )
                webbrowser.open(auth_url)
                while not completed.is_set():
                    if time.time() - started_at > 120:
                        return None
                    server.handle_request()
        except OSError:
            return None

        if error_container.get("error"):
            raise AuthenticationError(
                f"Spotify devolvio un error de autorizacion: {error_container['error']}"
            )
        return code_container.get("code")

    def _refresh_access_token(self) -> None:
        if not self._token_data or not self._token_data.get("refresh_token"):
            raise AuthenticationError("No hay refresh token disponible. Vuelve a autenticarte.")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self._token_data["refresh_token"],
        }
        refreshed = self._request_token(payload)
        if not refreshed.get("refresh_token"):
            refreshed["refresh_token"] = self._token_data["refresh_token"]
        self._token_data = refreshed
        self._save_token_cache(self._token_data)

    def _request_token(self, payload: dict[str, Any]) -> dict[str, Any]:
        auth_header = self._build_basic_auth_header()
        try:
            response = self._session.post(
                self.TOKEN_URL,
                data=payload,
                headers={"Authorization": auth_header},
                timeout=30,
            )
        except requests.RequestException as exc:
            raise AuthenticationError("No se pudo conectar con Spotify para autenticar la sesion.") from exc

        if response.status_code >= 400:
            self._raise_auth_error(response)

        try:
            token_data = response.json()
        except ValueError as exc:
            raise AuthenticationError("No se pudo interpretar la respuesta de autenticacion.") from exc

        token_data["expires_at"] = int(time.time()) + int(token_data.get("expires_in", 3600)) - 60
        return token_data

    def _build_basic_auth_header(self) -> str:
        raw = f"{self.config.spotify_client_id}:{self.config.spotify_client_secret}".encode("utf-8")
        return f"Basic {base64.b64encode(raw).decode('utf-8')}"

    def _build_authorization_url(self) -> str:
        scopes = quote(" ".join(self.SCOPES))
        redirect_uri = quote(self.config.spotify_redirect_uri)
        return (
            f"{self.AUTH_URL}?client_id={self.config.spotify_client_id}"
            f"&response_type=code&redirect_uri={redirect_uri}&scope={scopes}"
        )

    @staticmethod
    def _extract_authorization_code(redirected_url: str) -> str:
        parsed = urlparse(redirected_url)
        query = parse_qs(parsed.query)
        if "error" in query:
            raise AuthenticationError(f"Spotify devolvio un error de autorizacion: {query['error'][0]}")
        code = query.get("code", [""])[0]
        if not code:
            raise AuthenticationError("No se encontro el parametro 'code' en la URL proporcionada.")
        return code

    @staticmethod
    def _is_token_expired(token_data: dict[str, Any]) -> bool:
        return int(token_data.get("expires_at", 0)) <= int(time.time())

    def _load_token_cache(self) -> dict[str, Any] | None:
        if not self.config.token_cache_path.exists():
            return None

        try:
            content = self.config.token_cache_path.read_text(encoding="utf-8")
            if not content.strip():
                return None
            return json.loads(content)
        except (OSError, ValueError):
            return None

    def _save_token_cache(self, token_data: dict[str, Any]) -> None:
        try:
            self.config.token_cache_path.write_text(
                json.dumps(token_data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            raise AuthenticationError("No se pudo guardar el token localmente.") from exc

    @staticmethod
    def _raise_api_error(response: requests.Response, endpoint: str) -> None:
        message = "Error al comunicarse con Spotify."
        try:
            data = response.json()
            error = data.get("error", {})
            if isinstance(error, dict):
                message = error.get("message", message)
            elif isinstance(error, str):
                message = error
        except ValueError:
            pass

        if response.status_code == 403:
            playlist_endpoint = endpoint.startswith("/me/playlists") or endpoint.startswith("/playlists/")
            if playlist_endpoint:
                message = (
                    f"{message}. Spotify denego el acceso a playlists. "
                    "Las causas mas comunes son: token antiguo sin scopes actualizados, "
                    "falta de permisos concedidos o que tu cuenta no este habilitada en "
                    "Spotify for Developers para esta app. Prueba a borrar `data/token_cache.json` "
                    "y autenticarte de nuevo."
                )
            else:
                message = (
                    f"{message}. Spotify devolvio 403 Forbidden. Revisa permisos concedidos, "
                    "credenciales y que la cuenta tenga acceso a esta app en Spotify for Developers."
                )
        raise SpotifyAPIError(message)

    @staticmethod
    def _raise_auth_error(response: requests.Response) -> None:
        message = "No se pudo autenticar con Spotify."
        try:
            data = response.json()
            message = data.get("error_description") or data.get("error") or message
        except ValueError:
            pass
        raise AuthenticationError(message)
