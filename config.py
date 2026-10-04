"""
Configuración central de Rafa Music Pro
Desarrollado y Creado por Rafa
"""

import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Tokens y Credenciales de Discord
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
CLIENT_ID = os.getenv("CLIENT_ID", "")

# Información del Bot y Créditos
BOT_NAME = "Rafa Music Pro"
BOT_VERSION = "1.0.0 Pro Edition"
CREATOR_NAME = "RafaModzYT King of c+++"
BOT_DESCRIPTION = (
    "Bot de música de alta definición y fidelidad sonora con soporte 24/7 permanente, "
    "búsqueda en tiempo real con autocompletado y controles interactivos."
)
CREATOR_CREDITS = (
    "👑 **Creador y Desarrollador Oficial:** RafaModzYT King of c+++\n"
    "🚀 **Versión:** 1.0.0 Pro Edition\n"
    "⚡ **Motor:** Python + Discord.py + FFmpeg + yt-dlp\n"
    "🌐 **Disponible para cualquier servidor de Discord**"
)

# Colores de la paleta estética (Neon Purple / Cyberpunk Music)
COLOR_PRIMARY = 0x8A2BE2      # Azul violeta neón
COLOR_SUCCESS = 0x00FF7F      # Verde brillante
COLOR_ERROR = 0xFF4500        # Rojo neón / Naranja
COLOR_WARNING = 0xFFD700      # Dorado
COLOR_INFO = 0x00BFFF         # Azul cian eléctrico

# Ajustes de audio por defecto
DEFAULT_VOLUME = 0.8          # 80% de volumen
DEFAULT_INACTIVITY_TIMEOUT = 180  # 3 minutos antes de desconectarse si no está en 24/7

# Rutas de datos
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
GUILD_SETTINGS_FILE = os.path.join(DATA_DIR, "guild_settings.json")

# Permisos para el enlace de invitación (Permiso estándar: Conectar, Hablar, Administrar Mensajes, Embeds, etc.)
# 3468352 incluye: Conectar, Hablar, Voz Prioritaria, Ver Canales, Enviar Mensajes, Incrustar Enlaces, Adjuntar Archivos, Leer Historial
BOT_PERMISSIONS = 3468352

def get_invite_url(client_id: str = None) -> str:
    """Genera el enlace de invitación oficial para agregar el bot a cualquier servidor."""
    cid = client_id or CLIENT_ID
    if not cid:
        return ""
    return (
        f"https://discord.com/oauth2/authorize?client_id={cid}&permissions={BOT_PERMISSIONS}"
        f"&integration_type=0&scope=bot%20applications.commands"
    )
