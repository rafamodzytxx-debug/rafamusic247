"""
Sistema Profesional de Tickets y Compras Privadas
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import asyncio
import io
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, button, Select, select
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME

TICKET_CHANNEL_ID = 1542056651022929971
SERVER_ID = 1538269421020258304

PURCHASE_OPTIONS = [
    {
        "label": "Comprar Craker Tool",
        "value": "craker_tool",
        "desc": "Herramienta Cracker Tool exclusiva y potente",
        "emoji": "🛠️"
    },
    {
        "label": "Comprar TP y Fantasma",
        "value": "tp_fantasma",
        "desc": "Funciones de Teletransporte y Modo Fantasma",
        "emoji": "👻"
    },
    {
        "label": "Comprar un ImGui",
        "value": "imgui",
        "desc": "Interfaz gráfica ImGui personalizada y profesional",
        "emoji": "🎨"
    },
    {
        "label": "Comprar Proyecto",
        "value": "proyecto",
        "desc": "Código fuente y proyecto completo con soporte",
        "emoji": "💻"
    }
]


class TicketPurchaseSelect(Select):
    """Menú desplegable (combo) dentro del ticket para seleccionar compras."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label=opt["label"],
                value=opt["value"],
                description=opt["desc"],
                emoji=opt["emoji"]
            )
            for opt in PURCHASE_OPTIONS
        ]
        super().__init__(
            placeholder="🛒 Selecciona qué deseas comprar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_purchase_item"
        )

    async def callback(self, interaction: discord.Interaction):
        selected_val = self.values[0]
        selected_info = next((opt for opt in PURCHASE_OPTIONS if opt["value"] == selected_val), None)

        if not selected_info:
            return await interaction.response.send_message("❌ Opción no válida.", ephemeral=True)

        title = f"{selected_info['emoji']} {selected_info['label']}"
        desc = selected_info["desc"]

        embed = discord.Embed(
            title=f"🛒 Solicitud de Compra: {title}",
            description=(
                f"👤 **Cliente:** {interaction.user.mention} (`{interaction.user.name}`)\n"
                f"📦 **Producto Seleccionado:** **{title}**\n"
                f"ℹ️ **Detalle:** {desc}\n\n"
                f"👑 **Vendedor Oficial:** `{CREATOR_NAME}`\n\n"
                f"💬 **Instrucciones:**\n"
                f"Por favor indica abajo tus dudas, método de pago o detalles del pedido.\n"
                f"¡{CREATOR_NAME} te responderá aquí para concretar la compra!"
            ),
            color=COLOR_SUCCESS
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Tienda Oficial de {CREATOR_NAME}")

        await interaction.response.send_message(
            content=f"🔔 <@{interaction.guild.owner_id}> | ¡{interaction.user.mention} quiere **{title}**!",
            embed=embed
        )


class TicketControlView(View):
    """Controles dentro del canal privado de ticket: Combo de compra + Botones de cierre."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketPurchaseSelect())

    @button(label="Cerrar Ticket", style=discord.ButtonStyle.secondary, emoji="🔒", custom_id="btn_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, btn: Button):
        embed = discord.Embed(
            title="🔒 Ticket Cerrado",
            description=f"El ticket ha sido cerrado por {interaction.user.mention}.\n"
                        f"Puedes eliminar el canal con el botón rojo cuando termines.",
            color=COLOR_ERROR
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed)

    @button(label="Eliminar Ticket", style=discord.ButtonStyle.danger, emoji="🗑️", custom_id="btn_delete_ticket")
    async def delete_ticket(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_message("⚠️ El canal será eliminado en **5 segundos**...")
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason=f"Ticket eliminado por {interaction.user.name}")
        except Exception as e:
            print(f"Error eliminando canal de ticket: {e}")


class TicketPanelSelect(Select):
    """Combo de selección en el panel público de creación de tickets."""
    def __init__(self):
        options = [
            discord.SelectOption(
                label=opt["label"],
                value=opt["value"],
                description=opt["desc"],
                emoji=opt["emoji"]
            )
            for opt in PURCHASE_OPTIONS
        ]
        options.append(
            discord.SelectOption(
                label="Soporte General / Otra Consulta",
                value="general_support",
                description="Consultas generales o asistencia",
                emoji="📩"
            )
        )
        super().__init__(
            placeholder="🛒 Elige qué deseas comprar o consultar...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="select_panel_ticket"
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        selected_info = next((opt for opt in PURCHASE_OPTIONS if opt["value"] == choice), None)
        selected_product = selected_info["label"] if selected_info else "Soporte General"
        await create_private_ticket(interaction, selected_product=selected_product)


class TicketPanelView(View):
    """Vista pública permanente en el canal #🎫・crear-ticket."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketPanelSelect())

    @button(label="Abrir Ticket General", style=discord.ButtonStyle.success, emoji="📩", custom_id="btn_open_ticket")
    async def open_ticket_button(self, interaction: discord.Interaction, btn: Button):
        await create_private_ticket(interaction, selected_product=None)


async def create_private_ticket(interaction: discord.Interaction, selected_product: str = None):
    """Lógica unificada para crear canal de ticket 100% privado."""
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

    # Asignar nombre descriptivo según lo elegido
    clean_user = user.name.lower().replace(" ", "-")[:12]
    if selected_product and "Craker" in selected_product:
        channel_name = f"craker-{clean_user}"
    elif selected_product and "TP" in selected_product:
        channel_name = f"tp-{clean_user}"
    elif selected_product and "ImGui" in selected_product:
        channel_name = f"imgui-{clean_user}"
    elif selected_product and "Proyecto" in selected_product:
        channel_name = f"proyecto-{clean_user}"
    else:
        channel_name = f"ticket-{clean_user}"

    category = interaction.channel.category if interaction.channel else None

    ticket_channel = await guild.create_text_channel(
        name=channel_name,
        overwrites=overwrites,
        category=category,
        topic=f"ticket-user-{user.id}",
        reason=f"Ticket creado por {user.name}"
    )

    # Descripción adaptada
    product_text = f"\n📦 **Producto Solicitado Inicialmente:** **{selected_product}**\n" if selected_product else ""

    embed = discord.Embed(
        title="🎫 Ticket de Compra & Soporte Privado",
        description=(
            f"👋 ¡Hola {user.mention}! Bienvenido a tu canal privado de atención en **{guild.name}**.\n\n"
            f"👑 **Administración:** `{CREATOR_NAME}`{product_text}\n"
            f"🛒 **Opciones de Compra:**\n"
            f"Puedes usar el **menú desplegable (combo)** de abajo para elegir o cambiar el producto que deseas:\n"
            f"• 🛠️ **Comprar Craker Tool**\n"
            f"• 👻 **Comprar TP y Fantasma**\n"
            f"• 🎨 **Comprar un ImGui**\n"
            f"• 💻 **Comprar Proyecto**\n\n"
            f"📌 **Instrucciones:**\n"
            f"Describe los detalles de tu compra o consulta. ¡Un administrador te responderá a la brevedad!"
        ),
        color=COLOR_PRIMARY
    )
    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"{BOT_NAME} • Sistema de Tickets y Compras de {CREATOR_NAME}")

    view = TicketControlView()
    await ticket_channel.send(content=f"🔔 {user.mention} | <@{guild.owner_id}>", embed=embed, view=view)

    await interaction.followup.send(
        f"✅ ¡Tu ticket ha sido creado con éxito en {ticket_channel.mention}!",
        ephemeral=True
    )


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Registrar vistas persistentes para que no expiren nunca
        self.bot.add_view(TicketPanelView())
        self.bot.add_view(TicketControlView())

    @app_commands.command(name="panel_tickets", description="Publica el panel oficial de compras y tickets")
    @app_commands.describe(canal="Canal donde se publicará el panel (por defecto #crear-ticket)")
    async def panel_tickets_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        target_channel = canal or self.bot.get_channel(TICKET_CHANNEL_ID) or interaction.channel
        
        embed = discord.Embed(
            title="🛒 TIENDA OFICIAL & CENTRO DE TICKETS",
            description=(
                f"¡Bienvenido a la tienda y centro de pedidos de **{interaction.guild.name}**!\n\n"
                f"👑 **Creador & Desarrollador Oficial:**\n`{CREATOR_NAME}`\n\n"
                f"📦 **Productos Disponibles para Compra:**\n"
                f"🛠️ **Comprar Craker Tool**\n"
                f"👻 **Comprar TP y Fantasma**\n"
                f"🎨 **Comprar un ImGui**\n"
                f"💻 **Comprar Proyecto**\n\n"
                f"👇 **Selecciona una opción en el menú de abajo para abrir tu ticket privado:**"
            ),
            color=COLOR_SUCCESS
        )
        if interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        embed.set_footer(text=f"{BOT_NAME} • Tienda 24/7 de {CREATOR_NAME}")

        view = TicketPanelView()
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Panel de compras y tickets publicado en {target_channel.mention}!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
