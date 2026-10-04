"""
Módulo de reproducción de audio y extracción con yt-dlp
Rafa Music Pro - Creado y Desarrollado por Rafa
"""

import asyncio
import functools
import time
from collections import deque
from typing import Optional, List, Dict, Any
import discord
import yt_dlp
from config import DEFAULT_VOLUME, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from utils.storage import storage

# Opciones optimizadas para yt-dlp
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
}

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

    @classmethod
    async def create_source(cls, query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop = None):
        """Extrae la información completa del tema desde URL o búsqueda."""
        loop = loop or asyncio.get_event_loop()
        
        # Si es una búsqueda directa sin url
        is_url = query.startswith("http://") or query.startswith("https://")
        search_target = query if is_url else f"ytsearch1:{query}"

        # Extraer usando hilo secundario
        data = await loop.run_in_executor(
            None,
            lambda: ytdl.extract_info(search_target, download=False)
        )

        if not data:
            raise Exception("No se encontró ningún resultado.")

        if 'entries' in data:
            if not data['entries']:
                raise Exception("No se encontró ninguna canción con ese nombre.")
            data = data['entries'][0]

        return cls(data, requester)

    @classmethod
    async def create_sources(cls, query: str, requester: discord.Member, loop: asyncio.AbstractEventLoop = None) -> tuple[List['Song'], bool, str]:
        """
        Extrae canciones individuales o listas de reproducción (Playlists) completas.
        Retorna (lista_canciones, es_playlist, titulo_playlist).
        """
        loop = loop or asyncio.get_event_loop()
        is_url = query.startswith("http://") or query.startswith("https://")
        is_playlist = is_url and ("list=" in query or "playlist" in query)

        if is_playlist:
            fast_p_opts = {
                'format': 'bestaudio/best',
                'extract_flat': 'in_playlist',
                'skip_download': True,
                'quiet': True,
                'no_warnings': True,
            }
            def _fetch_playlist():
                with yt_dlp.YoutubeDL(fast_p_opts) as p_ydl:
                    return p_ydl.extract_info(query, download=False)

            data = await loop.run_in_executor(None, _fetch_playlist)
            if not data or 'entries' not in data:
                raise Exception("No se pudo cargar la lista de reproducción.")

            songs = []
            for e in data['entries']:
                if e:
                    songs.append(cls(e, requester))

            if not songs:
                raise Exception("La lista de reproducción está vacía.")

            return songs, True, data.get('title', 'Lista de Reproducción')
        else:
            song = await cls.create_source(query, requester, loop)
            return [song], False, ""


class AutocompleteManager:
    """Gestor de autocompletado en tiempo real para el comando /play."""
    @staticmethod
    async def search_suggestions(query: str) -> List[tuple[str, str]]:
        """
        Retorna una lista de tuplas (nombre_a_mostrar, valor_busqueda).
        Optimizado para responder antes del timeout de 3 segundos de Discord.
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

        # Opciones ultraligeras para extraer solo títulos
        fast_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist',
            'skip_download': True,
        }

        def _fetch():
            with yt_dlp.YoutubeDL(fast_opts) as fast_ydl:
                search_query = f"ytsearch5:{query}"
                res = fast_ydl.extract_info(search_query, download=False)
                entries = res.get('entries', []) if res else []
                out = []
                for e in entries:
                    if not e:
                        continue
                    title = e.get('title') or 'Sin título'
                    dur = format_duration(e.get('duration'))
                    # Limitar nombre para Discord (máximo 100 caracteres)
                    display = f"🎵 {title[:80]} [{dur}]"
                    val = e.get('url') or e.get('webpage_url') or title
                    out.append((display, val))
                return out

        try:
            loop = asyncio.get_event_loop()
            results = await asyncio.wait_for(loop.run_in_executor(None, _fetch), timeout=2.4)
            _autocomplete_cache[query.lower()] = (now, results)
            return results
        except Exception:
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
                # Obtener url de stream fresca para evitar enlaces caducados
                loop = asyncio.get_event_loop()
                fresh_data = await loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(next_song.webpage_url, download=False)
                )
                stream_url = fresh_data.get('url') if fresh_data else next_song.stream_url

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
