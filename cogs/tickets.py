"""
Sistema Profesional de Tickets de Soporte
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import asyncio
import io
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, button
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME

TICKET_CHANNEL_ID = 1542056651022929971
SERVER_ID = 1538269421020258304

class TicketControlView(View):
    """Botones de control dentro del canal privado de ticket."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Cerrar Ticket", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="btn_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, btn: Button):
        channel = interaction.channel
        embed = discord.Embed(
            title="🔒 Ticket Cerrado",
            description=f"El ticket ha sido cerrado por {interaction.user.mention}.\n"
                        f"Puedes guardar la transcripción o eliminarlo permanentemente.",
            color=COLOR_ERROR
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @button(label="Transcripción", style=discord.ButtonStyle.primary, emoji="📋", custom_id="btn_transcript_ticket")
    async def transcript_ticket(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(thinking=True)
        channel = interaction.channel
        
        # Recopilar historial de mensajes
        messages = []
        async for msg in channel.history(limit=200, oldest_first=True):
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            messages.append(f"[{time_str}] {msg.author.name}: {msg.content}")

        transcript_text = "\n".join(messages)
        buf = io.BytesIO(transcript_text.encode('utf-8'))
        file = discord.File(fp=buf, filename=f"transcripcion-{channel.name}.txt")

        embed = discord.Embed(
            title="📋 Transcripción del Ticket",
            description=f"Aquí tienes el registro completo de la conversación en {channel.mention}.",
            color=COLOR_PRIMARY
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.followup.send(embed=embed, file=file)

    @button(label="Eliminar Ticket", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="btn_delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_message("⚠️ El canal será eliminado en **5 segundos**...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket eliminado por {interaction.user.name}")
        except Exception as e:
            print(f"Error eliminando canal de ticket: {e}")


class TicketPanelView(View):
    """Vista con botón permanente en el canal de crear tickets."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Abrir Ticket", style=discord.ButtonStyle.success, emoji="📩", custom_id="btn_open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        user = interaction.user

        # Evitar tickets duplicados del mismo usuario
        existing = discord.utils.get(guild.text_channels, topic=f"ticket-user-{user.id}")
        if existing:
            return await interaction.response.send_message(
                f"⚠️ Ya tienes un ticket abierto actualmente en {existing.mention}.",
                ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)

        # Configurar permisos para que sea 100% privado
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                attach_files=True,
                embed_links=True,
                read_message_history=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True,
                send_messages=True,
                manage_channels=True,
                manage_messages=True
            )
        }

        channel_name = f"ticket-{user.name.lower().replace(' ', '-')[:15]}"
        
        # Buscar categoría de tickets si existe o crearlo en la actual
        category = interaction.channel.category if interaction.channel else None

        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=category,
            topic=f"ticket-user-{user.id}",
            reason=f"Ticket de soporte para {user.name}"
        )

        # Enviar mensaje inicial dentro del ticket privado
        embed = discord.Embed(
            title="🎫 Ticket de Soporte Privado",
            description=(
                f"👋 ¡Hola {user.mention}! Gracias por contactar al equipo de soporte de **{guild.name}**.\n\n"
                f"👑 **Administración:** `{CREATOR_NAME}`\n\n"
                f"📌 **Instrucciones:**\n"
                f"Por favor describe detalladamente tu consulta, duda o compra.\n"
                f"Un administrador te responderá lo antes posible.\n\n"
                f"⚙️ *Para gestionar este ticket, utiliza los botones de abajo:*",
            ),
            color=COLOR_PRIMARY
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Sistema de Tickets Oficial")

        view = TicketControlView()
        await ticket_channel.send(content=f"🔔 {user.mention} | <@&{guild.owner_id}>", embed=embed, view=view)

        await interaction.followup.send(
            f"✅ ¡Tu ticket privado ha sido creado con éxito en {ticket_channel.mention}!",
            ephemeral=True
        )


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Registrar vistas persistentes para que funcionen siempre tras reiniciar
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="panel_tickets", description="Publica el panel oficial de creación de tickets")
    @app_commands.describe(canal="Canal donde se publicará el panel (por defecto #crear-ticket)")
    async def panel_tickets_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        target_channel = canal or self.bot.get_channel(TICKET_CHANNEL_ID) or interaction.channel
        
        embed = discord.Embed(
            title="🎫 CENTRO DE TICKETS & ATENCIÓN AL CLIENTE",
            description=(
                f"¡Bienvenido al sistema de atención y tickets de **{interaction.guild.name}**!\n\n"
                f"👑 **Creador & Desarrollador Oficial:**\n`{CREATOR_NAME}`\n\n"
                f"💼 **¿Para qué puedes abrir un ticket?**\n"
                f"🔹 Soporte técnico o dudas sobre el servidor.\n"
                f"🔹 Consultas sobre compras, servicios y accesos.\n"
                f"🔹 Reporte de usuarios o problemas privados.\n\n"
                f"👇 **Haz clic en el botón verde para abrir tu canal privado:**"
            ),
            color=COLOR_SUCCESS
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"{BOT_NAME} • Sistema de Soporte 24/7 de {CREATOR_NAME}")

        view = TicketPanelView()
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Panel de tickets publicado en {target_channel.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
