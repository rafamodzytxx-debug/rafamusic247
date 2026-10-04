"""
Cog de Estaciones de Radio 24/7 en Vivo
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from utils.audio_player import MusicManager, Song, BASE_BEFORE_OPTIONS
from utils.storage import storage

RADIO_STATIONS = {
    "lofi": {
        "name": "☕ Lofi Hip Hop Beats (Chill & Estudio)",
        "url": "http://stream.zeno.fm/f3wvbbqmdg8uv",
        "description": "Música relajante instrumental 24/7 ideal para estudiar, jugar o descansar.",
        "emoji": "☕"
    },
    "reggaeton": {
        "name": "🔥 Reggaetón Latino 24/7 Urbano",
        "url": "http://stream.zeno.fm/s4k3v9f0d1zuv",
        "description": "Los mejores éxitos del género urbano, perreo y reggaetón latino sin cortes.",
        "emoji": "🔥"
    },
    "phonk": {
        "name": "🏎️ Drift Phonk & Gaming 24/7",
        "url": "http://stream.zeno.fm/7x3e7qfghg8uv",
        "description": "Graves pesados, drift phonk y electrónica potente para jugar a tope.",
        "emoji": "🏎️"
    },
    "rock": {
        "name": "🎸 Classic Rock & Pop Clásico 80s/90s",
        "url": "http://stream.zeno.fm/w42b0p6481zuv",
        "description": "Las mejores leyendas del rock en inglés y español en emisión continua.",
        "emoji": "🎸"
    },
    "electro": {
        "name": "⚡ EDM & Dance Electrónica 24/7",
        "url": "http://stream.zeno.fm/4v3fvffghg8uv",
        "description": "Sesiones de música electrónica, dance y festivales non-stop.",
        "emoji": "⚡"
    }
}

class Radio(commands.Cog):
    def __init__(self, bot: commands.Bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    @app_commands.command(name="radio", description="Sintoniza estaciones de radio 24/7 ininterrumpidas")
    @app_commands.choices(estacion=[
        app_commands.Choice(name="☕ Lofi Hip Hop Beats 24/7", value="lofi"),
        app_commands.Choice(name="🔥 Reggaetón Urbano Latino 24/7", value="reggaeton"),
        app_commands.Choice(name="🏎️ Phonk & Drift Gaming 24/7", value="phonk"),
        app_commands.Choice(name="⚡ EDM Electrónica 24/7", value="electro"),
        app_commands.Choice(name="🎸 Classic Rock Clásico 24/7", value="rock"),
    ])
    async def radio_cmd(self, interaction: discord.Interaction, estacion: app_commands.Choice[str]):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                "❌ **Debes estar en un canal de voz** para sintonizar una estación de radio.",
                ephemeral=True
            )

        channel = interaction.user.voice.channel
        player = self.music_manager.get_player(interaction.guild)
        player.text_channel = interaction.channel

        # Conectar al canal si no lo está
        if not player.voice_client or not player.voice_client.is_connected():
            player.voice_client = await channel.connect(timeout=20.0, reconnect=True)
        elif player.voice_client.channel != channel:
            await player.voice_client.move_to(channel)

        info = RADIO_STATIONS[estacion.value]

        # Detener reproducción previa y vaciar cola
        player.queue.clear()
        if player.voice_client.is_playing() or player.voice_client.is_paused():
            player.voice_client.stop()

        # Activar modo 24/7 automáticamente para que la radio nunca se corte
        await storage.set_247(interaction.guild.id, channel.id, interaction.channel.id)
        player.cancel_inactivity_timer()

        # Iniciar streaming continuo
        audio_source = discord.FFmpegPCMAudio(
            info["url"],
            before_options=BASE_BEFORE_OPTIONS,
            options='-vn',
            executable='ffmpeg'
        )
        volume_source = discord.PCMVolumeTransformer(audio_source, volume=player.volume)

        # Crear objeto ficticio de canción para el reproductor
        radio_song = Song({
            "title": f"📻 Estación en Vivo: {info['name']}",
            "webpage_url": info["url"],
            "url": info["url"],
            "duration": None,
            "uploader": f"Radio 24/7 • {BOT_NAME}",
            "thumbnail": self.bot.user.display_avatar.url if self.bot.user else None
        }, interaction.user)

        player.current = radio_song
        player.is_playing = True

        def radio_after(err):
            if err:
                print(f"Error en transmisión de radio: {err}")
            player.is_playing = False

        player.voice_client.play(volume_source, after=radio_after)

        embed = discord.Embed(
            title=f"{info['emoji']} Sintonizador de Radio 24/7 en Vivo",
            description=(
                f"### 📻 Sintonizando: **{info['name']}**\n\n"
                f"📝 **Descripción:** {info['description']}\n"
                f"🔊 **Canal:** {channel.mention}\n"
                f"🛡️ **Modo 24/7:** `Activado Automáticamente 🟢` (No se detendrá)\n"
                f"🙋 **Sintonizado por:** {interaction.user.mention}\n\n"
                f"💡 *Para cambiar a música normal, usa `/play`. Para apagar usa `/stop` o `/desconect 24.7`*"
            ),
            color=COLOR_SUCCESS
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot, music_manager: MusicManager):
    await bot.add_cog(Radio(bot, music_manager))
