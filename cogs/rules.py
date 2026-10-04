"""
Cog de Reglamento Oficial de la Comunidad
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, button
from config import COLOR_PRIMARY, COLOR_SUCCESS, BOT_NAME, CREATOR_NAME

RULES_CHANNEL_ID = 1542056244993466389

class RulesAcceptView(View):
    """Botón interactivo persistente para aceptar las reglas."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Aceptar Reglas & Verificarme", style=discord.ButtonStyle.success, emoji="✅", custom_id="btn_accept_rules")
    async def accept_rules(self, interaction: discord.Interaction, btn: Button):
        user = interaction.user
        guild = interaction.guild

        # Buscar si existe rol de verificado o miembro para asignarlo automáticamente
        role = discord.utils.find(lambda r: r.name.lower() in ["miembro", "verificado", "member", "usuarios", "verificados"], guild.roles)
        added_role_msg = ""
        if role and role not in user.roles:
            try:
                await user.add_roles(role, reason="Aceptó el reglamento oficial")
                added_role_msg = f"\n🎉 ¡Se te ha asignado el rol **{role.name}**!"
            except Exception as e:
                print(f"No se pudo asignar rol: {e}")

        await interaction.response.send_message(
            f"✨ ¡Muchas gracias {user.mention}! Has leído y aceptado el reglamento oficial de **{guild.name}**.{added_role_msg}\n"
            f"Disfruta de tu estancia en el servidor. 🚀",
            ephemeral=True
        )


class Rules(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Registrar vista persistente para que el botón funcione siempre
        self.bot.add_view(RulesAcceptView())

    @app_commands.command(name="publicar_reglas", description="Publica el reglamento oficial en el canal de reglas")
    @app_commands.describe(canal="Canal donde se publicará el reglamento (por defecto #reglas)")
    async def publicar_reglas_cmd(self, interaction: discord.Interaction, canal: discord.TextChannel = None):
        target_channel = canal or self.bot.get_channel(RULES_CHANNEL_ID) or interaction.channel

        embed = discord.Embed(
            title="📜 REGLAMENTO OFICIAL DE LA COMUNIDAD",
            description=(
                f"Bienvenido/a a **{interaction.guild.name}**.\n"
                f"Para mantener un ambiente agradable, seguro y ordenado, todos los miembros "
                f"deben cumplir obligatoriamente las siguientes normas:\n\n"
                f"👑 **Creador & Desarrollador Oficial:** `{CREATOR_NAME}`\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=COLOR_PRIMARY
        )

        embed.add_field(
            name="1️⃣ Respeto y Convivencia",
            value="Trata con respeto a todos los miembros y al equipo de administración. Están estrictamente prohibidos los insultos, el acoso, la discriminación y las conductas tóxicas.",
            inline=False
        )

        embed.add_field(
            name="2️⃣ Prohibido Spam y Flood",
            value="No envíes mensajes masivos, cadenas, menciones repetitivas ni publicidad de otros servidores o enlaces no autorizados por el chat o por mensaje directo.",
            inline=False
        )

        embed.add_field(
            name="3️⃣ Enlaces y Contenido Inapropiado",
            value="Queda terminantemente prohibido compartir virus, troyanos, software malicioso, enlaces phishing o contenido para adultos (NSFW).",
            inline=False
        )

        embed.add_field(
            name="4️⃣ Uso Correcto de Canales",
            value="Usa cada canal de texto y voz para lo que fue creado. Mantén los canales temáticos limpios y ordenados.",
            inline=False
        )

        embed.add_field(
            name="5️⃣ Canales de Música y Voz",
            value="No satures los comandos de música de Rafa Music Pro ni utilices distorsionadores de voz que molesten a otros usuarios.",
            inline=False
        )

        embed.add_field(
            name="6️⃣ Soporte y Compras Privadas",
            value="Para resolver cualquier problema, duda o compra, abre un ticket en <#1542056651022929971>. La administración nunca te pedirá contraseñas personales.",
            inline=False
        )

        embed.add_field(
            name="⚖️ Términos de Servicio de Discord",
            value="Se deben respetar todos los [Términos de Servicio de Discord](https://discord.com/terms) y las [Directrices de la Comunidad](https://discord.com/guidelines).",
            inline=False
        )

        embed.set_footer(
            text=f"{BOT_NAME} • Presiona el botón verde de abajo para aceptar las normas",
            icon_url=self.bot.user.display_avatar.url if self.bot.user else None
        )

        view = RulesAcceptView()
        await target_channel.send(embed=embed, view=view)
        await interaction.response.send_message(f"✅ Reglamento publicado con éxito en {target_channel.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Rules(bot))
