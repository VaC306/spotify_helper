from typing import Callable

from app.config import load_config
from app.exceptions import (
    AuthenticationError,
    ConfigurationError,
    PlaylistFileError,
    SpotifyAPIError,
    StorageError,
)
from app.exporter import PlaylistExporter
from app.playlist_manager import PlaylistManager
from app.recommender import Recommender
from app.spotify_client import SpotifyClient
from app.storage import LikedSongsStorage
from app.utils import ask_yes_no, truncate_text


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
            option = input("Selecciona una opcion: ").strip()

            if option == "1":
                self._safe_execute(self._handle_recommendations)
            elif option == "2":
                self._safe_execute(self._handle_create_playlist)
            elif option == "3":
                self._safe_execute(self._handle_export_playlist)
            elif option == "4":
                print("Hasta luego.")
                break
            else:
                print("Opcion invalida. Intenta nuevamente.")

            input("\nPresiona Enter para volver al menu principal...")

    @staticmethod
    def _print_main_menu() -> None:
        print("\n=================================")
        print(" Spotify CLI Playlist Manager")
        print("=================================")
        print("1. Recomendar canciones por genero")
        print("2. Crear playlist desde TXT")
        print("3. Exportar playlist a TXT")
        print("4. Salir")

    def _handle_recommendations(self) -> None:
        suggested = self.recommender.get_suggested_genres()
        if suggested:
            print("\nGeneros sugeridos:")
            for index, genre in enumerate(suggested, start=1):
                print(f"{index}. {genre}")

        raw_choice = input("\nEscribe un genero o el numero de la lista sugerida: ").strip()
        genre = self._resolve_genre_choice(raw_choice, suggested)
        if not genre:
            print("No se pudo resolver el genero indicado.")
            return

        tracks = self.recommender.recommend_by_genre(genre)
        if not tracks:
            print(f"No se encontraron recomendaciones para el genero '{genre}'.")
            return

        print(f"\nRecomendaciones para el genero: {genre}\n")
        for index, track in enumerate(tracks, start=1):
            title = track.get("name", "Sin titulo")
            artists = ", ".join(artist.get("name", "") for artist in track.get("artists", []))
            print(f"{index}. {truncate_text(title)} - {truncate_text(artists)}")
            if ask_yes_no("Quieres guardar esta cancion en canciones que te gustan"):
                saved = self.recommender.save_liked_song(track, genre)
                if saved:
                    print("Cancion guardada correctamente.")
                else:
                    print("La cancion ya estaba guardada.")

    def _handle_create_playlist(self) -> None:
        playlist_name = input("\nNombre de la nueva playlist: ").strip()
        if not playlist_name:
            print("El nombre de la playlist no puede estar vacio.")
            return

        txt_path = input("Ruta del archivo TXT: ").strip()
        if not txt_path:
            print("La ruta del archivo no puede estar vacia.")
            return

        result = self.playlist_manager.create_playlist_from_txt(playlist_name, txt_path)
        print("\nPlaylist creada correctamente.")
        print(f"- Playlist: {result['playlist_name']}")
        print(f"- Lineas leidas: {result['lines_read']}")
        print(f"- Canciones encontradas: {result['found_count']}")
        print(f"- Canciones no encontradas: {result['not_found_count']}")
        print(f"- Lineas invalidas: {result['invalid_count']}")

        if result["not_found"]:
            print("\nNo se encontraron estas canciones:")
            for item in result["not_found"]:
                print(f"- {item}")

        if result["invalid_lines"]:
            print("\nEstas lineas no cumplen el formato esperado:")
            for item in result["invalid_lines"]:
                print(f"- {item}")

    def _handle_export_playlist(self) -> None:
        title = input("\nTitulo de la playlist a exportar: ").strip()
        if not title:
            print("El titulo no puede estar vacio.")
            return

        matches = self.exporter.find_playlists(title)
        if not matches:
            print("No se encontraron playlists con ese titulo.")
            return

        if len(matches) == 1:
            selected = matches[0]
        else:
            print("\nSe encontraron varias playlists:")
            for index, playlist in enumerate(matches, start=1):
                owner = playlist.get("owner", {}).get("display_name", "Desconocido")
                print(f"{index}. {playlist.get('name', 'Sin nombre')} (owner: {owner})")
            choice = input("Selecciona el numero de la playlist: ").strip()
            if not choice.isdigit() or not (1 <= int(choice) <= len(matches)):
                print("Seleccion invalida.")
                return
            selected = matches[int(choice) - 1]

        output_path = self.exporter.export_playlist(selected)
        print("\nPlaylist exportada correctamente.")
        print(f"Archivo generado: {output_path}")

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
            PlaylistFileError,
            StorageError,
        ) as exc:
            print(f"\nError: {exc}")
