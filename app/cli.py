from typing import Any, Callable

from app.config import load_config
from app.advanced_tools import AdvancedTools
from app.exceptions import (
    AuthenticationError,
    ConfigurationError,
    OperationCancelled,
    PlaylistFileError,
    SpotifyAPIError,
    StorageError,
)
from app.exporter import PlaylistExporter
from app.html_report import HTMLReportBuilder
from app.playlist_manager import PlaylistManager
from app.recommender import Recommender
from app.spotify_client import SpotifyClient
from app.stats import StatsService
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
    print_session_badge,
    print_subtle,
    print_title,
    prompt_continue,
    prompt_menu_choice,
    prompt_text,
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
        self.stats_service = StatsService(self.spotify_client, self.storage)
        self.report_builder = HTMLReportBuilder(self.config.exports_dir)
        self.advanced_tools = AdvancedTools(
            self.spotify_client,
            self.playlist_manager,
            self.exporter,
            self.storage,
        )

    def run(self) -> None:
        while True:
            try:
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
                    self._safe_execute(self._handle_stats_report)
                elif option == "5":
                    self._safe_execute(self._handle_clear_session)
                elif option == "6":
                    self._safe_execute(self._handle_advanced_tools)
                elif option == "7":
                    self._exit_application()
                    break
                else:
                    print_message("[!]", "Opcion invalida. Intenta nuevamente.")

                prompt_continue()
            except KeyboardInterrupt:
                self._exit_application()
                break

    def _print_main_menu(self) -> None:
        print_banner()
        print_title("Spotify CLI Playlist Manager")
        print_subtle("Gestiona recomendaciones, playlists y exportaciones desde tu terminal.")
        self._print_user_session()
        print_menu(
            [
                (1, "Recomendaciones por genero (deshabilitada)"),
                (2, "Crear playlist desde TXT"),
                (3, "Exportar playlist a TXT"),
                (4, "Ver estadisticas en HTML"),
                (5, "Cerrar sesion de Spotify"),
                (6, "Herramientas avanzadas"),
                (7, "Salir"),
            ]
        )
        print_footer()

    def _handle_recommendations(self) -> None:
        print_section("Recomendaciones por genero")
        print_bullet_panel(
            "No disponible temporalmente",
            [
                "Spotify cambio varios endpoints en Development Mode (Febrero 2026).",
                "Los endpoints de recomendaciones por genero no estan disponibles para esta app en su estado actual.",
                "El resto de funciones de playlists y estadisticas siguen operativas.",
            ],
            color="yellow",
        )
        print_subtle(
            "Para reactivar esta opcion, la app debe operar con acceso de quota extendida y endpoints compatibles."
        )

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
        print_numbered_items(
            "Como quieres buscar la playlist",
            [
                "Listar playlists exportables",
                "Introducir nombre",
            ],
        )
        choice = prompt_text("Selecciona una opcion")
        if choice == "1":
            matches = self.exporter.list_exportable_playlists()
            if not matches:
                print_message(
                    "[!]",
                    "No hay playlists exportables disponibles. En modo desarrollo, Spotify solo permite leer playlists propias o colaborativas.",
                )
                return
            selected = self._select_playlist(matches, "Selecciona una playlist para exportar")
        elif choice == "2":
            title = prompt_text("Titulo de la playlist a exportar")
            matches = self.exporter.find_playlists(title)
            if not matches:
                print_message(
                    "[!]",
                    "No se encontraron playlists exportables con ese titulo. En modo desarrollo, Spotify solo permite leer items de playlists propias o colaborativas.",
                )
                return
            selected = self._select_playlist(matches, "Selecciona una playlist")
        else:
            print_message("[!]", "Seleccion invalida.")
            return

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

    def _handle_stats_report(self) -> None:
        print_section("Estadisticas en HTML")
        missing_scopes = self.spotify_client.get_missing_scopes()
        if missing_scopes:
            print_bullet_panel(
                "Reautorizacion recomendada",
                [
                    "La sesion actual parece no incluir todos los permisos necesarios para estadisticas.",
                    f"Scopes pendientes: {', '.join(missing_scopes)}",
                    "Usa 'Cerrar sesion de Spotify' y vuelve a autorizar la app.",
                ],
                color="yellow",
            )
        snapshot = self.stats_service.build_snapshot()
        output_path = self.report_builder.build_and_open(snapshot)
        print_message("[OK]", "Informe HTML generado y abierto en el navegador.")
        print_key_value_list([("Archivo generado", str(output_path))])
        if snapshot.warnings:
            print_bullet_panel(
                "Secciones parciales",
                snapshot.warnings,
                color="yellow",
            )

    def _handle_advanced_tools(self) -> None:
        print_section("Herramientas avanzadas")
        print_numbered_items(
            "Selecciona una funcion",
            [
                "Smart Playlist Builder",
                "Sync TXT <-> Playlist",
                "Batch Export Pro",
                "Buscar favoritos locales",
                "Detectar duplicados locales",
                "Mantenimiento de playlist",
            ],
        )
        choice = prompt_text("Elige una opcion")
        if choice == "1":
            self._advanced_smart_playlist()
        elif choice == "2":
            self._advanced_sync_txt_playlist()
        elif choice == "3":
            self._advanced_batch_export()
        elif choice == "4":
            self._advanced_search_liked()
        elif choice == "5":
            self._advanced_find_duplicates()
        elif choice == "6":
            self._advanced_maintain_playlist()
        else:
            print_message("[!]", "Seleccion invalida.")

    def _advanced_smart_playlist(self) -> None:
        print_section("Smart Playlist Builder")
        name = prompt_text("Nombre de playlist")
        periods_raw = prompt_text("Periodos (short_term,medium_term,long_term)")
        periods = [item.strip() for item in periods_raw.split(",") if item.strip()]
        allowed_periods = {"short_term", "medium_term", "long_term"}
        invalid_periods = [item for item in periods if item not in allowed_periods]
        if not periods or invalid_periods:
            print_message(
                "[!]",
                "Periodos invalidos. Usa solo: short_term, medium_term, long_term.",
            )
            return
        include_recent = ask_yes_no("Incluir escuchas recientes")
        max_per_artist = self._prompt_positive_int("Maximo por artista")
        limit = self._prompt_positive_int("Cantidad maxima de canciones")
        excluded_raw = prompt_text("Artistas a excluir (coma, opcional)", allow_empty=True)
        excluded = [item.strip() for item in excluded_raw.split(",") if item.strip()]
        result = self.advanced_tools.build_smart_playlist(
            name,
            periods,
            include_recent,
            max_per_artist,
            limit,
            excluded,
        )
        print_message("[OK]", "Smart playlist creada.")
        print_key_value_list(
            [
                ("Playlist", result["playlist_name"]),
                ("Tracks agregadas", str(result["tracks_added"])),
            ]
        )

    def _advanced_sync_txt_playlist(self) -> None:
        print_section("Sync TXT <-> Playlist")
        txt_path = prompt_text("Ruta TXT")
        matches = self.exporter.list_exportable_playlists()
        selected = self._select_playlist(matches, "Selecciona playlist para sync")
        preview = self.advanced_tools.sync_txt_playlist(txt_path, selected, False)
        print_section("Preview de sincronizacion")
        print_key_value_list(
            [
                ("Faltantes en playlist", str(preview["missing_count"])),
                ("Sobrantes en playlist", str(preview["extra_count"])),
            ]
        )
        if preview["missing"]:
            print_bullet_panel("Faltantes", preview["missing"], color="yellow")
        if preview["extra"]:
            print_bullet_panel("Sobrantes", preview["extra"], color="yellow")
        if ask_yes_no("Aplicar sincronizacion exacta en Spotify"):
            result = self.advanced_tools.sync_txt_playlist(txt_path, selected, True)
            print_message("[OK]", "Sincronizacion aplicada correctamente.")
            print_key_value_list([("Cambios aplicados", "si" if result["applied"] else "no")])
        else:
            print_message("[i]", "Solo se mostro preview. No se aplicaron cambios.")

    def _advanced_batch_export(self) -> None:
        print_section("Batch Export Pro")
        mode = prompt_text("Modo (all/own/collab)").strip().lower()
        if mode not in {"all", "own", "collab"}:
            print_message("[!]", "Modo invalido. Usa all, own o collab.")
            return
        include_json = ask_yes_no("Incluir export JSON")
        outputs = self.advanced_tools.batch_export_playlists(mode=mode, include_json=include_json)
        print_message("[OK]", f"Archivos generados: {len(outputs)}")

    def _advanced_search_liked(self) -> None:
        query = prompt_text("Texto a buscar en favoritos locales")
        matches = self.advanced_tools.search_liked_songs(query)
        print_message("[i]", f"Resultados: {len(matches)}")
        preview = [f"{item.get('title', '')} - {item.get('artist', '')}" for item in matches[:15]]
        if preview:
            print_bullet_panel("Coincidencias", preview, color="green")

    def _advanced_find_duplicates(self) -> None:
        groups = self.advanced_tools.find_liked_duplicates()
        print_message("[i]", f"Grupos duplicados: {len(groups)}")
        preview = []
        for group in groups[:10]:
            head = group[0]
            preview.append(f"{head.get('title', '')} - {head.get('artist', '')} ({len(group)}x)")
        if preview:
            print_bullet_panel("Duplicados detectados", preview, color="yellow")

    def _advanced_maintain_playlist(self) -> None:
        print_section("Mantenimiento de playlist")
        matches = self.exporter.list_exportable_playlists()
        selected = self._select_playlist(matches, "Selecciona playlist")
        preview = self.advanced_tools.maintain_playlist(selected, False)
        print_section("Preview de mantenimiento")
        print_key_value_list(
            [
                ("Incidencias", str(preview["issues_count"])),
            ]
        )
        if preview["issues"]:
            issue_preview = [f"{item.get('name', '')}: {item.get('reason', '')}" for item in preview["issues"][:20]]
            print_bullet_panel("Incidencias", issue_preview, color="yellow")
        if ask_yes_no("Aplicar reemplazos/saneado"):
            result = self.advanced_tools.maintain_playlist(selected, True)
            print_message("[OK]", "Mantenimiento aplicado.")
            print_key_value_list([("Cambios aplicados", "si" if result["applied"] else "no")])
        else:
            print_message("[i]", "Solo se mostro preview. No se aplicaron cambios.")

    @staticmethod
    def _prompt_positive_int(label: str) -> int:
        while True:
            raw = prompt_text(label)
            if not raw.isdigit():
                print_message("[!]", "Debes introducir un numero entero positivo.")
                continue
            value = int(raw)
            if value <= 0:
                print_message("[!]", "El numero debe ser mayor que cero.")
                continue
            return value

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
        if (
            "spotify denego el acceso a playlists" not in message
            and "spotify denego el acceso a datos de estadisticas" not in message
            and "403 forbidden" not in message
        ):
            return

        tips = [
            "Usa la opcion 'Cerrar sesion de Spotify' del menu para borrar el token cacheado.",
            "Autoriza la app de nuevo cuando te lo pida.",
            "Revisa que tu cuenta tenga acceso a la app en Spotify for Developers.",
            "Confirma que el redirect URI del .env coincide exactamente con el del dashboard.",
        ]
        if "datos de estadisticas" in message:
            tips.insert(
                2,
                "Asegurate de conceder los permisos `user-top-read`, `user-read-recently-played` y `user-read-private`.",
            )

        print_bullet_panel(
            "Que probar ahora",
            tips,
            color="yellow",
        )

    def _print_user_session(self) -> None:
        user = self.spotify_client.get_current_user_if_authenticated()
        if not user:
            return
        display_name = user.get("display_name") or user.get("id") or "Usuario"
        user_id = user.get("id", "spotify")
        print_session_badge(display_name, user_id)

    def _select_playlist(self, playlists: list[dict[str, Any]], title: str) -> dict[str, Any]:
        if len(playlists) == 1:
            return playlists[0]

        playlist_items = []
        for playlist in playlists:
            owner = playlist.get("owner", {}).get("display_name", "Desconocido")
            playlist_items.append(f"{playlist.get('name', 'Sin nombre')} (owner: {owner})")

        print_numbered_items(title, playlist_items)
        choice = prompt_text("Selecciona el numero de la playlist")
        if not choice.isdigit() or not (1 <= int(choice) <= len(playlists)):
            raise OperationCancelled("Seleccion cancelada o invalida. Regresando al menu principal.")
        return playlists[int(choice) - 1]

    @staticmethod
    def _exit_application() -> None:
        print_message("[i]", "Hasta luego.")
        print_exit_screen()
