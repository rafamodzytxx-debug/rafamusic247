"""
Cog de Música: /join, /play con autocompletado interactivo, cola y controles
Rafa Music Pro - Creado y Desarrollado por Rafa
"""

import discord
from discord.ext import commands
from discord import app_commands
import random
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from utils.audio_player import MusicManager, Song, AutocompleteManager
from utils.ui_components import PlayerControlView

class Music(commands.Cog):
    def __init__(self, bot: commands.Bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager

    async def _ensure_voice(self, interaction: discord.Interaction) -> bool:
        """Verifica y conecta el bot al canal de voz del usuario."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(
                description="❌ **Debes estar conectado a un canal de voz** para usar este comando.",
                color=COLOR_ERROR
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)
            return False

        user_channel = interaction.user.voice.channel
        player = self.music_manager.get_player(interaction.guild)

        if not player.voice_client or not player.voice_client.is_connected():
            try:
                player.voice_client = await user_channel.connect(timeout=20.0, reconnect=True)
            except Exception as e:
                embed = discord.Embed(
                    description=f"❌ No pude conectarme al canal de voz: `{e}`",
                    color=COLOR_ERROR
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return False
        elif player.voice_client.channel != user_channel:
            # Si el bot ya está en otro canal, moverlo si el usuario está en otro
            try:
                await player.voice_client.move_to(user_channel)
            except Exception as e:
                embed = discord.Embed(
                    description=f"❌ No pude moverme a tu canal: `{e}`",
                    color=COLOR_ERROR
                )
                if not interaction.response.is_done():
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return False

        player.text_channel = interaction.channel
        return True

    @app_commands.command(name="join", description="Conecta el bot Rafa Music Pro a tu canal de voz")
    async def join_cmd(self, interaction: discord.Interaction):
        """Comando /join solicitado por el usuario."""
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(
                "❌ **Primero debes unirte a un canal de voz.**",
                ephemeral=True
            )

        channel = interaction.user.voice.channel
        player = self.music_manager.get_player(interaction.guild)
        player.text_channel = interaction.channel

        if player.voice_client and player.voice_client.is_connected():
            if player.voice_client.channel == channel:
                return await interaction.response.send_message(
                    f"🔊 Ya estoy conectado en **{channel.name}**!",
                    ephemeral=True
                )
            await player.voice_client.move_to(channel)
        else:
            player.voice_client = await channel.connect(timeout=20.0, reconnect=True)

        embed = discord.Embed(
            title="🔊 ¡Conectado al Canal!",
            description=f"Me he unido a **{channel.name}**.\n"
                        f"Usa `/play` para empezar a escuchar música con la mejor calidad sonora.",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="play", description="Reproduce una canción o la agrega a la lista de espera")
    @app_commands.describe(musica="Nombre de la canción o enlace (YouTube, etc.)")
    async def play_cmd(self, interaction: discord.Interaction, musica: str):
        """Comando /play con autocompletado y búsqueda en vivo."""
        await interaction.response.defer(thinking=True)

        # Conectar a voz
        if not await self._ensure_voice(interaction):
            return

        player = self.music_manager.get_player(interaction.guild)
        player.text_channel = interaction.channel

        try:
            # Obtener canciones (soporta tanto individuales como playlists completas)
            songs, is_playlist, playlist_title = await Song.create_sources(musica, interaction.user, loop=self.bot.loop)
        except Exception as e:
            embed = discord.Embed(
                title="❌ Error al cargar la música",
                description=f"No se pudo cargar: `{e}`\nIntenta con otro título o enlace.",
                color=COLOR_ERROR
            )
            return await interaction.followup.send(embed=embed)

        if is_playlist:
            # Agregar todas las canciones de la lista a la cola
            for s in songs:
                player.queue.append(s)

            embed = discord.Embed(
                title="📚 ¡Lista de Reproducción Agregada!",
                description=f"### 🎵 {playlist_title}\n\n"
                            f"🔢 **Total de canciones añadidas:** `{len(songs)}`\n"
                            f"🙋 **Añadida por:** {interaction.user.mention}\n"
                            f"📜 Usa `/queue` para ver la lista completa.",
                color=COLOR_PRIMARY
            )
            embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
            await interaction.followup.send(embed=embed)

            # Si no estaba sonando nada, arrancar
            if not player.is_playing:
                await player.play_next()
            return

        # Canción individual
        song = songs[0]

        # Si ya está sonando algo, agregar a la cola
        if player.is_playing or (player.voice_client and player.voice_client.is_playing()):
            player.queue.append(song)
            embed = discord.Embed(
                title="📝 Agregado a la Cola de Reproducción",
                description=f"### [{song.title}]({song.webpage_url})\n\n"
                            f"⏱️ **Duración:** `{song.duration_str}`\n"
                            f"👤 **Canal:** `{song.uploader}`\n"
                            f"🔢 **Posición en cola:** `#{len(player.queue)}`\n"
                            f"🙋 **Pedido por:** {interaction.user.mention}",
                color=COLOR_PRIMARY
            )
            if song.thumbnail:
                embed.set_thumbnail(url=song.thumbnail)
            embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
            await interaction.followup.send(embed=embed)
        else:
            # Reproducir inmediatamente
            player.queue.append(song)
            await player.play_next()
            embed = discord.Embed(
                description=f"▶️ Cargando **[{song.title}]({song.webpage_url})**...",
                color=COLOR_SUCCESS
            )
            await interaction.followup.send(embed=embed)

    @play_cmd.autocomplete("musica")
    async def play_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        """Autocompletado interactivo con hasta 25 resultados (máximo de Discord)."""
        if not current.strip():
            # 15 sugerencias populares de inicio
            defaults = [
                ("🔥 Bad Bunny - Tití Me Preguntó", "Bad Bunny Tití Me Preguntó"),
                ("🔥 The Weeknd - Blinding Lights", "The Weeknd Blinding Lights"),
                ("🔥 Quevedo - Columbia", "Quevedo Columbia"),
                ("🔥 Feid, ATL Jacob - LUNA", "Feid Luna"),
                ("🔥 Bizarrap & Shakira - Bzrp Sessions", "Bizarrap Shakira Sessions"),
                ("🔥 Rauw Alejandro - Todo de Ti", "Rauw Alejandro Todo de Ti"),
                ("🔥 Peso Pluma - Ella Baila Sola", "Peso Pluma Ella Baila Sola"),
                ("🔥 Karol G - Provenza", "Karol G Provenza"),
                ("🔥 Travis Scott - FE!N", "Travis Scott FEIN"),
                ("🔥 Drake - God's Plan", "Drake Gods Plan"),
                ("🔥 Daddy Yankee - Gasolina", "Daddy Yankee Gasolina"),
                ("🔥 Don Omar - Danza Kuduro", "Don Omar Danza Kuduro"),
            ]
            return [
                app_commands.Choice(name=name, value=val)
                for name, val in defaults[:25]
            ]

        # Si el usuario ya pegó un enlace, no buscar
        if current.startswith("http://") or current.startswith("https://"):
            return [app_commands.Choice(name=f"🔗 Enlace directo: {current[:80]}", value=current)]

        # Buscar en YouTube con yt-dlp hasta 25 canciones (límite máximo permitido por Discord)
        results = await AutocompleteManager.search_suggestions(current)
        choices = []
        for display_name, search_val in results[:25]:
            choices.append(app_commands.Choice(name=display_name[:100], value=search_val[:100]))

        if not choices:
            choices.append(app_commands.Choice(name=f"🔍 Buscar: '{current[:80]}'", value=current))

        return choices[:25]

    @app_commands.command(name="buscar", description="Busca un montón de canciones y elígela en un menú interactivo")
    @app_commands.describe(musica="Nombre de la canción o artista a buscar")
    async def buscar_cmd(self, interaction: discord.Interaction, musica: str):
        """Busca hasta 15 canciones y las muestra en un menú desplegable interactivo."""
        await interaction.response.defer(thinking=True)
        if not await self._ensure_voice(interaction):
            return

        results = await AutocompleteManager.get_search_results(musica, limit=15)
        if not results:
            return await interaction.followup.send(f"❌ No se encontraron canciones para: `{musica}`")

        player = self.music_manager.get_player(interaction.guild)
        player.text_channel = interaction.channel

        from utils.ui_components import SongSelectView

        desc = ""
        for i, s in enumerate(results, 1):
            desc += f"`{i}.` **[{s['title'][:55]}]({s['url']})** (`{s['duration_str']}`)\n"

        embed = discord.Embed(
            title=f"🔎 Resultados de Búsqueda para: \"{musica}\"",
            description=f"{desc}\n👇 **Selecciona la canción que quieres escuchar en el menú de abajo:**",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")

        view = SongSelectView(player, results, interaction.user)
        await interaction.followup.send(embed=embed, view=view)

    @app_commands.command(name="skip", description="Salta la canción que está sonando actualmente")
    async def skip_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        vc = player.voice_client

        if not vc or not vc.is_connected() or not player.is_playing:
            return await interaction.response.send_message("❌ No hay ninguna canción reproduciéndose.", ephemeral=True)

        current_title = player.current.title if player.current else "canción"
        vc.stop()
        embed = discord.Embed(
            description=f"⏭️ **Se saltó:** `{current_title}`",
            color=COLOR_PRIMARY
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="stop", description="Detiene la música y vacía la cola")
    async def stop_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        vc = player.voice_client

        if not vc or not vc.is_connected():
            return await interaction.response.send_message("❌ El bot no está conectado a un canal de voz.", ephemeral=True)

        player.queue.clear()
        if vc.is_playing() or vc.is_paused():
            vc.stop()

        if not player.is_247:
            await player.cleanup()
            msg = "⏹️ **Música detenida, cola limpiada y bot desconectado.**"
        else:
            msg = "⏹️ **Música detenida y cola vaciada.**\n*(El bot permanece en el canal porque el modo 24/7 está activado 🛡️)*"

        embed = discord.Embed(description=msg, color=COLOR_PRIMARY)
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="Pausa la reproducción actual")
    async def pause_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        vc = player.voice_client

        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ No hay música reproduciéndose para pausar.", ephemeral=True)

        vc.pause()
        await interaction.response.send_message("⏸️ **Música pausada.** Usa `/resume` para continuar.", ephemeral=False)

    @app_commands.command(name="resume", description="Reanuda la canción pausada")
    async def resume_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        vc = player.voice_client

        if not vc or not vc.is_paused():
            return await interaction.response.send_message("❌ La música no está pausada.", ephemeral=True)

        vc.resume()
        await interaction.response.send_message("▶️ **Música reanudada.**", ephemeral=False)

    @app_commands.command(name="queue", description="Muestra la lista de canciones en espera")
    async def queue_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)

        if not player.current and not player.queue:
            return await interaction.response.send_message("📭 La cola de reproducción está vacía.", ephemeral=True)

        embed = discord.Embed(
            title=f"📜 Cola de Reproducción - {interaction.guild.name}",
            color=COLOR_PRIMARY
        )
        if player.current:
            embed.add_field(
                name="🔊 Ahora Reproduciendo",
                value=f"[{player.current.title}]({player.current.webpage_url}) (`{player.current.duration_str}`)\nPedido por: {player.current.requester.mention}",
                inline=False
            )

        queue_list = list(player.queue)
        if queue_list:
            desc = ""
            for idx, s in enumerate(queue_list[:15], 1):
                desc += f"`{idx}.` [{s.title}]({s.webpage_url}) | `{s.duration_str}` (por {s.requester.display_name})\n"
            if len(queue_list) > 15:
                desc += f"\n*... y {len(queue_list) - 15} canciones más.*"
            embed.add_field(name="En espera:", value=desc, inline=False)
        else:
            embed.add_field(name="En espera:", value="*No hay más temas en la cola.*", inline=False)

        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nowplaying", description="Muestra información detallada de la canción actual")
    async def nowplaying_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)

        if not player.current or not player.is_playing:
            return await interaction.response.send_message("❌ No hay ninguna canción reproduciéndose.", ephemeral=True)

        song = player.current
        embed = discord.Embed(
            title="🎶 Canción Actual",
            description=f"### [{song.title}]({song.webpage_url})\n\n"
                        f"⏱️ **Duración:** `{song.duration_str}`\n"
                        f"👤 **Artista / Canal:** `{song.uploader}`\n"
                        f"🙋 **Pedido por:** {song.requester.mention}\n"
                        f"🔊 **Volumen:** `{int(player.volume * 100)}%`\n"
                        f"🔁 **Repetición:** `{player.loop_mode.capitalize()}`\n"
                        f"🛡️ **Modo 24/7:** `{'Activado 🟢' if player.is_247 else 'Desactivado ⚪'}`",
            color=COLOR_PRIMARY
        )
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed, view=PlayerControlView(player))

    @app_commands.command(name="volume", description="Ajusta el volumen de la música (1% a 150%)")
    @app_commands.describe(nivel="Porcentaje de volumen (ej: 80)")
    async def volume_cmd(self, interaction: discord.Interaction, nivel: int):
        if nivel < 1 or nivel > 150:
            return await interaction.response.send_message("❌ El volumen debe estar entre 1% y 150%.", ephemeral=True)

        player = self.music_manager.get_player(interaction.guild)
        player.volume = nivel / 100.0

        if player.voice_client and player.voice_client.source and hasattr(player.voice_client.source, 'volume'):
            player.voice_client.source.volume = player.volume

        await interaction.response.send_message(f"🔊 Volumen ajustado al **{nivel}%**.", ephemeral=False)

    @app_commands.command(name="loop", description="Cambia el modo de repetición")
    @app_commands.choices(modo=[
        app_commands.Choice(name="Desactivado (Normal)", value="off"),
        app_commands.Choice(name="Repetir canción actual", value="song"),
        app_commands.Choice(name="Repetir toda la cola", value="queue"),
    ])
    async def loop_cmd(self, interaction: discord.Interaction, modo: app_commands.Choice[str]):
        player = self.music_manager.get_player(interaction.guild)
        player.loop_mode = modo.value
        await interaction.response.send_message(f"🔁 Modo de repetición: **{modo.name}**", ephemeral=False)

    @app_commands.command(name="shuffle", description="Mezcla aleatoriamente las canciones en la cola")
    async def shuffle_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        if len(player.queue) < 2:
            return await interaction.response.send_message("❌ Se necesitan al menos 2 canciones en la cola para mezclar.", ephemeral=True)

        temp_list = list(player.queue)
        random.shuffle(temp_list)
        player.queue.clear()
        player.queue.extend(temp_list)

        await interaction.response.send_message("🔀 **¡Cola de reproducción mezclada aleatoriamente!**")

    @app_commands.command(name="clear", description="Vacía la lista de canciones en espera")
    async def clear_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        total = len(player.queue)
        player.queue.clear()
        await interaction.response.send_message(f"🗑️ Se han eliminado **{total}** canciones de la cola.")

    @app_commands.command(name="leave", description="Desconecta el bot del canal de voz")
    async def leave_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        if not player.voice_client or not player.voice_client.is_connected():
            return await interaction.response.send_message("❌ No estoy conectado a ningún canal.", ephemeral=True)

        await player.cleanup()
        await interaction.response.send_message("👋 **Desconectado del canal de voz.** ¡Hasta luego!")

    # ==========================================
    # COMANDOS DE FILTROS Y EFECTOS DJ
    # ==========================================
    @app_commands.command(name="filtro", description="Aplica efectos de sonido DJ en tiempo real a la música")
    @app_commands.choices(efecto=[
        app_commands.Choice(name="Desactivar (Sonido Normal)", value="off"),
        app_commands.Choice(name="Bass Boost (Bajos Potentes) 🔊", value="bassboost"),
        app_commands.Choice(name="Bass Boost Extremo 💥", value="bassboost_extreme"),
        app_commands.Choice(name="Nightcore (Acelerado + Tono Alto) ⚡", value="nightcore"),
        app_commands.Choice(name="Vaporwave (Lento + Relajante) 🌊", value="vaporwave"),
        app_commands.Choice(name="Audio 8D (Efecto Envolvente 360°) 🎧", value="8d"),
    ])
    async def filtro_cmd(self, interaction: discord.Interaction, efecto: app_commands.Choice[str]):
        player = self.music_manager.get_player(interaction.guild)
        player.filter_mode = efecto.value
        
        embed = discord.Embed(
            title="🎛️ Efecto de Audio DJ Aplicado",
            description=f"El filtro se ha establecido en: **{efecto.name}**\n"
                        f"*(Se aplicará a la canción actual y a las siguientes de la cola)*",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="bassboost", description="Potencia los bajos y frecuencias graves al máximo")
    async def bassboost_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        player.filter_mode = "bassboost"
        embed = discord.Embed(
            title="🔊 Bass Boost Activado",
            description="¡Graves aumentados al máximo! Siente el impacto del bajo.",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="nightcore", description="Activa el modo Nightcore (más rápido y tono agudo)")
    async def nightcore_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        player.filter_mode = "nightcore"
        embed = discord.Embed(
            title="⚡ Modo Nightcore Activado",
            description="Velocidad y tono aumentados al estilo Nightcore remix.",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="vaporwave", description="Activa el modo Vaporwave (ralentizado y relajante)")
    async def vaporwave_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        player.filter_mode = "vaporwave"
        embed = discord.Embed(
            title="🌊 Modo Vaporwave Activado",
            description="Música ralentizada y relajante con estética retro.",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="audio8d", description="Activa el efecto envolvente 8D (gira entre auriculares)")
    async def audio8d_cmd(self, interaction: discord.Interaction):
        player = self.music_manager.get_player(interaction.guild)
        player.filter_mode = "8d"
        embed = discord.Embed(
            title="🎧 Efecto 8D Activado",
            description="¡Ponte auriculares! El sonido rotará en 360° de oreja a oreja.",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot, music_manager: MusicManager):
    await bot.add_cog(Music(bot, music_manager))
