"""
Cog de Bienvenidas y Despedidas Profesionales
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import json
import os
import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_SUCCESS, COLOR_ERROR, COLOR_PRIMARY, BOT_NAME, CREATOR_NAME
from utils.welcome_card import generate_welcome_card

SETTINGS_FILE = "data/welcome_settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error cargando welcome_settings: {e}")
    return {}

def save_settings(data):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

class Welcomer(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = load_settings()

    def get_guild_settings(self, guild_id: int):
        # Configuración por defecto vinculada al servidor de Rafa si no existe otra
        g_id = str(guild_id)
        if g_id not in self.settings:
            self.settings[g_id] = {
                "welcome_channel_id": 1538269422190592052 if guild_id == 1538269421020258304 else None,
                "goodbye_channel_id": 1538269422190592052 if guild_id == 1538269421020258304 else None,
                "welcome_enabled": True,
                "goodbye_enabled": True
            }
            save_settings(self.settings)
        return self.settings[g_id]

    # ==========================================
    # EVENTO DE BIENVENIDA (ON_MEMBER_JOIN)
    # ==========================================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        cfg = self.get_guild_settings(member.guild.id)
        if not cfg.get("welcome_enabled", True):
            return

        channel_id = cfg.get("welcome_channel_id")
        if not channel_id:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        try:
            # Generar tarjeta personalizada
            avatar_url = member.display_avatar.with_format("png").url
            card_buf = await generate_welcome_card(
                member_name=member.display_name,
                server_name=member.guild.name,
                member_count=member.guild.member_count,
                avatar_url=avatar_url,
                is_welcome=True
            )
            file = discord.File(fp=card_buf, filename="welcome.png")

            embed = discord.Embed(
                title=f"✨ ¡Bienvenido/a a {member.guild.name}! ✨",
                description=(
                    f"👋 ¡Hola {member.mention}!\n\n"
                    f"👤 **Usuario:** `{member.name}`\n"
                    f"👑 **Creador Oficial:** `{CREATOR_NAME}`\n"
                    f"📜 Por favor revisa las reglas en <#1542056244993466389>.\n"
                    f"🎉 ¡Eres el miembro número **#{member.guild.member_count}**!\n\n"
                    f"✨ ¡Esperamos que disfrutes tu estancia al máximo!"
                ),
                color=COLOR_SUCCESS
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_image(url="attachment://welcome.png")
            embed.set_footer(
                text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )

            await channel.send(content=f"🎉 ¡Un nuevo miembro ha llegado! {member.mention}", embed=embed, file=file)
            print(f"✅ Bienvenida enviada para {member.name} en #{channel.name}")
        except Exception as e:
            print(f"❌ Error al enviar bienvenida para {member.name}: {e}")

    # ==========================================
    # EVENTO DE DESPEDIDA (ON_MEMBER_REMOVE)
    # ==========================================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return

        cfg = self.get_guild_settings(member.guild.id)
        if not cfg.get("goodbye_enabled", True):
            return

        channel_id = cfg.get("goodbye_channel_id")
        if not channel_id:
            return

        channel = member.guild.get_channel(channel_id)
        if not channel or not isinstance(channel, discord.TextChannel):
            return

        try:
            avatar_url = member.display_avatar.with_format("png").url
            card_buf = await generate_welcome_card(
                member_name=member.display_name,
                server_name=member.guild.name,
                member_count=member.guild.member_count,
                avatar_url=avatar_url,
                is_welcome=False
            )
            file = discord.File(fp=card_buf, filename="goodbye.png")

            embed = discord.Embed(
                title="👋 ¡Hasta Pronto! 👋",
                description=(
                    f"👤 **Usuario:** `{member.name}` ({member.mention})\n\n"
                    f"Ha dejado la comunidad de **{member.guild.name}**.\n"
                    f"Le deseamos lo mejor y esperamos volver a verlo pronto.\n\n"
                    f"👥 Ahora quedamos **{member.guild.member_count} miembros** en el servidor."
                ),
                color=COLOR_ERROR
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_image(url="attachment://goodbye.png")
            embed.set_footer(
                text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}",
                icon_url=self.bot.user.display_avatar.url if self.bot.user else None
            )

            await channel.send(embed=embed, file=file)
            print(f"👋 Despedida enviada para {member.name} en #{channel.name}")
        except Exception as e:
            print(f"❌ Error al enviar despedida para {member.name}: {e}")

    # ==========================================
    # COMANDOS DE PRUEBA Y CONFIGURACIÓN
    # ==========================================
    @app_commands.command(name="test_bienvenida", description="Envía una tarjeta de prueba de bienvenida al canal configurado")
    async def test_bienvenida_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        cfg = self.get_guild_settings(interaction.guild.id)
        channel_id = cfg.get("welcome_channel_id") or interaction.channel.id
        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return await interaction.followup.send("❌ No se encontró el canal de bienvenida.", ephemeral=True)

        card_buf = await generate_welcome_card(
            member_name=interaction.user.display_name,
            server_name=interaction.guild.name,
            member_count=interaction.guild.member_count,
            avatar_url=interaction.user.display_avatar.with_format("png").url,
            is_welcome=True
        )
        file = discord.File(fp=card_buf, filename="welcome.png")

        embed = discord.Embed(
            title=f"✨ ¡Bienvenido/a a {interaction.guild.name}! ✨",
            description=(
                f"👋 ¡Hola {interaction.user.mention}! Te damos una cálida bienvenida a nuestro servidor.\n\n"
                f"👤 **Usuario:** `{interaction.user.name}`\n"
                f"👑 **Creador Oficial:** `{CREATOR_NAME}`\n"
                f"📜 Por favor revisa las reglas y los canales de información.\n"
                f"🎉 ¡Eres el miembro número **#{interaction.guild.member_count}**!\n\n"
                f"✨ ¡Esperamos que disfrutes tu estancia al máximo!"
            ),
            color=COLOR_SUCCESS
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url="attachment://welcome.png")
        embed.set_footer(
            text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        await channel.send(content=f"🎉 ¡Demostración de bienvenida! {interaction.user.mention}", embed=embed, file=file)
        await interaction.followup.send(f"✅ ¡Tarjeta de bienvenida de prueba enviada con éxito a {channel.mention}!", ephemeral=True)

    @app_commands.command(name="test_despedida", description="Envía una tarjeta de prueba de despedida al canal configurado")
    async def test_despedida_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        cfg = self.get_guild_settings(interaction.guild.id)
        channel_id = cfg.get("goodbye_channel_id") or interaction.channel.id
        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return await interaction.followup.send("❌ No se encontró el canal de despedida.", ephemeral=True)

        card_buf = await generate_welcome_card(
            member_name=interaction.user.display_name,
            server_name=interaction.guild.name,
            member_count=interaction.guild.member_count,
            avatar_url=interaction.user.display_avatar.with_format("png").url,
            is_welcome=False
        )
        file = discord.File(fp=card_buf, filename="goodbye.png")

        embed = discord.Embed(
            title="👋 ¡Hasta Pronto! 👋",
            description=(
                f"👤 **Usuario:** `{interaction.user.name}` ({interaction.user.mention})\n\n"
                f"Ha dejado la comunidad de **{interaction.guild.name}**.\n"
                f"Le deseamos lo mejor y esperamos volver a verlo pronto.\n\n"
                f"👥 Ahora quedamos **{interaction.guild.member_count} miembros** en la comunidad."
            ),
            color=COLOR_ERROR
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_image(url="attachment://goodbye.png")
        embed.set_footer(
            text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        await channel.send(embed=embed, file=file)
        await interaction.followup.send(f"✅ ¡Tarjeta de despedida de prueba enviada con éxito a {channel.mention}!", ephemeral=True)

    @app_commands.command(name="set_bienvenida", description="Configura el canal para los mensajes y tarjetas de bienvenida")
    @app_commands.describe(canal="Canal de texto donde se enviarán las bienvenidas")
    async def set_bienvenida_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel):
        cfg = self.get_guild_settings(interaction.guild.id)
        cfg["welcome_channel_id"] = canal.id
        cfg["welcome_enabled"] = True
        save_settings(self.settings)

        embed = discord.Embed(
            title="✅ Canal de Bienvenida Configurado",
            description=f"Las tarjetas de bienvenida se enviarán automáticamente a {canal.mention}.",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="set_despedida", description="Configura el canal para los mensajes y tarjetas de despedida")
    @app_commands.describe(canal="Canal de texto donde se enviarán las despedidas")
    async def set_despedida_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel):
        cfg = self.get_guild_settings(interaction.guild.id)
        cfg["goodbye_channel_id"] = canal.id
        cfg["goodbye_enabled"] = True
        save_settings(self.settings)

        embed = discord.Embed(
            title="✅ Canal de Despedida Configurado",
            description=f"Las tarjetas de despedida se enviarán automáticamente a {canal.mention}.",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcomer(bot))
