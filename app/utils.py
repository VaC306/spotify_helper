import re
import unicodedata
from pathlib import Path

from colorama import Fore, Style, init as colorama_init
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from app.exceptions import OperationCancelled


colorama_init(autoreset=True)
console = Console()


def _build_key_bindings() -> KeyBindings:
    bindings = KeyBindings()

    @bindings.add("escape")
    def _(event) -> None:
        raise OperationCancelled("Operacion cancelada. Regresando al menu principal.")

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
        answer = _prompt(f"[bold green]?[/bold green] {prompt} [dim](s/n, Esc cancela)[/dim]")
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
    logo = r"""
  _____             _   _  __       _____ _      _____
 / ____|           | | (_)/ _|     / ____| |    |_   _|
| (___  _ __   ___ | |_ _| |_ _   | |    | |      | |
 \___ \| '_ \ / _ \| __| |  _| | | | |    | |      | |
 ____) | |_) | (_) | |_| | | | |_| | |____| |____ _| |_
|_____/| .__/ \___/ \__|_|_|  \__, |\_____|______|_____|
       | |                     __/ |
       |_|                    |___/
        Playlist Manager for Spotify
"""
    print(Fore.GREEN + Style.BRIGHT + logo + Style.RESET_ALL)


def print_separator(char: str = "=", width: int = 58) -> None:
    """Print a horizontal separator."""
    console.print(f"[green4]{char * width}[/green4]")


def print_section(title: str) -> None:
    """Print a section heading."""
    console.print()
    console.print(
        Panel.fit(
            f"[bold green]{title}[/bold green]",
            border_style="green4",
            padding=(0, 2),
            box=box.ROUNDED,
        )
    )


def format_menu_option(number: int, label: str) -> str:
    """Return a formatted menu option string."""
    return f"[bold green][{number}][/bold green] {label}"


def print_message(prefix: str, message: str) -> None:
    """Print a simple prefixed message."""
    styles = {
        "[OK]": "bold green",
        "[!]": "bold red",
        "[i]": "bold cyan",
        "[x]": "bold yellow",
    }
    style = styles.get(prefix, "bold white")
    console.print(f"[{style}]{prefix}[/{style}] {message}")


def print_title(text: str) -> None:
    """Print the main title panel."""
    console.print(
        Panel.fit(
            Text(text, style="bold white"),
            border_style="green4",
            padding=(0, 4),
            box=box.ROUNDED,
        )
    )


def print_menu_option(number: int, label: str) -> None:
    """Print one menu option with rich styling."""
    console.print(format_menu_option(number, label))


def print_menu(options: list[tuple[int, str]]) -> None:
    """Render the main menu inside a subtle panel."""
    table = Table.grid(padding=(0, 2))
    table.expand = False
    for number, label in options:
        table.add_row(f"[bold green]{number}[/bold green]", f"[white]{label}[/white]")

    console.print(
        Panel(
            Align.left(table),
            border_style="green4",
            box=box.ROUNDED,
            padding=(0, 2),
            subtitle="[dim]Elige una opcion y pulsa Enter[/dim]",
            subtitle_align="right",
        )
    )


def print_subtle(text: str) -> None:
    """Print helper text with low visual weight."""
    console.print(f"[dim]{text}[/dim]")


def prompt_text(label: str, allow_empty: bool = False) -> str:
    """Prompt for text with a styled input and cancellation support."""
    while True:
        value = _prompt(f"[bold green]>[/bold green] {label} [dim](Esc cancela)[/dim]").strip()
        if value or allow_empty:
            return value
        print_message("[!]", "Este campo no puede estar vacio.")


def prompt_menu_choice(label: str) -> str:
    """Prompt for a menu choice with a styled input."""
    return _prompt(f"[bold green]>[/bold green] {label}").strip()


def print_footer() -> None:
    """Print a small visual footer below the main menu."""
    console.print()
    console.print(
        Align.center(
            "[dim]Spotify Web API  |  Favoritos locales JSON  |  Pulsa Esc para volver[/dim]"
        )
    )


def print_session_badge(display_name: str, user_id: str) -> None:
    """Print the current authenticated Spotify user."""
    console.print()
    console.print(
        Align.center(
            f"[green]Sesion activa:[/green] [bold white]{display_name}[/bold white] [dim]@{user_id}[/dim]"
        )
    )


def print_track_card(index: int, title: str, artist: str, genre: str) -> None:
    """Render a recommendation card."""
    body = Text()
    body.append(f"{index}. ", style="bold green")
    body.append(f"{title}\n", style="bold white")
    body.append("Artista: ", style="green")
    body.append(f"{artist}\n", style="white")
    body.append("Genero: ", style="green")
    body.append(genre, style="white")
    console.print(
        Panel(
            body,
            border_style="green4",
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_numbered_items(title: str, items: list[str]) -> None:
    """Render numbered items in a styled list."""
    print_section(title)
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold green")
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
            box=box.ROUNDED,
            padding=(0, 1),
        )
    )


def print_key_value_list(items: list[tuple[str, str]]) -> None:
    """Render a compact key/value summary block."""
    table = Table.grid(padding=(0, 1))
    table.add_column(style="green")
    table.add_column(style="white")
    for key, value in items:
        table.add_row(f"{key}:", value)
    console.print(table)


def print_exit_screen() -> None:
    """Render a styled goodbye message."""
    console.print()
    console.print(
        Panel.fit(
            "[bold green]Gracias por usar Spotify CLI[/bold green]\n[dim]Nos vemos en la siguiente playlist.[/dim]",
            border_style="green4",
            box=box.ROUNDED,
            padding=(1, 3),
        )
    )


def _prompt(message: str) -> str:
    """Read interactive input with Esc cancellation support."""
    plain_message = Text.from_markup(message).plain
    return PROMPT_SESSION.prompt(plain_message)
