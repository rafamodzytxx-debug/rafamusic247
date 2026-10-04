# 🎵 Rafa Music Pro - Bot de Música para Discord

> **Creado y Desarrollado con orgullo por Rafa**  
> *Bot de música de alta definición con soporte permanente 24/7, búsqueda inteligente con autocompletado en vivo y controles interactivos.*

---

## ✨ Características Principales

- 👑 **Perfil y Créditos Oficiales:** Todos los créditos a **Rafa** en embeds, perfil, comandos `/creditos`, `/invitar` y `/help`.
- 🌐 **Agregable a cualquier servidor:** Enlace OAuth2 directo para invitarlo a cualquier servidor de Discord con los permisos adecuados.
- 🔊 **Comando `/join`:** Conecta el bot inmediatamente al canal de voz donde estés.
- 🔍 **Comando `/play` con Autocompletado en Vivo:** Al escribir `/play musica:` aparece una lista desplegable en tiempo real con las mejores canciones de YouTube a medida que escribes.
- 🛡️ **Modo 24/7 Permanente (`/bot canal 24.7`):** El bot se queda fijado en el canal de voz las 24 horas del día, los 7 días de la semana. **Nunca se desconecta**, ni al terminarse la música ni si los usuarios se van.
- 🔌 **Desconexión 24/7 (`/desconect 24.7`):** Apaga el modo 24/7 y desconecta el bot del canal de inmediato.
- 🎛️ **Controles Interactivos por Botones:** Pausar/Reanudar (⏯️), Saltar (⏭️), Repetición (🔁), Cola (📜), Alternar 24/7 (🛡️) y Detener (⏹️).
- 💾 **Persistencia Automática:** Si el bot se reinicia, recuerda todos los canales 24/7 y se reconecta automáticamente al iniciar.

---

## 📋 Lista de Comandos

### 🎶 Música y Reproducción
| Comando | Descripción |
| :--- | :--- |
| `/join` | Conecta el bot a tu canal de voz actual. |
| `/play [musica]` | Busca una canción en vivo (con lista desplegable mientras escribes) o reproduce un enlace. |
| `/skip` | Salta a la siguiente canción de la cola. |
| `/pause` | Pausa la canción actual. |
| `/resume` | Reanuda la canción en pausa. |
| `/stop` | Detiene la reproducción y vacía la cola. |
| `/queue` | Muestra la lista de canciones en espera. |
| `/nowplaying` | Muestra la canción actual con sus botones de control interactivo. |
| `/volume [1-150]` | Ajusta el volumen del audio (ej: `/volume 100`). |
| `/loop [modo]` | Activa modo repetición: desactivado, canción actual o toda la cola. |
| `/shuffle` | Mezcla aleatoriamente las canciones en la cola. |
| `/clear` | Elimina todas las canciones en espera. |
| `/leave` | Desconecta el bot del canal de voz. |

---

### 🛡️ Modo 24/7 Permanente
Puedes activar o desactivar el modo 24/7 usando comandos de barra diagonal (`/`) o directamente escribiéndolo en el chat de texto:

| Modo Slash | Modo Texto en Chat | Qué hace |
| :--- | :--- | :--- |
| `/bot canal_24_7` | `/bot canal 24.7` o `!bot canal 24.7` | **Activa el modo 24/7:** El bot entra a tu canal y **nunca se desconecta**. |
| `/bot desconect_24_7` | `/desconect 24.7` o `!desconect 24.7` | **Desactiva el modo 24/7** y desconecta el bot del canal de voz. |
| `/canal247` | `!247` | Atajo alternativo para activar. |
| `/desconect247` | `!desconectar 24.7` | Atajo alternativo para desactivar. |

---

### 👑 Créditos e Invitación
| Comando | Descripción |
| :--- | :--- |
| `/creditos` | Muestra los créditos oficiales a **Rafa**, estadísticas del bot y botón para invitarlo. |
| `/invitar` | Genera el enlace oficial para agregar **Rafa Music Pro** a cualquier servidor de Discord. |
| `/help` | Guía de uso interactiva con todos los comandos. |
| `/ping` | Comprueba la latencia del bot con Discord. |

---

## 🚀 Guía de Instalación y Puesta en Marcha

### Paso 1: Crear la Aplicación del Bot en Discord
1. Ve al portal de desarrolladores de Discord: **[https://discord.com/developers/applications](https://discord.com/developers/applications)**
2. Haz clic en el botón superior derecho: **"New Application"**.
3. Nómbralo: **`Rafa Music Pro`** y pulsa **Create**.
4. Ve a la pestaña **Bot** en el menú izquierdo:
   - En **Username**, asegúrate de que sea `Rafa Music Pro`.
   - Haz clic en **Reset Token** (o *Copy Token*) y copia tu **Token**. *(¡Guárdalo bien, no lo compartas con nadie!)*
   - Desplázate hacia abajo hasta la sección **Privileged Gateway Intents** y activa los 3 interruptores:
     - ✅ **Presence Intent**
     - ✅ **Server Members Intent**
     - ✅ **Message Content Intent**
   - Haz clic en **Save Changes**.
5. Ve a la pestaña **General Information** en el menú izquierdo:
   - Copia el **Application ID** (este es tu `CLIENT_ID`).

---

### Paso 2: Configurar el archivo `.env`
Abre el archivo [`.env`](file:///d:/Discord%20Bot%20Musica/.env) en el editor y pega tus datos:

```env
DISCORD_TOKEN=tu_token_aqui_sin_comillas
CLIENT_ID=tu_application_id_aqui
```

---

### Paso 3: Iniciar el Bot
Tienes dos maneras súper sencillas:

#### Opción A (La más rápida en Windows):
Simplemente haz doble clic en el archivo [`run.bat`](file:///d:/Discord%20Bot%20Musica/run.bat).  
El script instalará las dependencias necesarias automáticamente y pondrá el bot en línea.

#### Opción B (Desde la terminal):
```powershell
python -m pip install -r requirements.txt
python bot.py
```

---

### Paso 4: Agregar el Bot a tu Servidor de Discord
Cuando el bot inicie, verás en la consola de comandos el enlace de invitación generado especialmente para tu bot.  
También puedes usar el comando `/invitar` dentro de cualquier servidor.

El enlace tiene la siguiente estructura:
```
https://discord.com/oauth2/authorize?client_id=TU_CLIENT_ID&permissions=3468352&integration_type=0&scope=bot%20applications.commands
```

Solo selecciona el servidor donde quieres agregarlo y dale a **Autorizar**.

---

## 🛠️ Tecnologías Utilizadas
- **Python 3.14**
- **Discord.py 2.7+** con soporte de voz Opus y E2EE DAVE
- **yt-dlp** para extracción de audio de alta velocidad
- **FFmpeg 9.0+** para codificación y streaming fluido en tiempo real
- **Desarrollado y Creado por Rafa**
