from app.cli import SpotifyCLI
from app.exceptions import ConfigurationError, SpotifyCLIError


def main() -> None:
    try:
        app = SpotifyCLI()
        app.run()
    except ConfigurationError as exc:
        print(f"Error de configuracion: {exc}")
    except SpotifyCLIError as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()
