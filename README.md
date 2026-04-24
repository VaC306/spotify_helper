# Spotify CLI Playlist Manager

Aplicacion CLI en Python para gestionar playlists de Spotify usando la Web API oficial.

## Funcionalidades

- Recomendar canciones por genero y guardarlas localmente.
- Crear una playlist desde un archivo TXT.
- Exportar una playlist existente a un archivo TXT.

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

## Estructura principal

```text
main.py
app/
data/
requirements.txt
README.md
.env.example
```
