"""
Script para actualizar automáticamente el avatar del bot en Discord
Rafa Music Pro - Creado por Rafa
"""

import sys
import asyncio

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import discord
from config import DISCORD_TOKEN

async def update_bot_avatar():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Conectado como {client.user.name} ({client.user.id})")
        try:
            with open("assets/logo.png", "rb") as f:
                avatar_bytes = f.read()
            print("Subiendo nuevo avatar a Discord...")
            await client.user.edit(avatar=avatar_bytes)
            print("¡Avatar actualizado con éxito en Discord!")
        except discord.errors.HTTPException as e:
            print(f"Error HTTP de Discord: {e}")
        except Exception as e:
            print(f"Error inesperado: {e}")
        finally:
            await client.close()

    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(update_bot_avatar())
