"""
Rafa Music Pro - Bot Principal
Desarrollado y Creado por Rafa
"""

import asyncio
import os
import sys

# Asegurar codificación UTF-8 en consola de Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import discord
from discord.ext import commands
from discord import opus
import config
from utils.audio_player import MusicManager
from utils.storage import storage

# Asegurar carga de biblioteca Opus para audio de Discord
try:
    if not opus.is_loaded():
        opus._load_default()
    print("🔊 Biblioteca Opus cargada correctamente.")
except Exception as e:
    print(f"⚠️ Advertencia al cargar Opus: {e}")

def get_intents(enable_privileged: bool = True) -> discord.Intents:
    intents = discord.Intents.default()
    intents.voice_states = True
    intents.guilds = True
    if enable_privileged:
        intents.message_content = True
        intents.members = True
    return intents

class RafaMusicBot(commands.Bot):
    def __init__(self, intents: discord.Intents = None):
        super().__init__(
            command_prefix=["!", "/"],
            intents=intents or get_intents(True),
            help_command=None
        )
        self.music_manager = MusicManager(self)

    async def setup_hook(self):
        """Carga módulos y sincroniza comandos de barra diagonal (Slash Commands)."""
        print("⚙️ Cargando módulos de Rafa Music Pro...")
        
        # Cargar Cogs
        from cogs.general import setup as setup_general
        from cogs.music import setup as setup_music
        from cogs.channel_247 import setup as setup_247
        from cogs.radio import setup as setup_radio
        from cogs.welcomer import setup as setup_welcomer
        from cogs.tickets import setup as setup_tickets
        from cogs.rules import setup as setup_rules
        from cogs.ai_chat import setup as setup_ai

        await setup_general(self)
        await setup_music(self, self.music_manager)
        await setup_247(self, self.music_manager)
        await setup_radio(self, self.music_manager)
        await setup_welcomer(self)
        await setup_tickets(self)
        await setup_rules(self)
        await setup_ai(self)

        # Registrar vistas interactivas persistentes ANTES de conectar
        from cogs.tickets import TicketPanelView, TicketControlView
        from cogs.general import ServerInviteView
        from cogs.rules import RulesAcceptView

        self.add_view(TicketPanelView())
        self.add_view(TicketControlView())
        self.add_view(ServerInviteView())
        self.add_view(RulesAcceptView())
        print("🔘 Vistas persistentes de tickets, reglas e invitación registradas con éxito.")

        # Sincronizar en segundo plano para evitar bloqueos por rate limit de Discord
        async def sync_slash_tree():
            try:
                print("🔄 Sincronizando comandos de barra diagonal (/)...")
                synced = await self.tree.sync()
                print(f"✅ ¡{len(synced)} comandos slash sincronizados con éxito globalmente!")
            except Exception as e:
                print(f"⚠️ Nota de sincronización: {e}")

        self.loop.create_task(sync_slash_tree())

    async def on_ready(self):
        """Se ejecuta cuando el bot se conecta a Discord."""
        # Establecer presencia del bot
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name="RafaModzYT King of c+++ 👑 | /play"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)

        invite_url = config.get_invite_url(str(self.user.id))

        banner = rf"""
========================================================================
   ____             __          __  __           _         ____             
  / __ \____ _     / /___ _    / / / /_  _______(_)____   / __ \_________  
 / /_/ / __ `/____/ / __ `/   / /_/ / / / / ___/ / ___/  / /_/ / ___/ __ \ 
/ _, _/ /_/ /____/ / /_/ /   / __  / /_/ (__  ) / /__   / ____/ /  / /_/ / 
/_/ |_|\__,_/    /_/\__,_/   /_/ /_/\__,_/____/_/\___/  /_/   /_/   \____/  
========================================================================
👑 Creado y Desarrollado por: {config.CREATOR_NAME}
🤖 Bot Conectado como: {self.user.name} (ID: {self.user.id})
🌐 Servidores Activos: {len(self.guilds)}
🔗 Enlace para agregar a cualquier servidor:
{invite_url}
========================================================================
        """
        print(banner)

def main():
    token = config.DISCORD_TOKEN
    if not token or token == "TU_DISCORD_TOKEN_AQUI":
        print("\n" + "="*60)
        print("❌ ERROR: No se ha configurado el DISCORD_TOKEN en el archivo .env")
        print("Abre el archivo .env y coloca el Token de tu bot.")
        print("Ejemplo: DISCORD_TOKEN=OTk5MTIzNDU2...")
        print("="*60 + "\n")
        return

    try:
        bot = RafaMusicBot(intents=get_intents(enable_privileged=True))
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n" + "="*70)
        print("⚠️ AVISO: El Intent de 'Message Content' no está activado en Discord Portal.")
        print("Iniciando con intents estándar:")
        print("✅ Todos los comandos slash (/play, /join, /bot canal_24_7, /creditos) funcionarán al 100%.")
        print("💡 Para habilitar también comandos por texto sin barra, activa 'Message Content Intent'")
        print("   en: https://discord.com/developers/applications/ -> Bot -> Privileged Gateway Intents")
        print("="*70 + "\n")
        bot = RafaMusicBot(intents=get_intents(enable_privileged=False))
        bot.run(token)
    except discord.errors.LoginFailure:
        print("\n❌ Error: El Token proporcionado en el archivo .env no es válido.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error al ejecutar el bot: {e}")

if __name__ == "__main__":
    main()
