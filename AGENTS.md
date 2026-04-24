# AGENTS.md

Guia para agentes que trabajen en este repositorio.

## Proyecto

- Nombre: `spotify_helper`
- Tipo: aplicacion CLI en Python para gestionar playlists de Spotify
- API externa: Spotify Web API oficial
- Objetivo funcional:
  - recomendar canciones por genero
  - crear playlists desde TXT
  - exportar playlists a TXT
- Restricciones:
  - sin GUI
  - sin base de datos
  - sin frameworks innecesarios
  - sin IA integrada en la app

## Stack real del repositorio

- Python 3
- `requests`
- `python-dotenv`
- `colorama`
- `rich`
- `prompt-toolkit`

## Estructura actual

```text
main.py
requirements.txt
README.md
.env.example
.gitignore
app/
  __init__.py
  cli.py
  config.py
  exceptions.py
  exporter.py
  playlist_manager.py
  recommender.py
  spotify_client.py
  storage.py
  utils.py
data/
  liked_songs.json
  exports/
```

## Comandos de trabajo

### Crear entorno e instalar dependencias

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Ejecutar la aplicacion

```bash
python main.py
```

### Verificacion rapida de sintaxis

```bash
python -m py_compile main.py app/*.py
```

### Tests / lint / formato

- No hay suite de tests automatizada todavia.
- No hay linter configurado todavia.
- No hay formateador configurado todavia.
- Si se anaden mas adelante, actualizar este archivo con comandos exactos.

### Ejecutar un solo test

- Actualmente no aplica porque el repo no tiene tests.
- Si se introduce `pytest`, usar:

```bash
pytest tests/test_archivo.py::test_nombre
```

## Flujo funcional importante

### Autenticacion Spotify

- La app usa Authorization Code Flow.
- Lee credenciales desde `.env`.
- Variables requeridas:
  - `SPOTIFY_CLIENT_ID`
  - `SPOTIFY_CLIENT_SECRET`
  - `SPOTIFY_REDIRECT_URI`
- Si el redirect URI es local, por ejemplo `http://127.0.0.1:8888/callback`, la app intenta capturar el callback automaticamente.
- Si la captura automatica falla, hay fallback manual pegando la URL final.

### CLI y UX

- La experiencia CLI usa `rich`, `colorama` y `prompt-toolkit`.
- `Esc` cancela el flujo actual y devuelve al menu principal.
- Mantener el tono de mensajes claro, breve y amigable.
- No degradar el estilo visual del menu principal ni de los paneles sin motivo.

### Persistencia local

- Los favoritos se guardan en `data/liked_songs.json`.
- Debe evitarse duplicados por `spotify_uri` o por `title + artist` normalizados.
- Las exportaciones van a `data/exports/`.

### Formato de canciones

Usar siempre:

```text
Titulo - Artista
```

## Reglas de codigo

### Estilo general

- Priorizar codigo simple, modular y legible.
- Preferir funciones pequenas y con una sola responsabilidad.
- Mantener nombres claros y consistentes.
- Evitar sobreingenieria.
- No introducir nuevas dependencias sin beneficio claro.

### Imports

- Ordenar imports en este orden:
  1. libreria estandar
  2. terceros
  3. modulos internos `app.*`
- Evitar imports no usados.
- Mantener imports explicitamente nombrados.

### Tipos

- Usar type hints en funciones nuevas y APIs publicas.
- Mantener consistencia con `list[str]`, `dict[str, Any]`, etc.
- Si una estructura crece demasiado, considerar `dataclass` o un modelo ligero, pero no introducir complejidad innecesaria.

### Nombres

- Clases: `PascalCase`
- Funciones y variables: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
- Modulos: `snake_case.py`

### Formato y estructura

- Seguir el estilo ya presente en el repo.
- Mantener docstrings breves donde aporten valor.
- No anadir comentarios obvios.
- No mezclar logica de Spotify, CLI y almacenamiento en el mismo modulo.

## Manejo de errores

- Usar excepciones propias de `app/exceptions.py` cuando tenga sentido.
- Mostrar mensajes amigables al usuario desde la capa CLI.
- No dejar tracebacks crudos para errores esperables.
- Validar entradas de usuario y archivos antes de operar.
- Mantener fallback razonables cuando Spotify falle o no devuelva resultados.

## Modulos y responsabilidades

- `main.py`: punto de entrada
- `app/cli.py`: menu, prompts, navegacion y mensajes
- `app/config.py`: carga de entorno y rutas
- `app/spotify_client.py`: autenticacion y wrapper de la API
- `app/recommender.py`: recomendaciones por genero
- `app/playlist_manager.py`: lectura de TXT y creacion de playlist
- `app/exporter.py`: busqueda y exportacion de playlists
- `app/storage.py`: JSON local para favoritos
- `app/utils.py`: utilidades de presentacion, prompts y helpers pequenos

## Cambios que deben preservarse

- Mantener el orden exacto del TXT al crear playlists.
- Mantener soporte de cancelacion con `Esc`.
- Mantener el estilo visual del CLI salvo mejora clara.
- Mantener soporte de callback automatico para autenticacion local.
- No trackear `.env` ni caches.

## Git y archivos sensibles

- No commitear `.env`.
- No commitear secretos, tokens ni credenciales.
- Respetar `.gitignore`.
- Si se toca autenticacion, revisar que no se persistan secretos indebidamente.

## Si vas a ampliar el proyecto

- Primero preservar la estructura modular actual.
- Segundo mantener compatibilidad con la UX de terminal existente.
- Tercero actualizar `README.md` y este `AGENTS.md` si cambian comandos, dependencias o flujos.
