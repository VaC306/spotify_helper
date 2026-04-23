# Spotify CLI Project

## Objetivo
Aplicación CLI en Python para gestionar playlists de Spotify.

Funcionalidades:
- Recomendar canciones por género
- Crear playlist desde archivo TXT
- Exportar playlist a TXT
- Generar prompts para IA (NO usar IA dentro de la app)

## Stack
- Python 3
- requests
- python-dotenv
- Spotify Web API

## Estructura esperada

project/
├─ main.py
├─ cli.py
├─ spotify_client.py
├─ playlist_manager.py
├─ recommender.py
├─ prompt_generator.py
├─ storage.py
│
├─ data/
│  ├─ liked_songs.json
│  └─ exports/
│
├─ .env
├─ requirements.txt

## Reglas IMPORTANTES

- No usar frameworks innecesarios
- No usar base de datos
- No usar interfaz gráfica
- No usar IA integrada
- Código simple, modular y claro
- Funciones pequeñas
- Manejo de errores obligatorio
- Mantener estructura consistente

## Formato de canciones

Siempre usar:
Título - Artista

## Prioridades

1. Crear playlist desde TXT
2. Exportar playlist a TXT
3. Recomendador simple
4. Generador de prompts

## Notas

- Mantener orden de canciones del TXT
- Manejar errores de búsqueda
- Evitar duplicados en liked songs
