# Spotify CLI Playlist Manager

Aplicacion CLI en Python para gestionar playlists de Spotify usando la Web API oficial.

## Funcionalidades

- Recomendaciones por genero (deshabilitada temporalmente en Development Mode por cambios de Spotify Web API en febrero 2026).
- Crear una playlist desde un archivo TXT.
- Exportar una playlist existente a un archivo TXT.
- Generar un informe HTML moderno con estadisticas de la cuenta.
- Herramientas avanzadas desde CLI para automatizar playlists, sincronizar, exportar en lote y mantenimiento.
- Historial local de playlists creadas desde la app.

## Herramientas avanzadas (menu opcion 6)

La app incluye un submenu de herramientas avanzadas:

- Smart Playlist Builder:
  - Crea una playlist desde reglas (`short_term`, `medium_term`, `long_term`).
  - Permite incluir recientes, limitar canciones por artista, excluir artistas y fijar un maximo total.
- Sync TXT <-> Playlist:
  - Compara un TXT contra una playlist y muestra un preview de faltantes/sobrantes.
  - Solo aplica cambios si confirmas la sincronizacion exacta.
- Batch Export Pro:
  - Exporta en lote playlists `all`, `own` o `collab`.
  - Puede generar TXT y JSON estructurado.
- Buscar favoritos locales:
  - Busca en `data/liked_songs.json` por titulo, artista o genero consultado.
- Detectar duplicados locales:
  - Encuentra grupos duplicados por `title + artist` normalizados.
- Mantenimiento de playlist:
  - Muestra preview de incidencias (locales/sin reemplazo).
  - Aplica saneado solo si confirmas.
- Historial de playlists creadas:
  - Muestra las ultimas playlists creadas desde import TXT o Smart Playlist Builder.
  - Se guarda localmente en `data/playlist_history.json`.

### Validaciones incluidas

- Validacion de numeros positivos para limites y maximos.
- Validacion de periodos permitidos (`short_term`, `medium_term`, `long_term`).
- Validacion de modo de exportacion (`all`, `own`, `collab`).
- Flujos con preview antes de aplicar cambios en operaciones sensibles.

## Estado de la opcion de recomendaciones por genero

- La opcion existe en el menu pero esta deshabilitada y muestra un aviso informativo.
- Motivo: en Development Mode, Spotify cambio disponibilidad de endpoints usados por esta funcion (`/recommendations` y `/recommendations/available-genre-seeds`).
- Las funciones de crear/exportar playlists y estadisticas HTML siguen funcionando.

## Requisitos

- Python 3.10 o superior
- Una app registrada en Spotify for Developers

## Instalacion

1. Crea y activa un entorno virtual si lo deseas.
2. Instala dependencias:

```bash
pip install -r requirements.txt
```

## Configuracion

1. Copia `.env.example` a `.env`.
2. Completa estas variables:

```env
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback
```

3. En Spotify for Developers agrega la misma `SPOTIFY_REDIRECT_URI` a la configuracion de tu aplicacion.

## Ejecucion

```bash
python main.py
```

La primera vez que una accion necesite acceder a Spotify, la app abrira el navegador para autorizar la cuenta.
Si usas un `SPOTIFY_REDIRECT_URI` local como `http://127.0.0.1:8888/callback`, la app intentara capturar el callback automaticamente.
Si no puede hacerlo, usara el modo manual y te pedira pegar la URL final redirigida en la terminal.

La app solicita permisos para:

- leer playlists
- crear playlists
- leer top tracks y top artists
- leer reproducciones recientes

## Formato del TXT para crear playlists

Una cancion por linea con este formato:

```text
Bohemian Rhapsody - Queen
Viva La Vida - Coldplay
HUMBLE. - Kendrick Lamar
```

## Exportacion

- Los archivos exportados se guardan en `data/exports/`.
- El formato generado es:

```text
1. Bohemian Rhapsody - Queen
2. Viva La Vida - Coldplay
3. HUMBLE. - Kendrick Lamar
```

## Informe HTML de estadisticas

- La opcion de estadisticas genera un archivo HTML en `data/exports/`.
- Lo abre automaticamente en el navegador por defecto.
- Incluye top tracks, top artists, actividad reciente y favoritos locales de la app.
- No incluye minutos oficiales de escucha porque Spotify no expone ese dato en la Web API.

## Estructura principal

```text
main.py
app/
data/
requirements.txt
README.md
.env.example
```
