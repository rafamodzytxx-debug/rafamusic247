"""
Componentes interactivos de interfaz (Botones, Selectores, Paginación)
Rafa Music Pro - Creado y Desarrollado por Rafa
"""

import discord
from discord.ui import View, Button, button
from typing import TYPE_CHECKING
from config import COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, BOT_NAME, CREATOR_NAME, get_invite_url
from utils.storage import storage

if TYPE_CHECKING:
    from utils.audio_player import GuildPlayer

class PlayerControlView(View):
    """Botones interactivos en el mensaje de Ahora Reproduciendo."""
    def __init__(self, player: 'GuildPlayer'):
        super().__init__(timeout=None)  # Persistente mientras dure la reproducción
        self.player = player
        self._update_button_states()

    def _update_button_states(self):
        # Actualizar color del botón 24/7
        for child in self.children:
            if isinstance(child, Button):
                if child.custom_id == "btn_247":
                    child.style = discord.ButtonStyle.success if self.player.is_247 else discord.ButtonStyle.secondary
                    child.label = "24/7: ON" if self.player.is_247 else "24/7: OFF"
                elif child.custom_id == "btn_pause":
                    is_paused = self.player.voice_client and self.player.voice_client.is_paused()
                    child.label = "Reanudar" if is_paused else "Pausar"
                    child.emoji = "▶️" if is_paused else "⏸️"

    @button(label="Pausar", style=discord.ButtonStyle.primary, emoji="⏸️", custom_id="btn_pause")
    async def pause_resume(self, interaction: discord.Interaction, btn: Button):
        vc = self.player.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message("❌ El bot no está en un canal de voz.", ephemeral=True)

        if vc.is_paused():
            vc.resume()
            btn.label = "Pausar"
            btn.emoji = "⏸️"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("▶️ Música reanudada.", ephemeral=True)
        elif vc.is_playing():
            vc.pause()
            btn.label = "Reanudar"
            btn.emoji = "▶️"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("⏸️ Música pausada.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No hay nada reproduciéndose.", ephemeral=True)

    @button(label="Saltar", style=discord.ButtonStyle.secondary, emoji="⏭️", custom_id="btn_skip")
    async def skip(self, interaction: discord.Interaction, btn: Button):
        vc = self.player.voice_client
        if not vc or not vc.is_connected() or not self.player.is_playing:
            return await interaction.response.send_message("❌ No hay música reproduciéndose para saltar.", ephemeral=True)

        song_title = self.player.current.title if self.player.current else "canción"
        vc.stop()  # El callback after llamará a play_next
        await interaction.response.send_message(f"⏭️ Se ha saltado: **{song_title}**", ephemeral=False)

    @button(label="Repetir", style=discord.ButtonStyle.secondary, emoji="🔁", custom_id="btn_loop")
    async def toggle_loop(self, interaction: discord.Interaction, btn: Button):
        modes = ["off", "song", "queue"]
        curr_idx = modes.index(self.player.loop_mode)
        next_mode = modes[(curr_idx + 1) % len(modes)]
        self.player.loop_mode = next_mode

        names = {
            "off": "Desactivado ⚪",
            "song": "Canción actual 🔂",
            "queue": "Toda la cola 🔁"
        }
        await interaction.response.send_message(f"🔁 Modo de repetición establecido en: **{names[next_mode]}**", ephemeral=True)

    @button(label="Cola", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="btn_queue")
    async def view_queue(self, interaction: discord.Interaction, btn: Button):
        if not self.player.current and not self.player.queue:
            return await interaction.response.send_message("📭 La cola está actualmente vacía.", ephemeral=True)

        embed = discord.Embed(
            title=f"📜 Cola de Reproducción - {self.player.guild.name}",
            color=COLOR_PRIMARY
        )
        if self.player.current:
            embed.add_field(
                name="🔊 Ahora Reproduciendo",
                value=f"[{self.player.current.title}]({self.player.current.webpage_url}) (`{self.player.current.duration_str}`)\nPedido por: {self.player.current.requester.mention}",
                inline=False
            )

        queue_list = list(self.player.queue)
        if queue_list:
            desc = ""
            for idx, s in enumerate(queue_list[:10], 1):
                desc += f"`{idx}.` [{s.title}]({s.webpage_url}) | `{s.duration_str}` (por {s.requester.display_name})\n"
            if len(queue_list) > 10:
                desc += f"\n*... y {len(queue_list) - 10} canciones más.*"
            embed.add_field(name="Próximas en la lista:", value=desc, inline=False)
        else:
            embed.add_field(name="Próximas:", value="*No hay más canciones en la cola.*", inline=False)

        embed.set_footer(text=f"{BOT_NAME} • Desarrollado por {CREATOR_NAME}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="24/7: OFF", style=discord.ButtonStyle.secondary, emoji="🛡️", custom_id="btn_247")
    async def toggle_247(self, interaction: discord.Interaction, btn: Button):
        guild_id = self.player.guild.id
        if self.player.is_247:
            await storage.remove_247(guild_id)
            btn.style = discord.ButtonStyle.secondary
            btn.label = "24/7: OFF"
            msg = "⚪ **Modo 24/7 Desactivado.** El bot se desconectará si la música se detiene y no hay actividad."
        else:
            vc = self.player.voice_client
            if not vc or not vc.channel:
                return await interaction.response.send_message("❌ El bot no está en un canal de voz.", ephemeral=True)
            await storage.set_247(guild_id, vc.channel.id, interaction.channel_id)
            self.player.cancel_inactivity_timer()
            btn.style = discord.ButtonStyle.success
            btn.label = "24/7: ON"
            msg = f"🟢 **Modo 24/7 Activado en {vc.channel.mention}!**\nEl bot permanecerá en el canal indefinidamente hasta que uses `/desconect 24.7`."

        await interaction.response.edit_message(view=self)
        await interaction.followup.send(msg, ephemeral=True)

    @button(label="Detener", style=discord.ButtonStyle.danger, emoji="⏹️", custom_id="btn_stop")
    async def stop(self, interaction: discord.Interaction, btn: Button):
        vc = self.player.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message("❌ El bot no está conectado.", ephemeral=True)

        self.player.queue.clear()
        if vc.is_playing() or vc.is_paused():
            vc.stop()

        if not self.player.is_247:
            await self.player.cleanup()
            await interaction.response.send_message("⏹️ Música detenida, cola limpiada y bot desconectado.", ephemeral=False)
        else:
            await interaction.response.send_message("⏹️ Música detenida y cola vaciada. (El bot se queda en el canal por estar en modo 24/7 🛡️).", ephemeral=False)


class InviteButtonView(View):
    """Vista con botón de enlace directo para agregar el bot a cualquier servidor."""
    def __init__(self, bot_user: discord.ClientUser):
        super().__init__(timeout=None)
        invite_link = get_invite_url(str(bot_user.id))
        self.add_item(Button(
            label="➕ Agregar Rafa Music Pro a tu Servidor",
            url=invite_link,
            style=discord.ButtonStyle.link,
            emoji="🤖"
        ))
