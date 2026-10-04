"""
Módulo de reproducción de audio y extracción con yt-dlp
Rafa Music Pro - Creado y Desarrollado por Rafa
"""

import asyncio
import functools
import json
import os
import re
import time
import urllib.request
from collections import deque
from typing import Optional, List, Dict, Any
import discord
import yt_dlp
from config import DEFAULT_VOLUME, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from utils.storage import storage

# Gestión de Cookies de YouTube (opcional, para entornos de hosting como Railway)
COOKIES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cookies.txt")
cookies_env = os.getenv("YOUTUBE_COOKIES") or os.getenv("COOKIES_DATA")
if cookies_env and not os.path.exists(COOKIES_FILE):
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as f:
            f.write(cookies_env)
        print("🍪 Cookies de YouTube inicializadas desde variable de entorno.")
    except Exception as e:
        print(f"⚠️ Error al crear cookies.txt: {e}")

# Opciones optimizadas para yt-dlp con bypass de bot-check (Android / Web Embedded / iOS)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web_embedded', 'ios', 'mweb'],
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
    }
}

if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
    YTDL_OPTIONS['cookiefile'] = COOKIES_FILE
    print("🍪 Usando archivo cookies.txt para yt-dlp.")

# Filtros de audio DJ con FFmpeg
AUDIO_FILTERS = {
    "off": {"name": "Normal (Sin Filtros)", "ffmpeg": ""},
    "bassboost": {"name": "Bass Boost 🔊", "ffmpeg": "-af bass=g=12:f=110:w=0.6"},
    "bassboost_extreme": {"name": "Bass Boost Extremo 💥", "ffmpeg": "-af bass=g=22:f=110:w=0.6"},
    "nightcore": {"name": "Nightcore ⚡", "ffmpeg": "-af asetrate=48000*1.25,aresample=48000,atempo=1.06"},
    "vaporwave": {"name": "Vaporwave 🌊", "ffmpeg": "-af asetrate=48000*0.82,aresample=48000,atempo=1.0"},
    "8d": {"name": "Audio 8D 🎧", "ffmpeg": "-af apulsator=hz=0.125"}
}

# Opciones de FFmpeg base
BASE_BEFORE_OPTIONS = '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Caché en memoria para autocompletado rápido
_autocomplete_cache: Dict[str, tuple[float, List[tuple[str, str]]]] = {}
CACHE_TTL = 300  # 5 minutos

def format_duration(seconds: Optional[int]) -> str:
    """Convierte segundos a formato MM:SS o HH:MM:SS."""
    if not seconds or seconds <= 0:
        return "En vivo 🔴"
    minutes, sec = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{sec:02d}"
    return f"{minutes:02d}:{sec:02d}"

class Song:
    """Representa una pista musical."""
    def __init__(self, data: Dict[str, Any], requester: discord.Member):
        self.data = data
        self.requester = requester
        self.title: str = data.get('title', 'Canción desconocida')
        self.webpage_url: str = data.get('webpage_url') or data.get('url', '')
        self.stream_url: str = data.get('url', '')
        self.duration: Optional[int] = data.get('duration')
        self.duration_str: str = format_duration(self.duration)
        self.thumbnail: Optional[str] = data.get('thumbnail')
        self.uploader: str = data.get('uploader') or data.get('channel', 'Desconocido')
        self.extractor: str = data.get('extractor', 'youtube')

def _fetch_spotify_track_info(url: str) -> Optional[str]:
    """Extrae el título y artista de un enlace de Spotify mediante metadatos y oEmbed."""
    try:
        import urllib.parse
        oembed_url = f"https://open.spotify.com/oembed?url={urllib.parse.quote(url)}"
        req = urllib.request.Request(oembed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            title = data.get('title')
            
        req_page = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_page, timeout=3) as resp_page:
            html = resp_page.read().decode('utf-8', errors='ignore')
            desc_m = re.search(r'<meta property="og:description" content="([^"]+)"', html)
            if desc_m:
                desc = desc_m.group(1)
                artist = desc.split('·')[0].strip() if '·' in desc else desc.split('-')[0].strip()
                if artist and title:
                    return f"{artist} - {title}"
        return title
    except Exception as e:
        print(f"Error resolviendo Spotify: {e}")
        return None

def fetch_spotify_playlist_tracks(url: str) -> List[str]:
    """Extrae hasta 100 canciones de una playlist o álbum de Spotify mediante datos incrustados."""
    try:
        m = re.search(r'open\.spotify\.com\/(playlist|album)\/([a-zA-Z0-9]+)', url)
        if not m:
            return []
        kind, item_id = m.groups()
        embed_url = f"https://open.spotify.com/embed/{kind}/{item_id}"
        req = urllib.request.Request(embed_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            
        match = re.search(r'<script id="__NEXT_DATA__" type="application\/json">([^<]+)<\/script>', html)
        if match:
            data = json.loads(match.group(1))
            props = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity', {})
            track_list = props.get('trackList', [])
            tracks = []
            for t in track_list:
                title = t.get('title')
                artists = t.get('subtitle', '')
                if title:
                    tracks.append(f"{artists} - {title}" if artists else title)
            return tracks
    except Exception as e:
        print(f"Error extrayendo playlist de Spotify: {e}")
    return []

def _fetch_apple_music_info(url: str) -> Optional[str]:
    """Extrae el título y artista de un enlace de Apple Music."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
            title_m = re.search(r'<title>([^<]+)</title>', html)
            if title_m:
                raw = title_m.group(1)
                raw = re.sub(r'\s*[\-–|]\s*Apple Music.*$', '', raw, flags=re.I).strip()
                return raw
    except Exception as e:
        print(f"Error resolviendo Apple Music: {e}")
    return None

def resolve_universal_query(query: str) -> tuple[str, str, Optional[str]]:
    """
    Normaliza y detecta enlaces de Spotify, YouTube Shorts, YouTube Music, Apple Music,
    SoundCloud o búsquedas libres.
    Retorna (target_busqueda, nombre_plataforma, titulo_limpio).
    """
    q = query.strip()

    # 1. YouTube Shorts
    shorts_m = re.search(r'youtube\.com\/shorts\/([a-zA-Z0-9_-]{11})', q)
    if shorts_m:
        return f"https://www.youtube.com/watch?v={shorts_m.group(1)}", "YouTube Shorts", None

    # 2. YouTube Music
    if "music.youtube.com" in q:
        q = q.replace("music.youtube.com", "www.youtube.com")

    # 3. Spotify Track
    spotify_track = re.search(r'open\.spotify\.com\/track\/([a-zA-Z0-9]+)', q)
    if spotify_track:
        info = _fetch_spotify_track_info(f"https://open.spotify.com/track/{spotify_track.group(1)}")
        if info:
            return f"ytsearch1:{info}", "Spotify", info

    # 4. Apple Music
    if "music.apple.com" in q:
        apple_info = _fetch_apple_music_info(q)
        if apple_info:
            return f"ytsearch1:{apple_info}", "Apple Music", apple_info

    # 5. Prefijo explícito de SoundCloud (ej: sc:cancion o soundcloud:cancion)
    if q.lower().startswith("sc:") or q.lower().startswith("soundcloud:"):
        term = re.sub(r'^(?:sc|soundcloud):', '', q, flags=re.I).strip()
        return f"scsearch1:{term}", "SoundCloud", term

    # 6. ID de video de YouTube (11 caracteres)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', q):
        return f"https://www.youtube.com/watch?v={q}", "YouTube", None

    # 7. Enlace directo URL (SoundCloud, YouTube normal, enlaces mp3, radio)
    if q.startswith("http://") or q.startswith("https://"):
        return q, "URL Directa", None

    # 8. Búsqueda por texto (Cualquier canción, artista, género o remix)
    return f"ytsearch1:{q}", "Búsqueda Global", None


class Song:
    """Representa una pista musical."""
    def __init__(self, data: Dict[str, Any], requester: discord.Member, platform_tag: str = "🎵"):
        self.data = data
        self.requester = requester
        self.title: str = data.get('title', 'Canción desconocida')
        self.webpage_url: str = data.get('webpage_url') or data.get('url', '')
        self.stream_url: str = data.get('url', '')
        self.duration: Optional[int] = data.get('duration')
        self.duration_str: str = format_duration(self.duration)
        self.thumbnail: Optional[str] = data.get('thumbnail')
        self.uploader: str = data.get('uploader') or data.get('channel', 'Desconocido')
        self.extractor: str = data.get('extractor', 'youtube')
        self.platform_tag: str = platform_tag

    @classmethod
    async def create_source(cls, query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop = None):
        """Extrae la información completa del tema desde cualquier enlace o búsqueda con soporte multi-fuente."""
        loop = loop or asyncio.get_event_loop()
        
        search_target, platform, display_title = resolve_universal_query(query)
        data = None
        last_error = None

        # 1. Intentar extracción principal (YouTube / Enlace directo con extractor_args)
        try:
            data = await loop.run_in_executor(
                None,
                lambda: ytdl.extract_info(search_target, download=False)
            )
        except Exception as e:
            last_error = e
            print(f"⚠️ Aviso en extracción principal: {e}")

        # 2. Si falla o no hay entradas, activar rescate automático a SoundCloud
        if not data or ('entries' in data and not data.get('entries')):
            print("🔄 Activando rescate automático multi-fuente (SoundCloud)...")
            fallback_query = display_title
            
            # Si era un enlace de YouTube que falló, extraer el título real con oEmbed
            if not fallback_query and ("youtube.com/watch" in search_target or "youtu.be/" in search_target):
                m = re.search(r'(?:v=|\/)([a-zA-Z0-9_-]{11})', search_target)
                if m:
                    vid = m.group(1)
                    try:
                        def _fetch_oembed():
                            req = urllib.request.Request(
                                f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json",
                                headers={'User-Agent': 'Mozilla/5.0'}
                            )
                            with urllib.request.urlopen(req, timeout=5) as resp:
                                return json.loads(resp.read().decode()).get('title')
                        raw_title = await loop.run_in_executor(None, _fetch_oembed)
                        if raw_title:
                            fallback_query = re.sub(r'[\(\[][^\)\]]*(?:video|oficial|official|audio|lyric|remastered|hd|4k)[^\)\]]*[\)\]]', '', raw_title, flags=re.I).strip()
                            fallback_query = re.sub(r'\s+', ' ', fallback_query)
                    except Exception as e:
                        print(f"Error en oEmbed: {e}")

            if not fallback_query and not (query.startswith("http://") or query.startswith("https://")):
                fallback_query = query

            if fallback_query:
                try:
                    sc_opts = dict(YTDL_OPTIONS)
                    sc_opts['default_search'] = 'scsearch'
                    def _fetch_sc():
                        with yt_dlp.YoutubeDL(sc_opts) as sc_ydl:
                            return sc_ydl.extract_info(f"scsearch1:{fallback_query}", download=False)
                    data = await loop.run_in_executor(None, _fetch_sc)
                    if data:
                        print(f"✅ Canción recuperada exitosamente vía SoundCloud: {fallback_query}")
                except Exception as sc_err:
                    print(f"⚠️ Error en rescate SoundCloud: {sc_err}")

        if not data:
            err_str = str(last_error) if last_error else ""
            if "Sign in to confirm" in err_str:
                raise Exception("No se pudo obtener el audio en este momento. Intenta escribiendo el nombre de la canción directamente (ej: `/play nombre de la canción`).")
            raise Exception(last_error or "No se encontró ningún resultado para esta búsqueda musical.")

        if 'entries' in data:
            if not data['entries']:
                raise Exception("No se encontró ninguna canción con ese nombre o enlace.")
            data = data['entries'][0]

        return cls(data, requester, platform_tag=platform)

    @classmethod
    async def create_sources(cls, query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop = None) -> tuple[List['Song'], bool, str]:
        """
        Extrae canciones individuales o listas de reproducción (YouTube, Spotify Playlists/Álbumes).
        Retorna (lista_canciones, es_playlist, titulo_playlist).
        """
        loop = loop or asyncio.get_event_loop()
        q = query.strip()

        # 1. Soporte para Playlists y Álbumes de Spotify
        if "open.spotify.com/playlist/" in q or "open.spotify.com/album/" in q:
            spotify_tracks = await loop.run_in_executor(None, lambda: fetch_spotify_playlist_tracks(q))
            if spotify_tracks:
                is_album = "album" in q
                tipo = "Álbum de Spotify" if is_album else "Playlist de Spotify"
                # Cargar la primera canción inmediatamente para que empiece la reproducción sin demora
                first_song = await cls.create_source(spotify_tracks[0], requester, loop)
                songs = [first_song]
                
                # Crear las siguientes pistas
                for track_name in spotify_tracks[1:50]: # Límite inicial de 50 temas para fluidez
                    dummy_data = {
                        'title': track_name,
                        'webpage_url': f"https://www.youtube.com/results?search_query={urllib.parse.quote(track_name)}",
                        'url': '', # Se resolverá al reproducir si no tiene url
                        'duration': None,
                        'uploader': 'Spotify',
                        '_lazy_query': track_name
                    }
                    songs.append(cls(dummy_data, requester, platform_tag="Spotify"))
                return songs, True, f"{tipo} ({len(songs)} canciones)"

        # 2. Soporte para Playlists de YouTube
        is_url = q.startswith("http://") or q.startswith("https://")
        is_yt_playlist = is_url and ("list=" in q or "playlist" in q)

        if is_yt_playlist:
            fast_p_opts = {
                'format': 'bestaudio/best',
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android', 'web_embedded', 'ios'],
                    }
                }
            }
            def _fetch_playlist():
                with yt_dlp.YoutubeDL(fast_p_opts) as p_ydl:
                    return p_ydl.extract_info(q, download=False)

            data = await loop.run_in_executor(None, _fetch_playlist)
            if not data or 'entries' not in data:
                raise Exception("No se pudo cargar la lista de reproducción de YouTube.")

            songs = []
            for e in data['entries']:
                if e:
                    songs.append(cls(e, requester, platform_tag="YouTube"))

            if not songs:
                raise Exception("La lista de reproducción está vacía.")

            return songs, True, data.get('title', 'Lista de Reproducción')
        else:
            song = await cls.create_source(q, requester, loop)
            return [song], False, ""


# Opciones para búsquedas rápidas con bypass de bot-check
FAST_SEARCH_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'skip_download': True,
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web_embedded', 'ios', 'mweb'],
        }
    },
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }
}
if os.path.exists(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
    FAST_SEARCH_OPTS['cookiefile'] = COOKIES_FILE

class AutocompleteManager:
    """Gestor de autocompletado en tiempo real ultra-rápido para el comando /play."""
    @staticmethod
    async def search_suggestions(query: str) -> List[tuple[str, str]]:
        """
        Retorna una lista de sugerencias instantáneas.
        Combina la API instantánea de Google Suggestions (~40ms) con yt-dlp y SoundCloud.
        """
        query = query.strip()
        if not query:
            return []

        # Verificar caché
        now = time.time()
        cached = _autocomplete_cache.get(query.lower())
        if cached:
            cache_time, results = cached
            if now - cache_time < CACHE_TTL:
                return results

        results = []

        # 1. Sugerencias instantáneas de Google/YouTube (~40ms)
        def _fetch_google_suggest():
            try:
                import urllib.parse
                url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={urllib.parse.quote(query)}"
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    data = json.loads(resp.read().decode())
                    if len(data) > 1 and isinstance(data[1], list):
                        return data[1][:12]
            except Exception:
                pass
            return []

        # 2. Canciones reales directas con yt-dlp usando cliente android
        def _fetch_ytdl():
            try:
                with yt_dlp.YoutubeDL(FAST_SEARCH_OPTS) as fast_ydl:
                    res = fast_ydl.extract_info(f"ytsearch10:{query}", download=False)
                    entries = res.get('entries', []) if res else []
                    out = []
                    for e in entries:
                        if not e:
                            continue
                        title = e.get('title') or 'Sin título'
                        dur = format_duration(e.get('duration'))
                        display = f"🎵 {title[:76]} [{dur}]"
                        vid_id = e.get('id')
                        raw_url = e.get('url') or e.get('webpage_url') or ''
                        if vid_id and len(vid_id) == 11:
                            val = f"https://www.youtube.com/watch?v={vid_id}"
                        elif raw_url.startswith("http"):
                            val = raw_url
                        elif len(raw_url) == 11:
                            val = f"https://www.youtube.com/watch?v={raw_url}"
                        else:
                            val = title
                        out.append((display, val))
                    return out
            except Exception:
                return []

        loop = asyncio.get_event_loop()
        suggest_task = loop.run_in_executor(None, _fetch_google_suggest)
        ytdl_task = loop.run_in_executor(None, _fetch_ytdl)

        try:
            # Esperar ambas en paralelo con timeout seguro para Discord (1.8s)
            ytdl_res, google_res = await asyncio.gather(
                asyncio.wait_for(ytdl_task, timeout=1.8),
                suggest_task,
                return_exceptions=True
            )
            if isinstance(ytdl_res, list) and ytdl_res:
                results.extend(ytdl_res)
            if isinstance(google_res, list) and google_res:
                for s in google_res:
                    if not any(val.lower() == s.lower() for _, val in results):
                        results.append((f"🔥 {s.title()}", s))
        except Exception:
            try:
                google_res = await asyncio.wait_for(suggest_task, timeout=0.6)
                if isinstance(google_res, list):
                    for s in google_res:
                        results.append((f"🔥 {s.title()}", s))
            except Exception:
                pass

        if results:
            _autocomplete_cache[query.lower()] = (now, results)

        return results[:25]

    @staticmethod
    async def get_search_results(query: str, limit: int = 15) -> List[Dict[str, Any]]:
        """Retorna hasta 15 resultados completos para el menú interactivo /buscar con soporte dual YouTube + SoundCloud."""
        def _fetch():
            clean = []
            # 1. Intentar YouTube con clientes móviles
            try:
                with yt_dlp.YoutubeDL(FAST_SEARCH_OPTS) as ydl:
                    res = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                    entries = res.get('entries', []) if res else []
                    for e in entries:
                        if not e:
                            continue
                        vid_id = e.get('id')
                        url = f"https://www.youtube.com/watch?v={vid_id}" if (vid_id and len(vid_id) == 11) else (e.get('url') or e.get('webpage_url', ''))
                        clean.append({
                            'title': e.get('title', 'Sin título'),
                            'duration': e.get('duration'),
                            'duration_str': format_duration(e.get('duration')),
                            'uploader': e.get('uploader') or e.get('channel', 'Desconocido'),
                            'url': url
                        })
            except Exception as e:
                print(f"Error en búsqueda YouTube: {e}")

            # 2. Si faltan resultados, complementar con SoundCloud
            if len(clean) < limit:
                try:
                    sc_opts = dict(FAST_SEARCH_OPTS)
                    sc_opts['default_search'] = 'scsearch'
                    with yt_dlp.YoutubeDL(sc_opts) as sc_ydl:
                        res = sc_ydl.extract_info(f"scsearch{limit}:{query}", download=False)
                        entries = res.get('entries', []) if res else []
                        for e in entries:
                            if not e:
                                continue
                            t = e.get('title', 'Sin título')
                            if not any(c['title'].lower() == t.lower() for c in clean):
                                clean.append({
                                    'title': f"[SC] {t}",
                                    'duration': e.get('duration'),
                                    'duration_str': format_duration(e.get('duration')),
                                    'uploader': e.get('uploader') or 'SoundCloud',
                                    'url': e.get('url') or e.get('webpage_url', '')
                                })
                            if len(clean) >= limit:
                                break
                except Exception as sc_err:
                    print(f"Error en búsqueda SoundCloud: {sc_err}")

            return clean[:limit]

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _fetch)
        except Exception as e:
            print(f"Error obteniendo lista de búsqueda: {e}")
            return []


class GuildPlayer:
    """Controlador de reproducción por servidor (Cola, Voz, Estado 24/7)."""
    def __init__(self, bot: discord.Client, guild: discord.Guild):
        self.bot = bot
        self.guild = guild
        self.queue: deque[Song] = deque()
        self.history: deque[Song] = deque(maxlen=20)
        self.current: Optional[Song] = None
        self.voice_client: Optional[discord.VoiceClient] = None
        self.text_channel: Optional[discord.TextChannel] = None
        
        self.volume: float = DEFAULT_VOLUME
        self.loop_mode: str = "off"  # "off", "song", "queue"
        self.filter_mode: str = "off" # "off", "bassboost", "nightcore", "vaporwave", "8d"
        self.now_playing_message: Optional[discord.Message] = None
        
        self.is_playing: bool = False
        self._inactivity_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    @property
    def is_247(self) -> bool:
        """Verifica si este servidor tiene activado el modo 24/7."""
        return storage.is_247(self.guild.id)

    def cancel_inactivity_timer(self):
        """Cancela el contador de auto-desconexión si existe."""
        if self._inactivity_task and not self._inactivity_task.done():
            self._inactivity_task.cancel()
            self._inactivity_task = None

    def start_inactivity_timer(self):
        """Inicia el temporizador de desconexión por inactividad (solo si no es 24/7)."""
        if self.is_247:
            # En modo 24/7 NUNCA se desconecta
            return
        self.cancel_inactivity_timer()
        self._inactivity_task = asyncio.create_task(self._inactivity_countdown())

    async def _inactivity_countdown(self):
        """Espera 3 minutos. Si no hay actividad y no es 24/7, se desconecta."""
        try:
            await asyncio.sleep(180)  # 3 minutos
            if not self.is_247 and self.voice_client and self.voice_client.is_connected() and not self.is_playing:
                if self.text_channel:
                    embed = discord.Embed(
                        description="💤 **Me he desconectado por inactividad.**\n"
                                    "💡 *Para que me quede siempre conectado en el canal, usa `/bot canal 24.7`*",
                        color=COLOR_PRIMARY
                    )
                    embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
                    await self.text_channel.send(embed=embed)
                await self.cleanup()
        except asyncio.CancelledError:
            pass

    async def play_next(self, error=None):
        """Reproduce la siguiente canción en la cola o maneja repeticiones."""
        if error:
            print(f"Error en reproducción en {self.guild.name}: {error}")

        if not self.voice_client or not self.voice_client.is_connected():
            return

        async with self._lock:
            # Manejo del modo de repetición
            if self.loop_mode == "song" and self.current:
                # Repetir la misma canción
                next_song = self.current
            elif self.loop_mode == "queue" and self.current:
                # Agregar la actual al final de la cola
                self.queue.append(self.current)
                next_song = self.queue.popleft() if self.queue else None
            else:
                next_song = self.queue.popleft() if self.queue else None

            if not next_song:
                self.current = None
                self.is_playing = False
                self.start_inactivity_timer()
                return

            self.cancel_inactivity_timer()
            self.current = next_song
            self.is_playing = True

            try:
                loop = asyncio.get_event_loop()
                stream_url = None

                # 1. Si la canción requiere resolución tardía (ej: de Spotify o lista)
                lazy_q = next_song.data.get('_lazy_query')
                if lazy_q:
                    resolved = await Song.create_source(lazy_q, next_song.requester, loop)
                    next_song.title = resolved.title
                    next_song.webpage_url = resolved.webpage_url
                    next_song.stream_url = resolved.stream_url
                    next_song.duration = resolved.duration
                    next_song.duration_str = resolved.duration_str
                    next_song.thumbnail = resolved.thumbnail
                    stream_url = resolved.stream_url
                elif next_song.stream_url and ("googlevideo.com" not in next_song.stream_url):
                    stream_url = next_song.stream_url
                else:
                    try:
                        fresh_data = await loop.run_in_executor(
                            None,
                            lambda: ytdl.extract_info(next_song.webpage_url, download=False)
                        )
                        stream_url = fresh_data.get('url') if fresh_data else next_song.stream_url
                    except Exception:
                        stream_url = next_song.stream_url

                if not stream_url:
                    stream_url = next_song.stream_url

                # Aplicar filtro de audio si está activo
                filter_args = AUDIO_FILTERS.get(self.filter_mode, {}).get("ffmpeg", "")
                custom_opts = f"-vn {filter_args}".strip()

                audio_source = discord.FFmpegPCMAudio(
                    stream_url,
                    before_options=BASE_BEFORE_OPTIONS,
                    options=custom_opts,
                    executable='ffmpeg'
                )
                volume_source = discord.PCMVolumeTransformer(audio_source, volume=self.volume)

                def after_callback(err):
                    coro = self.play_next(err)
                    fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
                    try:
                        fut.result()
                    except Exception as e:
                        print(f"Error en callback after: {e}")

                self.voice_client.play(volume_source, after=after_callback)

                # Notificar Now Playing
                await self._send_now_playing(next_song)

            except Exception as e:
                print(f"Error iniciando reproducción de '{next_song.title}': {e}")
                if self.text_channel:
                    await self.text_channel.send(f"⚠️ Error reproduciendo **{next_song.title}**: `{e}`. Pasando a la siguiente...")
                # Intentar siguiente
                await self.play_next()

    async def _send_now_playing(self, song: Song):
        """Envía el mensaje de Ahora Reproduciendo con controles interactivos."""
        if not self.text_channel:
            return

        from utils.ui_components import PlayerControlView

        filter_name = AUDIO_FILTERS.get(self.filter_mode, {}).get("name", "Normal")
        embed = discord.Embed(
            title="🎶 Ahora Reproduciendo",
            description=f"### [{song.title}]({song.webpage_url})\n\n"
                        f"⏱️ **Duración:** `{song.duration_str}`\n"
                        f"👤 **Canal / Artista:** `{song.uploader}`\n"
                        f"🙋 **Pedido por:** {song.requester.mention}\n"
                        f"🔊 **Volumen:** `{int(self.volume * 100)}%` | 🎛️ **Filtro:** `{filter_name}`\n"
                        f"🔁 **Repetición:** `{self.loop_mode.capitalize()}` | 🛡️ **24/7:** `{'Activado 🟢' if self.is_247 else 'Desactivado ⚪'}`",
            color=COLOR_PRIMARY
        )
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)

        embed.set_footer(
            text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME} | /help",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        view = PlayerControlView(self)
        try:
            self.now_playing_message = await self.text_channel.send(embed=embed, view=view)
        except Exception as e:
            print(f"No se pudo enviar el embed de reproducción: {e}")

    async def cleanup(self):
        """Limpia la cola y desconecta el cliente de voz."""
        self.cancel_inactivity_timer()
        self.queue.clear()
        self.current = None
        self.is_playing = False

        if self.voice_client:
            try:
                if self.voice_client.is_playing() or self.voice_client.is_paused():
                    self.voice_client.stop()
                await self.voice_client.disconnect(force=True)
            except Exception as e:
                print(f"Error limpiando voice_client: {e}")
            self.voice_client = None


class MusicManager:
    """Colección y gestor global de reproductores para cada Guild."""
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.players: Dict[int, GuildPlayer] = {}

    def get_player(self, guild: discord.Guild) -> GuildPlayer:
        """Obtiene o crea el GuildPlayer del servidor."""
        if guild.id not in self.players:
            self.players[guild.id] = GuildPlayer(self.bot, guild)
        return self.players[guild.id]

    async def remove_player(self, guild_id: int):
        """Elimina el reproductor del servidor."""
        if guild_id in self.players:
            await self.players[guild_id].cleanup()
            del self.players[guild_id]
