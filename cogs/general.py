"""
Cog General: /creditos, /invitar, /help y /ping
Rafa Music Pro - Creado y Desarrollado por Rafa
"""

import os
import discord
from discord.ext import commands
from discord import app_commands
import time
from config import COLOR_PRIMARY, COLOR_SUCCESS, BOT_NAME, BOT_VERSION, CREATOR_NAME, CREATOR_CREDITS, get_invite_url
from utils.ui_components import InviteButtonView

SERVER_INVITE_CHANNEL_ID = 1542056297367871499
OFFICIAL_INVITE_URL = "https://discord.gg/s4uZ5Ju4Fv"

class ServerInviteView(discord.ui.View):
    def __init__(self, invite_url: str = OFFICIAL_INVITE_URL):
        super().__init__(timeout=None)
        self.add_item(discord.ui.Button(
            label="Entrar a RAFA PANEL",
            style=discord.ButtonStyle.link,
            url=invite_url,
            emoji="🚀"
        ))

    @discord.ui.button(label="Copiar Enlace", style=discord.ButtonStyle.primary, emoji="📋", custom_id="btn_copy_server_invite")
    async def copy_link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔗 **Enlace Oficial Permanente de RAFA PANEL:**\n>>> **{OFFICIAL_INVITE_URL}**\n\n¡Cópialo y compártelo donde gustes!",
            ephemeral=True
        )

START_TIME = time.time()

class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(ServerInviteView())

    @app_commands.command(name="creditos", description="Muestra la información oficial y créditos de Rafa Music Pro")
    async def creditos_cmd(self, interaction: discord.Interaction):
        """Muestra los créditos completos a Rafa."""
        embed = discord.Embed(
            title=f"⭐ Créditos Oficiales - {BOT_NAME}",
            description=(
                f"### 🎵 **{BOT_NAME} - {BOT_VERSION}**\n\n"
                f"{CREATOR_CREDITS}\n\n"
                f"📌 **Sobre este Bot:**\n"
                f"Diseñado para ofrecer una experiencia auditiva superior en Discord. "
                f"Cuenta con modo **24/7 permanente**, extracción de audio de alta tasa de bits, "
                f"búsqueda predictiva instantánea y controles táctiles mediante botones.\n\n"
                f"🌐 **¿Quieres tener a Rafa Music Pro en tu servidor?**\n"
                f"Puedes agregarlo fácilmente a cualquier servidor haciendo clic en el botón de abajo."
            ),
            color=COLOR_PRIMARY
        )

        # Estadísticas del bot
        total_guilds = len(self.bot.guilds)
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        uptime_seconds = int(time.time() - START_TIME)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, sec = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {sec}s"

        embed.add_field(name="🌐 Servidores", value=f"`{total_guilds}`", inline=True)
        embed.add_field(name="👥 Usuarios", value=f"`{total_users}`", inline=True)
        embed.add_field(name="⏱️ Tiempo activo", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="📶 Latencia", value=f"`{round(self.bot.latency * 1000)}ms`", inline=True)

        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"Rafa Music Pro • Proyecto Exclusivo de {CREATOR_NAME}")

        view = InviteButtonView(self.bot.user) if self.bot.user else None
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="invitar", description="Enlace para agregar Rafa Music Pro a cualquier servidor de Discord")
    async def invitar_cmd(self, interaction: discord.Interaction):
        """Genera el enlace para invitar el bot a cualquier servidor."""
        invite_url = get_invite_url(str(self.bot.user.id) if self.bot.user else None)
        
        embed = discord.Embed(
            title="🤖 Invita a Rafa Music Pro a tu Servidor",
            description=(
                f"¡Puedes agregar **{BOT_NAME}** a cualquier servidor donde tengas permisos!\n\n"
                f"🔗 **Enlace de Invitación:**\n[Haz clic aquí para invitar al bot]({invite_url})\n\n"
                f"✨ Disfruta de música ininterrumpida las 24 horas del día con la mejor fidelidad sonora."
            ),
            color=COLOR_SUCCESS
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")

        view = InviteButtonView(self.bot.user) if self.bot.user else None
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="help", description="Lista completa de comandos y guía de uso de Rafa Music Pro")
    async def help_cmd(self, interaction: discord.Interaction):
        """Menú de ayuda organizado por categorías."""
        embed = discord.Embed(
            title=f"📖 Guía de Comandos - {BOT_NAME}",
            description=(
                f"¡Bienvenido a **{BOT_NAME}**! Creado por **{CREATOR_NAME}**.\n"
                f"A continuación tienes la lista completa de comandos disponibles:\n"
            ),
            color=COLOR_PRIMARY
        )

        embed.add_field(
            name="🎵 Comandos de Música",
            value=(
                "🔹 `/join` - Conecta el bot a tu canal de voz.\n"
                "🔹 `/play [musica]` - Busca canciones o listas de reproducción (Playlists) con autocompletado en vivo.\n"
                "🔹 `/skip` - Salta la canción actual.\n"
                "🔹 `/pause` - Pausa la reproducción.\n"
                "🔹 `/resume` - Reanuda la reproducción.\n"
                "🔹 `/stop` - Detiene la música y limpia la cola.\n"
                "🔹 `/queue` - Muestra la lista de canciones en espera.\n"
                "🔹 `/nowplaying` - Muestra detalles de la canción en reproducción con botones.\n"
                "🔹 `/volume [1-150]` - Ajusta el volumen del reproductor.\n"
                "🔹 `/loop [modo]` - Configura modo de repetición (desactivado, canción, cola).\n"
                "🔹 `/shuffle` - Mezcla aleatoriamente las canciones de la cola.\n"
                "🔹 `/clear` - Limpia la cola de canciones.\n"
                "🔹 `/leave` - Desconecta el bot del canal."
            ),
            inline=False
        )

        embed.add_field(
            name="🎛️ Filtros y Efectos DJ",
            value=(
                "🔊 `/bassboost` - Graves aumentados al máximo.\n"
                "⚡ `/nightcore` - Modo acelerado y tono agudo estilo remix.\n"
                "🌊 `/vaporwave` - Modo ralentizado, relajante y nostálgico.\n"
                "🎧 `/audio8d` - Efecto 360° que rota entre tus auriculares.\n"
                "🎚️ `/filtro [efecto]` - Menú selector de todos los filtros."
            ),
            inline=False
        )

        embed.add_field(
            name="📻 Estaciones de Radio 24/7 en Vivo",
            value=(
                "☕ `/radio lofi` - Lofi Hip Hop Beats (Chill / Estudio).\n"
                "🔥 `/radio reggaeton` - Éxitos del género urbano sin cortes.\n"
                "🏎️ `/radio phonk` - Drift Phonk y graves pesados para jugar.\n"
                "⚡ `/radio electro` - Electrónica & EDM festival 24/7.\n"
                "🎸 `/radio rock` - Lo mejor del Rock clásico 80s/90s."
            ),
            inline=False
        )

        embed.add_field(
            name="🛡️ Modo 24/7 Permanente",
            value=(
                "🟢 `/bot canal_24_7` o texto `/bot canal 24.7` - Activa el bot 24/7 en tu canal (nunca se desconecta).\n"
                "🔴 `/bot desconect_24_7` o texto `/desconect 24.7` - Desactiva el modo 24/7 y desconecta el bot."
            ),
            inline=False
        )

        embed.add_field(
            name="ℹ️ Información y Servidores",
            value=(
                f"👑 `/creditos` - Información de {CREATOR_NAME} y estadísticas.\n"
                "➕ `/invitar` - Agrega el bot a cualquier servidor de Discord.\n"
                "📶 `/ping` - Comprueba la latencia del bot con Discord."
            ),
            inline=False
        )

        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        view = InviteButtonView(self.bot.user) if self.bot.user else None
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="ping", description="Comprueba la latencia de respuesta del bot")
    async def ping_cmd(self, interaction: discord.Interaction):
        latency_ms = round(self.bot.latency * 1000)
        embed = discord.Embed(
            description=f"🏓 **Pong!** Latencia de respuesta: `{latency_ms}ms`",
            color=COLOR_SUCCESS if latency_ms < 150 else COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Creado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="link_servidor", description="Publica el panel con el enlace oficial permanente de invitación al servidor")
    @app_commands.describe(canal="Canal donde se publicará el enlace (por defecto el canal de links)")
    async def link_servidor_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        target_channel = canal or self.bot.get_channel(SERVER_INVITE_CHANNEL_ID) or interaction.channel

        invite_url = OFFICIAL_INVITE_URL
        try:
            inv = await target_channel.create_invite(max_age=0, max_uses=0, reason="Enlace permanente oficial")
            invite_url = inv.url
        except Exception:
            pass

        embed = discord.Embed(
            title=f"🌐 ENLACE OFICIAL DE INVITACIÓN • {interaction.guild.name.upper()}",
            description=(
                f"✨ **¡Bienvenido/a a la comunidad oficial de {interaction.guild.name}!** ✨\n"
                f"👑 **Creador & Desarrollador Oficial:** `{CREATOR_NAME}`\n\n"
                f"📢 **¡Comparte nuestro servidor con todos tus amigos!**\n"
                f"Usa este enlace oficial permanente para invitar personas, compartirlo en redes sociales o en otros grupos:\n\n"
                f"🔗 **Enlace Oficial Permanente:**\n"
                f">>> **{invite_url}**\n\n"
                f"💎 **¿Qué encontrarás en nuestra comunidad?**\n"
                f"• 🎵 **Música 24/7:** Bot de música ininterrumpido en canales de voz con ecualizadores DJ exclusivos.\n"
                f"• 🛒 **Tienda Oficial:** Catálogo de Craker Tool, TP y Fantasma, ImGui personalizado y Proyectos completos.\n"
                f"• 🎫 **Atención y Soporte Privado 24/7:** Sistema de tickets con respuesta rápida del creador.\n"
                f"• 🛡️ **Comunidad Verificada y Segura:** Normas claras, sistema de bienvenida dinámico y ambiente gamer.\n\n"
                f"👇 **¡Haz clic en el botón de abajo para unirte o copiar el enlace!**"
            ),
            color=0x00F0FF
        )
        file = None
        if os.path.exists("assets/banner.png"):
            file = discord.File("assets/banner.png", filename="banner.png")
            embed.set_image(url="attachment://banner.png")
        embed.set_footer(text=f"{BOT_NAME} • Servidor Oficial de {CREATOR_NAME}")

        view = ServerInviteView(invite_url)
        if file:
            await target_channel.send(embed=embed, view=view, file=file)
        else:
            await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ ¡Enlace oficial publicado con éxito en {target_channel.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
