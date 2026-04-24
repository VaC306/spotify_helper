from typing import Callable

from app.config import load_config
from app.exceptions import (
    AuthenticationError,
    ConfigurationError,
    OperationCancelled,
    PlaylistFileError,
    SpotifyAPIError,
    StorageError,
)
from app.exporter import PlaylistExporter
from app.playlist_manager import PlaylistManager
from app.recommender import Recommender
from app.spotify_client import SpotifyClient
from app.storage import LikedSongsStorage
from app.utils import (
    ask_yes_no,
    print_banner,
    print_bullet_panel,
    print_exit_screen,
    print_footer,
    print_key_value_list,
    print_menu,
    print_message,
    print_numbered_items,
    print_section,
    print_separator,
    print_session_badge,
    print_subtle,
    print_track_card,
    print_title,
    prompt_continue,
    prompt_menu_choice,
    prompt_text,
    truncate_text,
)


class SpotifyCLI:
    """Interactive command-line interface for the app."""

    def __init__(self) -> None:
        self.config = load_config()
        self.spotify_client = SpotifyClient(self.config)
        self.storage = LikedSongsStorage(self.config.liked_songs_path)
        self.recommender = Recommender(self.spotify_client, self.storage)
        self.playlist_manager = PlaylistManager(self.spotify_client)
        self.exporter = PlaylistExporter(self.spotify_client, self.config.exports_dir)

    def run(self) -> None:
        while True:
            self._print_main_menu()
            option = prompt_menu_choice()

            if not option:
                continue

            if option == "1":
                self._safe_execute(self._handle_recommendations)
            elif option == "2":
                self._safe_execute(self._handle_create_playlist)
            elif option == "3":
                self._safe_execute(self._handle_export_playlist)
            elif option == "4":
                self._safe_execute(self._handle_clear_session)
            elif option == "5":
                print_message("[i]", "Hasta luego.")
                print_exit_screen()
                break
            else:
                print_message("[!]", "Opcion invalida. Intenta nuevamente.")

            prompt_continue()

    def _print_main_menu(self) -> None:
        print_banner()
        print_title("Spotify CLI Playlist Manager")
        print_subtle("Gestiona recomendaciones, playlists y exportaciones desde tu terminal.")
        self._print_user_session()
        print_menu(
            [
                (1, "Recomendar canciones por genero"),
                (2, "Crear playlist desde TXT"),
                (3, "Exportar playlist a TXT"),
                (4, "Cerrar sesion de Spotify"),
                (5, "Salir"),
            ]
        )
        print_footer()

    def _handle_recommendations(self) -> None:
        print_section("Recomendaciones por genero")
        suggested = self.recommender.get_suggested_genres()
        if suggested:
            print_numbered_items("Generos sugeridos por Spotify", suggested)

        raw_choice = prompt_text("Escribe un genero o el numero de la lista sugerida")
        genre = self._resolve_genre_choice(raw_choice, suggested)
        if not genre:
            print_message("[!]", "No se pudo resolver el genero indicado.")
            return

        tracks = self.recommender.recommend_by_genre(genre)
        if not tracks:
            print_message("[!]", f"No se encontraron recomendaciones para el genero '{genre}'.")
            return

        print_section(f"Recomendaciones para: {genre}")
        for index, track in enumerate(tracks, start=1):
            title = track.get("name", "Sin titulo")
            artists = ", ".join(artist.get("name", "") for artist in track.get("artists", []))
            print_track_card(index, truncate_text(title), truncate_text(artists), genre)
            if ask_yes_no("Quieres guardar esta cancion en canciones que te gustan"):
                saved = self.recommender.save_liked_song(track, genre)
                if saved:
                    print_message("[OK]", "Cancion guardada correctamente.")
                else:
                    print_message("[i]", "La cancion ya estaba guardada.")
            print_separator(".", 36)

    def _handle_create_playlist(self) -> None:
        print_section("Crear playlist desde TXT")
        playlist_name = prompt_text("Nombre de la nueva playlist")
        txt_path = prompt_text("Ruta del archivo TXT")

        result = self.playlist_manager.create_playlist_from_txt(playlist_name, txt_path)
        print_section("Resumen de creacion")
        print_message("[OK]", "Playlist creada correctamente.")
        print_key_value_list(
            [
                ("Playlist", str(result["playlist_name"])),
                ("Lineas leidas", str(result["lines_read"])),
                ("Canciones encontradas", str(result["found_count"])),
                ("Canciones no encontradas", str(result["not_found_count"])),
                ("Lineas invalidas", str(result["invalid_count"])),
            ]
        )

        if result["not_found"]:
            print_bullet_panel("Canciones no encontradas", result["not_found"], color="yellow")

        if result["invalid_lines"]:
            print_bullet_panel("Lineas con formato invalido", result["invalid_lines"], color="red")

    def _handle_export_playlist(self) -> None:
        print_section("Exportar playlist a TXT")
        title = prompt_text("Titulo de la playlist a exportar")

        matches = self.exporter.find_playlists(title)
        if not matches:
            print_message("[!]", "No se encontraron playlists con ese titulo.")
            return

        if len(matches) == 1:
            selected = matches[0]
        else:
            playlist_items = []
            for playlist in matches:
                owner = playlist.get("owner", {}).get("display_name", "Desconocido")
                playlist_items.append(f"{playlist.get('name', 'Sin nombre')} (owner: {owner})")
            print_numbered_items("Selecciona una playlist", playlist_items)
            choice = prompt_text("Selecciona el numero de la playlist")
            if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
                print_message("[!]", "Seleccion invalida.")
                return
            selected = matches[int(choice) - 1]

        output_path = self.exporter.export_playlist(selected)
        print_section("Exportacion completada")
        print_message("[OK]", "Playlist exportada correctamente.")
        print_key_value_list([("Archivo generado", str(output_path))])

    def _handle_clear_session(self) -> None:
        print_section("Cerrar sesion de Spotify")
        if not ask_yes_no("Quieres borrar la sesion local guardada"):
            print_message("[i]", "Se mantuvo la sesion actual.")
            return

        cleared = self.spotify_client.clear_cached_session()
        if cleared:
            print_message("[OK]", "Sesion local borrada. La proxima accion pedira autorizacion de nuevo.")
        else:
            print_message("[i]", "No habia una sesion local guardada.")

    @staticmethod
    def _resolve_genre_choice(choice: str, suggested: list[str]) -> str:
        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(suggested):
                return suggested[index - 1]
            return ""
        return choice.strip().lower()

    @staticmethod
    def _safe_execute(action: Callable[[], None]) -> None:
        try:
            action()
        except (
            ConfigurationError,
            AuthenticationError,
            SpotifyAPIError,
            OperationCancelled,
            PlaylistFileError,
            StorageError,
        ) as exc:
            if isinstance(exc, OperationCancelled):
                print_message("[x]", str(exc))
            else:
                print_section("Error")
                print_message("[!]", str(exc))
                SpotifyCLI._print_auth_guidance(exc)

    @staticmethod
    def _print_auth_guidance(exc: Exception) -> None:
        message = str(exc).lower()
        if "spotify denego el acceso a playlists" not in message and "403 forbidden" not in message:
            return

        print_bullet_panel(
            "Que probar ahora",
            [
                "Usa la opcion 'Cerrar sesion de Spotify' del menu para borrar el token cacheado.",
                "Autoriza la app de nuevo cuando te lo pida.",
                "Revisa que tu cuenta tenga acceso a la app en Spotify for Developers.",
                "Confirma que el redirect URI del .env coincide exactamente con el del dashboard.",
            ],
            color="yellow",
        )

    def _print_user_session(self) -> None:
        user = self.spotify_client.get_current_user_if_authenticated()
        if not user:
            return
        display_name = user.get("display_name") or user.get("id") or "Usuario"
        user_id = user.get("id", "spotify")
        print_session_badge(display_name, user_id)
