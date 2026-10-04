"""
Cog de Inteligencia Artificial (Rafa AI)
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import asyncio
from collections import deque
from typing import Dict, List
import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from g4f.client import Client

AI_CHANNEL_ID = 1556123788788371556

SYSTEM_PROMPT = (
    f"Eres Rafa AI, la Inteligencia Artificial oficial de la comunidad RAFA PANEL, "
    f"creada y desarrollada por el programador {CREATOR_NAME}.\n"
    f"Eres un asistente altamente inteligente, carismático, respetuoso y experto en: "
    f"programación en C++, Python, desarrollo de bots, arquitectura de software, "
    f"diseño de interfaces ImGui, optimización de videojuegos, servidores y tecnología en general.\n"
    f"Responde siempre en español de manera clara, concisa, útil y profesional. "
    f"Usa formato Markdown elegante (negritas, bloques de código, listas) cuando sea oportuno."
)

class AIChat(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.client = Client()
        # Historial de conversación por usuario: max 12 turnos recientes
        self.history: Dict[int, deque] = {}

    def _get_history(self, user_id: int) -> deque:
        if user_id not in self.history:
            self.history[user_id] = deque(maxlen=12)
        return self.history[user_id]

    def _generate_response(self, user_id: int, user_message: str) -> str:
        """Llamada síncrona a la API de IA ejecutada en un threadpool."""
        hist = self._get_history(user_id)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in hist:
            messages.append(item)
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages
            )
            reply = response.choices[0].message.content
            if not reply:
                reply = "No pude generar una respuesta en este momento. Por favor inténtalo de nuevo."

            # Guardar en memoria
            hist.append({"role": "user", "content": user_message})
            hist.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            print(f"Error generando respuesta de IA: {e}")
            return f"⚠️ Ocurrió un error al procesar tu consulta con la IA: `{e}`"

    async def _send_long_message(self, target, content: str, reply_to: discord.Message = None):
        """Divide mensajes largos mayores a 2000 caracteres de Discord."""
        if len(content) <= 1990:
            if reply_to:
                return await reply_to.reply(content, mention_author=False)
            return await target.send(content)

        # Dividir por párrafos o líneas
        chunks = []
        current = ""
        for line in content.split("\n"):
            if len(current) + len(line) + 1 > 1900:
                chunks.append(current)
                current = line + "\n"
            else:
                current += line + "\n"
        if current.strip():
            chunks.append(current)

        for i, chunk in enumerate(chunks):
            if i == 0 and reply_to:
                await reply_to.reply(chunk, mention_author=False)
            else:
                await target.send(chunk)

    # ==========================================
    # LISTENER AUTOMÁTICO EN EL CANAL DE IA Y MENCIONES
    # ==========================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar mensajes de bots o fuera de servidores
        if message.author.bot or not message.guild:
            return

        is_ai_channel = (message.channel.id == AI_CHANNEL_ID)
        is_mentioned = bool(self.bot.user and self.bot.user in message.mentions)

        # Responder si es el canal de IA o si el usuario etiquetó al bot
        if not is_ai_channel and not is_mentioned:
            return

        content = message.content.strip()

        # Si el bot fue mencionado, limpiar la mención del texto para procesar la pregunta limpia
        if is_mentioned and self.bot.user:
            content = content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()

        # Si se escribió en el canal de IA pero content viene vacío (porque falta Message Content Intent)
        if is_ai_channel and not content:
            embed = discord.Embed(
                title="⚠️ Discord requiere activar 'Message Content Intent'",
                description=(
                    "¡Hola! Para que pueda **leer tus mensajes automáticamente con solo escribir** (sin tener que etiquetarme con `@`):\n\n"
                    "👉 **Activa el interruptor en 5 segundos:**\n"
                    "1. Abre el enlace: [Discord Developer Portal](https://discord.com/developers/applications/1556114224449716264/bot)\n"
                    "2. Baja a la sección **Privileged Gateway Intents**.\n"
                    "3. Enciende los interruptores: **Message Content Intent** y **Server Members Intent**.\n"
                    "4. Guarda los cambios (**Save Changes**).\n\n"
                    "💡 *Mientras tanto, puedes hablarme mencionándome:* `@Rafa Music 24/7 tu pregunta` o usando `/ia [pregunta]`."
                ),
                color=COLOR_ERROR
            )
            embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
            try:
                await message.reply(embed=embed, mention_author=False)
            except Exception:
                pass
            return

        # Ignorar comandos con prefijo para no chocar
        if content.startswith("!") or content.startswith("/"):
            return

        async with message.channel.typing():
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(
                None,
                self._generate_response,
                message.author.id,
                content
            )
            await self._send_long_message(message.channel, reply, reply_to=message)

    # ==========================================
    # COMANDOS DE BARRA DIAGONAL (SLASH)
    # ==========================================
    @app_commands.command(name="ia", description="Haz una pregunta o consulta a Rafa AI")
    @app_commands.describe(pregunta="Escribe lo que deseas preguntar a la inteligencia artificial")
    async def slash_ia(self, interaction: discord.Interaction, pregunta: str):
        await interaction.response.defer(thinking=True)

        loop = asyncio.get_event_loop()
        reply = await loop.run_in_executor(
            None,
            self._generate_response,
            interaction.user.id,
            pregunta
        )

        if len(reply) <= 1990:
            await interaction.followup.send(f"💬 **Pregunta:** {pregunta}\n\n🤖 **Rafa AI:**\n{reply}")
        else:
            await interaction.followup.send(f"💬 **Pregunta:** {pregunta}\n\n🤖 **Rafa AI:**")
            await self._send_long_message(interaction.channel, reply)

    @app_commands.command(name="ia_limpiar", description="Reinicia tu historial de conversación con Rafa AI")
    async def slash_ia_limpiar(self, interaction: discord.Interaction):
        if interaction.user.id in self.history:
            self.history[interaction.user.id].clear()
        embed = discord.Embed(
            description="🧹 **Tu memoria y contexto con Rafa AI han sido reiniciados.**\n¡Puedes iniciar una nueva conversación limpia!",
            color=COLOR_SUCCESS
        )
        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="panel_ia", description="Publica el panel oficial de bienvenida en el canal de IA")
    async def slash_panel_ia(self, interaction: discord.Interaction):
        channel = self.bot.get_channel(AI_CHANNEL_ID) or interaction.channel

        embed = discord.Embed(
            title="🤖 RAFA AI • CENTRO DE INTELIGENCIA ARTIFICIAL",
            description=(
                f"✨ ¡Bienvenido/a al canal oficial de Inteligencia Artificial de **{interaction.guild.name}**! ✨\n\n"
                f"👑 **Creador & Desarrollador Oficial:**\n`{CREATOR_NAME}`\n\n"
                f"💬 **¿Cómo funciona?**\n"
                f"No necesitas usar comandos. **Simplemente escribe cualquier mensaje o pregunta en este chat** "
                f"y Rafa AI te responderá automáticamente en tiempo real.\n\n"
                f"🧠 **¿Qué le puedes pedir?**\n"
                f"• 💻 **Programación:** Código en C++, Python, C#, algoritmos, depuración de errores.\n"
                f"• 🎨 **Diseño ImGui & Software:** Estructura de interfaces gráficas, menús y proyectos.\n"
                f"• 📝 **Redacción & Explicaciones:** Textos, resúmenes, traducción y tutoriales paso a paso.\n"
                f"• 🌐 **Consultas Generales:** Cualquier duda técnica, gamer o cotidiana.\n\n"
                f"💡 *Para reiniciar tu memoria con el bot escribe:* `/ia_limpiar`\n\n"
                f"👇 **¡Escribe tu mensaje abajo para comenzar a chatear!**"
            ),
            color=0x00F0FF
        )
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text=f"{BOT_NAME} • Potenciado con Inteligencia Artificial")

        await channel.send(embed=embed)
        await interaction.response.send_message(f"✅ Panel de IA publicado con éxito en {channel.mention}!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
