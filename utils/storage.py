"""
Módulo de almacenamiento y persistencia de Rafa Music Pro
Guarda y carga canales 24/7 por servidor
"""

import json
import os
import asyncio
from typing import Dict, Any, Optional
from config import GUILD_SETTINGS_FILE, DATA_DIR

# Servidor principal RAFA PANEL y canal #General pre-configurados por defecto
DEFAULT_GUILDS_247 = {
    "1538269421020258304": {
        "voice_channel_id": 1542358479270846565,
        "text_channel_id": 1538269422190592052,
        "active": True
    }
}

class StorageManager:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._ensure_dir()
        self._data: Dict[str, Any] = self._load()

    def _ensure_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR, exist_ok=True)
        if not os.path.exists(GUILD_SETTINGS_FILE):
            with open(GUILD_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump({"guilds_247": dict(DEFAULT_GUILDS_247)}, f, indent=4)

    def _load(self) -> Dict[str, Any]:
        data = {"guilds_247": dict(DEFAULT_GUILDS_247)}
        try:
            if os.path.exists(GUILD_SETTINGS_FILE):
                with open(GUILD_SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and "guilds_247" in loaded:
                        for k, v in DEFAULT_GUILDS_247.items():
                            if k not in loaded["guilds_247"]:
                                loaded["guilds_247"][k] = v
                        return loaded
        except Exception as e:
            print(f"Error cargando configuraciones: {e}")
        return data

    def _save(self):
        try:
            with open(GUILD_SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando configuraciones: {e}")

    async def set_247(self, guild_id: int, voice_channel_id: int, text_channel_id: Optional[int] = None):
        """Activa el modo 24/7 para un servidor y guarda el canal de voz."""
        async with self._lock:
            if "guilds_247" not in self._data:
                self._data["guilds_247"] = {}
            self._data["guilds_247"][str(guild_id)] = {
                "voice_channel_id": voice_channel_id,
                "text_channel_id": text_channel_id,
                "active": True
            }
            self._save()

    async def remove_247(self, guild_id: int):
        """Desactiva el modo 24/7 para un servidor."""
        async with self._lock:
            if "guilds_247" in self._data and str(guild_id) in self._data["guilds_247"]:
                del self._data["guilds_247"][str(guild_id)]
                self._save()

    def is_247(self, guild_id: int) -> bool:
        """Comprueba si un servidor tiene activado el modo 24/7."""
        return str(guild_id) in self._data.get("guilds_247", {})

    def get_247_info(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Obtiene la información del canal 24/7 de un servidor."""
        return self._data.get("guilds_247", {}).get(str(guild_id))

    def get_247(self, guild_id: int) -> Optional[Dict[str, Any]]:
        """Alias para get_247_info."""
        return self.get_247_info(guild_id)

    def get_all_247(self) -> Dict[str, Dict[str, Any]]:
        """Devuelve todos los servidores con 24/7 activo."""
        return self._data.get("guilds_247", {})

# Instancia global
storage = StorageManager()
