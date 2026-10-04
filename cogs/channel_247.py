"""
Cog de Modo 24/7 Permanente: /bot canal 24.7 y /desconect 24.7
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_PRIMARY, BOT_NAME, CREATOR_NAME
from utils.storage import storage
from utils.audio_player import MusicManager

class Channel247(commands.Cog):
    def __init__(self, bot: commands.Bot, music_manager: MusicManager):
        self.bot = bot
        self.music_manager = music_manager
        self.watchdog_247.start()

    def cog_unload(self):
        self.watchdog_247.cancel()

    # ==========================================
    # GRUPO DE COMANDOS SLASH: /bot canal_24_7 y /bot desconect_24_7
    # ==========================================
    cmd_bot = app_commands.Group(name="bot", description="Comandos de configuración y estado del bot Rafa Music Pro")

    @cmd_bot.command(name="canal_24_7", description="Activa el modo 24/7 en tu canal de voz o el seleccionado")
    @app_commands.describe(canal="Canal de voz a fijar 24/7 (opcional, por defecto tu canal actual)")
    async def slash_bot_canal_24_7(self, interaction: discord.Interaction, canal: discord.VoiceChannel = None):
        await self._activate_247(interaction, target_channel=canal)

    @cmd_bot.command(name="desconect_24_7", description="Desactiva el modo 24/7 y desconecta el bot del canal de voz")
    async def slash_bot_desconect_24_7(self, interaction: discord.Interaction):
        await self._deactivate_247(interaction)

    # ==========================================
    # COMANDOS SLASH DIRECTOS ALTERNATIVOS
    # ==========================================
    @app_commands.command(name="canal247", description="Activa el modo 24/7 en tu canal de voz o el seleccionado")
    @app_commands.describe(canal="Canal de voz a fijar 24/7 (opcional)")
    async def slash_canal247(self, interaction: discord.Interaction, canal: discord.VoiceChannel = None):
        await self._activate_247(interaction, target_channel=canal)

    @app_commands.command(name="desconect247", description="Desactiva el modo 24/7 y desconecta el bot")
    async def slash_desconect247(self, interaction: discord.Interaction):
        await self._deactivate_247(interaction)

    @app_commands.command(name="fijar_247", description="Fija un canal de voz 24/7 por ID o selección directa")
    @app_commands.describe(canal="Canal de voz que permanecerá activo 24/7")
    async def slash_fijar_247(self, interaction: discord.Interaction, canal: discord.VoiceChannel):
        await self._activate_247(interaction, target_channel=canal)

    # ==========================================
    # LÓGICA DE ACTIVACIÓN Y DESACTIVACIÓN 24/7
    # ==========================================
    async def _activate_247(self, interaction: discord.Interaction, target_channel: discord.VoiceChannel = None):
        voice_channel = target_channel
        if not voice_channel:
            if not interaction.user.voice or not interaction.user.voice.channel:
                embed = discord.Embed(
                    title="❌ Error",
                    description="Debes estar conectado a un canal de voz o especificar uno con el parámetro `canal`.",
                    color=COLOR_ERROR
                )
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            voice_channel = interaction.user.voice.channel

        guild = interaction.guild
        player = self.music_manager.get_player(guild)
        player.text_channel = interaction.channel

        # Conectar al canal si no lo está
        try:
            if not player.voice_client or not player.voice_client.is_connected():
                if guild.voice_client and guild.voice_client.is_connected():
                    player.voice_client = guild.voice_client
                    if player.voice_client.channel != voice_channel:
                        await player.voice_client.move_to(voice_channel)
                else:
                    player.voice_client = await voice_channel.connect(timeout=20.0, reconnect=True)
            elif player.voice_client.channel != voice_channel:
                await player.voice_client.move_to(voice_channel)
        except Exception as e:
            print(f"Error conectando a voz 24/7: {e}")

        # Cancelar cualquier desconexión por inactividad
        player.cancel_inactivity_timer()

        # Guardar en base de datos persistente
        await storage.set_247(guild.id, voice_channel.id, interaction.channel_id)

        embed = discord.Embed(
            title="🛡️ ¡Modo 24/7 Permanente Activado!",
            description=(
                f"🔊 **Canal fijado:** {voice_channel.mention} (`{voice_channel.name}`)\n"
                f"📌 **Estado:** El bot permanecerá activo en este canal **las 24 horas del día, los 7 días de la semana**.\n"
                f"⚡ **Auto-Reconexión:** Activada. Si el bot se desconecta o alguien lo expulsa, el sistema Guardián lo reconectará en segundos automáticamente.\n"
                f"🚫 **Auto-desconexión:** Desactivada por completo.\n\n"
                f"💡 *Para desactivarlo y desconectar el bot usa:* `/desconect 24.7` o `/bot desconect_24_7`"
            ),
            color=COLOR_SUCCESS
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    async def _deactivate_247(self, interaction: discord.Interaction):
        guild = interaction.guild
        player = self.music_manager.get_player(guild)

        if not storage.is_247(guild.id):
            embed = discord.Embed(
                description="ℹ️ **El modo 24/7 no estaba activado** en este servidor.",
                color=COLOR_PRIMARY
            )
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Eliminar de almacenamiento persistente
        await storage.remove_247(guild.id)

        # Desconectar el bot
        await player.cleanup()

        embed = discord.Embed(
            title="🔌 ¡Modo 24/7 Desactivado!",
            description=(
                "✅ Se ha desactivado el modo 24/7.\n"
                "👋 **El bot ha sido desconectado del canal de voz.**\n\n"
                "💡 *Puedes volver a activarlo en cualquier momento con:* `/bot canal 24.7`"
            ),
            color=COLOR_ERROR
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    # ==========================================
    # WATCHDOG GUARDIÁN 24/7 (RECONEXIÓN AUTOMÁTICA)
    # Revisa cada 15 segundos que el bot esté en su canal
    # ==========================================
    @tasks.loop(seconds=15)
    async def watchdog_247(self):
        """Monitorea continuamente todos los servidores 24/7 y los reconecta si es necesario."""
        all_247 = storage.get_all_247()
        if not all_247:
            return

        for guild_id_str, info in all_247.items():
            try:
                guild_id = int(guild_id_str)
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                vc_id = info.get("voice_channel_id")
                if not vc_id:
                    continue

                channel = guild.get_channel(vc_id)
                if not channel or not isinstance(channel, discord.VoiceChannel):
                    continue

                player = self.music_manager.get_player(guild)
                vc = player.voice_client or guild.voice_client

                # Si no está conectado
                if not vc or not vc.is_connected():
                    try:
                        player.voice_client = await channel.connect(timeout=15.0, reconnect=True)
                        player.cancel_inactivity_timer()
                        print(f"🛡️ [24/7 Guardián] Reconectado exitosamente a #{channel.name} en '{guild.name}'")
                    except discord.ClientException:
                        if guild.voice_client:
                            player.voice_client = guild.voice_client
                        else:
                            await player.cleanup()
                            player.voice_client = await channel.connect(timeout=15.0, reconnect=True)
                elif vc.channel.id != vc_id:
                    # Si fue movido a otro canal distinto al fijado 24/7
                    print(f"🛡️ [24/7 Guardián] Regresando al canal fijado #{channel.name}...")
                    await vc.move_to(channel)
            except Exception as e:
                pass

    @watchdog_247.before_loop
    async def before_watchdog(self):
        await self.bot.wait_until_ready()

    # ==========================================
    # LISTENER ON_VOICE_STATE_UPDATE
    # Detección instantánea si expulsan al bot
    # ==========================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not self.bot.user or member.id != self.bot.user.id:
            return

        # Si el bot fue desconectado de un canal
        if after.channel is None and storage.is_247(member.guild.id):
            cfg = storage.get_247(member.guild.id)
            if cfg and cfg.get("voice_channel_id"):
                target_vc = member.guild.get_channel(cfg["voice_channel_id"])
                if target_vc and isinstance(target_vc, discord.VoiceChannel):
                    print(f"⚠️ [24/7 Guardián] Bot desconectado de voz. Reconectando en 2 segundos a #{target_vc.name}...")
                    await asyncio.sleep(2)
                    player = self.music_manager.get_player(member.guild)
                    try:
                        if not player.voice_client or not player.voice_client.is_connected():
                            player.voice_client = await target_vc.connect(timeout=15.0, reconnect=True)
                            player.cancel_inactivity_timer()
                    except Exception as e:
                        print(f"Error en reconexión inmediata: {e}")

    # ==========================================
    # LISTENER PARA TEXTO DIRECTO (ej: /bot canal 24.7 o !bot canal 24.7)
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip().lower()

        is_activate = content in [
            "/bot canal 24.7", "!bot canal 24.7", "bot canal 24.7",
            "/bot canal 24/7", "!bot canal 24/7",
            "!247", "/247 on", "!247 on"
        ]

        is_deactivate = content in [
            "/desconect 24.7", "!desconect 24.7", "desconect 24.7",
            "/desconectar 24.7", "!desconectar 24.7",
            "/desconect 24/7", "!desconect 24/7",
            "/247 off", "!247 off"
        ]

        if is_activate:
            if not message.author.voice or not message.author.voice.channel:
                embed = discord.Embed(
                    description="❌ **Debes estar en un canal de voz** para activar el modo 24/7.",
                    color=COLOR_ERROR
                )
                return await message.reply(embed=embed)

            voice_channel = message.author.voice.channel
            player = self.music_manager.get_player(message.guild)
            player.text_channel = message.channel

            if not player.voice_client or not player.voice_client.is_connected():
                player.voice_client = await voice_channel.connect(timeout=20.0, reconnect=True)
            elif player.voice_client.channel != voice_channel:
                await player.voice_client.move_to(voice_channel)

            player.cancel_inactivity_timer()
            await storage.set_247(message.guild.id, voice_channel.id, message.channel.id)

            embed = discord.Embed(
                title="🛡️ ¡Modo 24/7 Activado!",
                description=(
                    f"🔊 **Canal fijado:** {voice_channel.mention}\n"
                    f"📌 **Rafa Music Pro se quedará activado en el canal y nunca se saldrá.**\n\n"
                    f"💡 Para desactivarlo y desconectarlo, escribe: `/desconect 24.7`"
                ),
                color=COLOR_SUCCESS
            )
            embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
            return await message.reply(embed=embed)

        elif is_deactivate:
            player = self.music_manager.get_player(message.guild)
            await storage.remove_247(message.guild.id)
            await player.cleanup()

            embed = discord.Embed(
                title="🔌 ¡Modo 24/7 Desactivado!",
                description="👋 El bot ha salido del canal y el modo 24/7 se ha apagado.",
                color=COLOR_ERROR
            )
            embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
            return await message.reply(embed=embed)

    # ==========================================
    # RECONEXIÓN AUTOMÁTICA AL INICIAR EL BOT
    # ==========================================
    @commands.Cog.listener()
    async def on_ready(self):
        """Al iniciar el bot, reconecta a todos los canales 24/7 guardados."""
        all_247 = storage.get_all_247()
        if not all_247:
            return

        print(f"🔄 Reanudando {len(all_247)} conexiones 24/7...")
        for guild_id_str, info in all_247.items():
            try:
                guild_id = int(guild_id_str)
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                vc_id = info.get("voice_channel_id")
                channel = guild.get_channel(vc_id)
                if not channel or not isinstance(channel, discord.VoiceChannel):
                    continue

                player = self.music_manager.get_player(guild)
                if info.get("text_channel_id"):
                    player.text_channel = guild.get_channel(info["text_channel_id"])

                if not player.voice_client or not player.voice_client.is_connected():
                    player.voice_client = await channel.connect(timeout=20.0, reconnect=True)
                    player.cancel_inactivity_timer()
                    print(f"✅ Conectado a canal 24/7 en '{guild.name}' -> #{channel.name}")
            except Exception as e:
                print(f"⚠️ Error reconectando 24/7 en guild {guild_id_str}: {e}")

async def setup(bot: commands.Bot, music_manager: MusicManager):
    cog = Channel247(bot, music_manager)
    await bot.add_cog(cog)
