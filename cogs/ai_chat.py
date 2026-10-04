"""
Cog de Inteligencia Artificial (Rafa AI) - Modo Completo & Generador de Fotos
Rafa Music Pro - Creado y Desarrollado por RafaModzYT King of c+++
"""

import asyncio
import io
import random
import re
import urllib.parse
from collections import deque
from typing import Dict, List, Optional
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME
from g4f.client import Client

AI_CHANNEL_ID = 1556123788788371556

SYSTEM_PROMPT = (
    f"Eres Rafa AI, la Inteligencia Artificial oficial y más avanzada de la comunidad RAFA PANEL, "
    f"creada y desarrollada con orgullo por el programador {CREATOR_NAME}.\n\n"
    f"DIRECTIVAS FUNDAMENTALES:\n"
    f"1. CREACIÓN DE PROYECTOS Y CÓDIGO: Si el usuario te pide un proyecto o código (en C++, Python, C#, JavaScript, Lua, HTML/CSS, etc.), "
    f"desarróllalo COMPLETO, funcional, sin saltarte partes con '...aquí va el resto...'. Incluye bibliotecas/includes (#include), funciones completas, "
    f"manejo de errores, comentarios detallados y explicación de cómo compilarlo o ejecutarlo paso a paso.\n"
    f"2. DISEÑO Y SOFTWARE: Eres experta en interfaces ImGui, diseño de menús visuales, arquitectura de software y optimización.\n"
    f"3. ASISTENCIA TOTAL: Estás programada para ayudar al usuario en TODO lo que te pida: tareas, scripts, redacción, ideas, "
    f"resolución de dudas, tutoriales, cálculos y explicaciones.\n"
    f"4. IDIOMA Y ESTILO: Responde siempre en español con formato Markdown elegante (bloques de código, negritas, listas), "
    f"mostrando amabilidad, respeto y orgullo por ser la IA oficial de {CREATOR_NAME}."
)

IMAGE_TRIGGERS = [
    "dibuja", "haz una foto", "haz una imagen", "crea una foto", "crea una imagen",
    "genera una foto", "genera una imagen", "hazme una foto", "hazme una imagen",
    "dame una foto", "dame una imagen", "dibuja una", "dibuja un", "foto de",
    "imagen de", "draw", "generate an image", "create an image", "make an image",
    "renderiza", "crea un logo", "haz un logo", "hazme un logo"
]

def is_image_request(text: str) -> bool:
    """Detecta si el mensaje es una petición de imagen artística o foto con IA."""
    t = text.lower().strip()
    return any(p in t for p in IMAGE_TRIGGERS)

def extract_image_prompt(text: str) -> str:
    """Limpia el texto para dejar solo la descripción visual de la imagen."""
    t = text.strip()
    lower_t = t.lower()
    for trig in IMAGE_TRIGGERS:
        if lower_t.startswith(trig):
            cleaned = t[len(trig):].strip()
            if cleaned.lower().startswith("de "):
                cleaned = cleaned[3:].strip()
            elif cleaned.lower().startswith("un ") or cleaned.lower().startswith("una "):
                cleaned = cleaned[4:].strip()
            if cleaned.startswith(":"):
                cleaned = cleaned[1:].strip()
            if cleaned:
                return cleaned
    return t

async def generate_ai_image(prompt: str) -> Optional[io.BytesIO]:
    """Genera una imagen con IA en alta resolución (1024x1024)."""
    encoded = urllib.parse.quote(prompt.strip())
    seed = random.randint(1000, 9999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Referer': 'https://pollinations.ai/'
    }
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=35)) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    return io.BytesIO(data)
    except Exception as e:
        print(f"Error generando imagen IA: {e}")
    return None

async def _keep_typing(channel, stop_event: asyncio.Event):
    """Mantiene el estado 'Escribiendo...' activo continuamente mientras la IA procesa."""
    while not stop_event.is_set():
        try:
            await channel.typing()
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=6.0)
        except asyncio.TimeoutError:
            pass

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
        """Divide mensajes largos y extrae proyectos de código para adjuntarlos como archivo descargable."""
        # Detectar si hay bloques de código grandes para adjuntar archivo
        file_attachment = None
        code_match = re.search(r"```(cpp|c\+\+|c|python|py|cs|csharp|js|javascript|html|lua)?\s*\n([\s\S]{300,})\n```", content)
        if code_match:
            lang = (code_match.group(1) or "txt").lower()
            code_text = code_match.group(2)
            ext_map = {"cpp": "cpp", "c++": "cpp", "c": "c", "python": "py", "py": "py", "cs": "cs", "csharp": "cs", "js": "js", "html": "html", "lua": "lua"}
            ext = ext_map.get(lang, "txt")
            buf = io.BytesIO(code_text.encode('utf-8'))
            file_attachment = discord.File(fp=buf, filename=f"proyecto_{lang}.{ext}")

        if len(content) <= 1990:
            if reply_to:
                return await reply_to.reply(content, file=file_attachment, mention_author=False)
            return await target.send(content, file=file_attachment)

        # Dividir mensajes largos
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
            # Enviar el archivo adjunto en el último mensaje
            att = file_attachment if i == len(chunks) - 1 else None
            if i == 0 and reply_to:
                await reply_to.reply(chunk, mention_author=False)
            else:
                await target.send(chunk, file=att)

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

        # Solo responder si es el canal de IA o si etiquetaron al bot
        if not is_ai_channel and not is_mentioned:
            return

        content = message.content.strip()

        # Si el bot fue mencionado, limpiar la mención para que la IA procese la pregunta limpia
        if is_mentioned and self.bot.user:
            content = content.replace(f"<@{self.bot.user.id}>", "").replace(f"<@!{self.bot.user.id}>", "").strip()

        # Ignorar comandos con prefijo para no chocar
        if content.startswith("!") or content.startswith("/"):
            return

        if not content:
            return

        # Iniciar indicador continuo de "Escribiendo..."
        stop_typing = asyncio.Event()
        typing_task = asyncio.create_task(_keep_typing(message.channel, stop_typing))

        try:
            # 1. Comprobar si es una petición de imagen/foto
            if is_image_request(content):
                prompt = extract_image_prompt(content)
                img_buf = await generate_ai_image(prompt)
                if img_buf:
                    file = discord.File(fp=img_buf, filename="rafa_ai_art.png")
                    embed = discord.Embed(
                        title="🎨 Imagen Generada con Éxito",
                        description=f"Prompt: **{prompt}**\n👤 Solicitado por: {message.author.mention}",
                        color=COLOR_SUCCESS
                    )
                    embed.set_image(url="attachment://rafa_ai_art.png")
                    embed.set_footer(text=f"{BOT_NAME} • Generador de Imágenes IA de {CREATOR_NAME}")
                    await message.reply(embed=embed, file=file, mention_author=False)
                    return
                else:
                    await message.reply("⚠️ Hubo una demora con el motor de imágenes. Generando respuesta en texto...", mention_author=False)

            # 2. Generación de texto / código / proyecto completo
            loop = asyncio.get_event_loop()
            reply = await loop.run_in_executor(
                None,
                self._generate_response,
                message.author.id,
                content
            )
            await self._send_long_message(message.channel, reply, reply_to=message)

        finally:
            stop_typing.set()
            typing_task.cancel()

    # ==========================================
    # COMANDOS DE BARRA DIAGONAL (SLASH)
    # ==========================================
    @app_commands.command(name="ia", description="Haz una pregunta o consulta a Rafa AI")
    @app_commands.describe(pregunta="Escribe lo que deseas pedirle a la inteligencia artificial")
    async def slash_ia(self, interaction: discord.Interaction, pregunta: str):
        await interaction.response.defer(thinking=True)

        # Comprobar si pide una imagen
        if is_image_request(pregunta):
            prompt = extract_image_prompt(pregunta)
            img_buf = await generate_ai_image(prompt)
            if img_buf:
                file = discord.File(fp=img_buf, filename="rafa_ai_art.png")
                embed = discord.Embed(
                    title="🎨 Imagen Generada con Éxito",
                    description=f"Prompt: **{prompt}**\n👤 Solicitado por: {interaction.user.mention}",
                    color=COLOR_SUCCESS
                )
                embed.set_image(url="attachment://rafa_ai_art.png")
                embed.set_footer(text=f"{BOT_NAME} • Generador de Imágenes de {CREATOR_NAME}")
                return await interaction.followup.send(embed=embed, file=file)

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

    @app_commands.command(name="imagen", description="Genera una foto o ilustración artística con Inteligencia Artificial")
    @app_commands.describe(descripcion="Describe detalladamente qué quieres en la imagen")
    async def slash_imagen(self, interaction: discord.Interaction, descripcion: str):
        await interaction.response.defer(thinking=True)

        img_buf = await generate_ai_image(descripcion)
        if not img_buf:
            return await interaction.followup.send("❌ No se pudo generar la imagen en este momento. Por favor intenta con otra descripción.", ephemeral=True)

        file = discord.File(fp=img_buf, filename="imagen_ia.png")
        embed = discord.Embed(
            title="🎨 Imagen Generada por Inteligencia Artificial",
            description=f"✨ **Descripción:** `{descripcion}`\n👤 **Creada por:** {interaction.user.mention}",
            color=COLOR_PRIMARY
        )
        embed.set_image(url="attachment://imagen_ia.png")
        embed.set_footer(text=f"{BOT_NAME} • Generador IA de {CREATOR_NAME}")

        await interaction.followup.send(embed=embed, file=file)

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

async def setup(bot: commands.Bot):
    await bot.add_cog(AIChat(bot))
