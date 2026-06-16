import re
import unicodedata
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from app.exceptions import OperationCancelled


console = Console()
ESCAPE_SENTINEL = "__ESCAPE_CANCELLED__"
PRIMARY_COLOR = "spring_green3"
SECONDARY_COLOR = "cyan1"
SURFACE_COLOR = "green4"
MUTED_COLOR = "grey70"
SOURCE_STYLES = {
    "txt_import": ("TXT Import", "cyan1"),
    "smart_playlist": ("Smart Rules", "magenta"),
    "manual": ("Manual", "yellow"),
    "api_clone": ("API Clone", "blue"),
    "template_build": ("Template", "green_yellow"),
    "future_tool": ("Future Tool", "bright_black"),
}


def _build_key_bindings() -> KeyBindings:
    bindings = KeyBindings()

    @bindings.add("escape")
    def _(event) -> None:
        event.app.exit(result=ESCAPE_SENTINEL)

    return bindings


PROMPT_SESSION = PromptSession(key_bindings=_build_key_bindings())


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
        answer = _prompt(f"{prompt} [dim](s/n, Esc cancela)[/dim]\n[bold green]>[/bold green] ")
        answer = answer.strip().lower()
        if answer in {"s", "si", "y", "yes"}:
            return True
        if answer in {"n", "no"}:
            return False
        print_message("[!]", "Respuesta invalida. Escribe 's' o 'n', o pulsa Esc.")


def truncate_text(value: str, limit: int = 60) -> str:
    """Trim long text for CLI display."""
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def print_banner() -> None:
    """Display the CLI title banner."""
    logo = Text()
    logo.append("SPOTIFY", style=f"bold {PRIMARY_COLOR}")
    logo.append(" CLI", style="bold white")
    logo.append("\n")
    logo.append("Playlist Manager", style=f"bold {SECONDARY_COLOR}")
    logo.append("\n")
    logo.append("Crea, exporta y analiza playlists desde tu terminal", style=MUTED_COLOR)
    console.print(
        Panel(
            Align.center(logo),
            border_style=SURFACE_COLOR,
            box=box.DOUBLE,
            padding=(1, 4),
        )
    )


def print_separator(char: str = "=", width: int = 58) -> None:
    """Print a horizontal separator."""
    console.print(f"[{SURFACE_COLOR}]{char * width}[/{SURFACE_COLOR}]")


def print_section(title: str) -> None:
    """Print a section heading."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold {PRIMARY_COLOR}]{title}[/bold {PRIMARY_COLOR}]",
            border_style=SURFACE_COLOR,
            padding=(0, 3),
            box=box.HEAVY,
        )
    )


def format_menu_option(number: int, label: str) -> str:
    """Return a formatted menu option string."""
    return f"[bold {PRIMARY_COLOR}][{number}][/bold {PRIMARY_COLOR}] {label}"


def print_message(prefix: str, message: str) -> None:
    """Print a simple prefixed message."""
    styles = {
        "[OK]": f"bold {PRIMARY_COLOR}",
        "[!]": "bold red",
        "[i]": f"bold {SECONDARY_COLOR}",
        "[x]": "bold yellow",
    }
    style = styles.get(prefix, "bold white")
    console.print(f"[{style}]{prefix}[/{style}] {message}")


def print_title(text: str) -> None:
    """Print the main title panel."""
    console.print(
        Panel.fit(
            Text(text, style=f"bold {SECONDARY_COLOR}"),
            border_style=SURFACE_COLOR,
            padding=(0, 5),
            box=box.DOUBLE,
        )
    )


def print_menu_option(number: int, label: str) -> None:
    """Print one menu option with rich styling."""
    console.print(format_menu_option(number, label))


def print_menu(options: list[tuple[int, str]]) -> None:
    """Render the main menu inside a subtle panel."""
    table = Table.grid(padding=(0, 2))
    table.expand = True
    for number, label in options:
        table.add_row(f"[bold {PRIMARY_COLOR}]{number:>2}[/bold {PRIMARY_COLOR}]", f"[white]{label}[/white]")

    console.print(
        Panel(
            Align.left(table),
            title=f"[bold {SECONDARY_COLOR}]Menu principal[/bold {SECONDARY_COLOR}]",
            border_style=SURFACE_COLOR,
            box=box.HEAVY,
            padding=(0, 2),
            subtitle="[dim]Elige una opcion y pulsa Enter[/dim]",
            subtitle_align="right",
        )
    )


def print_subtle(text: str) -> None:
    """Print helper text with low visual weight."""
    console.print(f"[{MUTED_COLOR}]{text}[/{MUTED_COLOR}]")


def prompt_text(label: str, allow_empty: bool = False) -> str:
    """Prompt for text with a styled input and cancellation support."""
    while True:
        value = _prompt(f"{label} [dim](Esc cancela)[/dim]\n[bold {PRIMARY_COLOR}]>[/bold {PRIMARY_COLOR}] ").strip()
        if value or allow_empty:
            return value
        print_message("[!]", "Este campo no puede estar vacio.")


def prompt_menu_choice() -> str:
    """Prompt for a menu choice with a minimal styled input."""
    return _prompt(f"[bold {PRIMARY_COLOR}]>[/bold {PRIMARY_COLOR}] ", allow_cancel=False).strip()


def prompt_continue() -> None:
    """Wait for Enter or Esc to continue."""
    _prompt(
        f"[dim]Pulsa Enter para volver al menu principal[/dim]\n[bold {PRIMARY_COLOR}]>[/bold {PRIMARY_COLOR}] ",
        allow_cancel=False,
    )


def print_footer() -> None:
    """Print a small visual footer below the main menu."""
    console.print()
    console.print(Rule(style=SURFACE_COLOR))
    console.print(Align.center("[dim]Spotify Web API | Favoritos JSON | Historial local | Esc vuelve atras[/dim]"))


def print_session_badge(display_name: str, user_id: str) -> None:
    """Print the current authenticated Spotify user."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold {PRIMARY_COLOR}]Sesion activa[/bold {PRIMARY_COLOR}]  [bold white]{display_name}[/bold white]  [dim]@{user_id}[/dim]",
            border_style=SURFACE_COLOR,
            box=box.SQUARE,
            padding=(0, 2),
        )
    )


def print_track_card(index: int, title: str, artist: str, genre: str) -> None:
    """Render a recommendation card."""
    body = Text()
    body.append(f"{index}. ", style=f"bold {PRIMARY_COLOR}")
    body.append(f"{title}\n", style="bold white")
    body.append("Artista: ", style=PRIMARY_COLOR)
    body.append(f"{artist}\n", style="white")
    body.append("Genero: ", style=SECONDARY_COLOR)
    body.append(genre, style="white")
    console.print(
        Panel(
            body,
            border_style=SURFACE_COLOR,
            box=box.HEAVY,
            padding=(0, 1),
        )
    )


def print_numbered_items(title: str, items: list[str]) -> None:
    """Render numbered items in a styled list."""
    print_section(title)
    table = Table.grid(padding=(0, 2))
    table.add_column(style=f"bold {PRIMARY_COLOR}")
    table.add_column(style="white")
    for index, item in enumerate(items, start=1):
        table.add_row(f"{index}.", item)
    console.print(table)


def print_bullet_panel(title: str, items: list[str], color: str = "yellow") -> None:
    """Render a list of items inside a panel."""
    body = Text()
    for item in items:
        body.append("- ", style=f"bold {color}")
        body.append(f"{item}\n", style="white")
    console.print(
        Panel(
            body,
            title=f"[bold {color}]{title}[/bold {color}]",
            border_style=color,
            box=box.HEAVY,
            padding=(0, 1),
        )
    )


def print_key_value_list(items: list[tuple[str, str]]) -> None:
    """Render a compact key/value summary block."""
    table = Table.grid(padding=(0, 1))
    table.add_column(style=PRIMARY_COLOR)
    table.add_column(style="white")
    for key, value in items:
        table.add_row(f"{key}:", value)
    console.print(table)


def print_playlist_history(entries: list[dict[str, str]]) -> None:
    """Render local playlist creation history."""
    if not entries:
        print_message("[i]", "Todavia no hay playlists creadas registradas localmente.")
        return

    table = Table(
        box=box.HEAVY,
        border_style=SURFACE_COLOR,
        header_style=f"bold {SECONDARY_COLOR}",
        expand=True,
        pad_edge=False,
    )
    table.add_column("Fecha", style=MUTED_COLOR, width=19)
    table.add_column("Playlist", style="bold white")
    table.add_column("Origen", style=PRIMARY_COLOR, width=16)
    table.add_column("Tracks", justify="right", style=SECONDARY_COLOR, width=8)

    for entry in entries:
        created_at = truncate_text(entry.get("created_at", "-"), 19)
        name = truncate_text(entry.get("playlist_name", "Sin nombre"), 34)
        source_key = entry.get("source", "manual")
        source = _format_history_source(source_key)
        tracks = str(entry.get("tracks_added") or entry.get("found_count") or 0)
        table.add_row(
            created_at,
            name,
            source,
            tracks,
            style=_get_history_row_style(source_key),
        )

    console.print(
        Panel(
            table,
            title=f"[bold {SECONDARY_COLOR}]Historial de playlists creadas[/bold {SECONDARY_COLOR}]",
            border_style=SURFACE_COLOR,
            box=box.HEAVY,
            padding=(0, 1),
        )
    )


def _format_history_source(source: str) -> str:
    label, color = SOURCE_STYLES.get(source, (source.replace("_", " ").title() or "Manual", "yellow"))
    return f"[{color}][{label}][/{color}]"


def _get_history_row_style(source: str) -> str:
    _, color = SOURCE_STYLES.get(source, ("Manual", "yellow"))
    return color


def print_exit_screen() -> None:
    """Render a styled goodbye message."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold {PRIMARY_COLOR}]Gracias por usar Spotify CLI[/bold {PRIMARY_COLOR}]\n[dim]Nos vemos en la siguiente playlist.[/dim]",
            border_style=SURFACE_COLOR,
            box=box.DOUBLE,
            padding=(1, 3),
        )
    )


def _prompt(message: str, allow_cancel: bool = True) -> str:
    """Read interactive input with Esc cancellation support."""
    plain_message = Text.from_markup(message).plain
    result = PROMPT_SESSION.prompt(plain_message)
    if result == ESCAPE_SENTINEL:
        if allow_cancel:
            raise OperationCancelled("Operacion cancelada. Regresando al menu principal.")
        return ""
    return result
