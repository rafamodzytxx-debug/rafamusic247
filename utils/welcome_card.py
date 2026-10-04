"""
Generador de Tarjetas de Bienvenida y Despedida
Rafa Music Pro - Creado por RafaModzYT King of c+++
"""

import io
import math
import os
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter

async def fetch_avatar_image(avatar_url: str) -> Image.Image:
    """Descarga el avatar del usuario y lo convierte en objeto PIL Image."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(avatar_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    img = Image.open(io.BytesIO(data)).convert("RGBA")
                    return img
    except Exception as e:
        print(f"Error descargando avatar: {e}")
    # Avatar por defecto si falla la descarga
    default_img = Image.new("RGBA", (256, 256), (30, 25, 50, 255))
    d = ImageDraw.Draw(default_img)
    d.ellipse([20, 20, 236, 236], fill=(138, 43, 226, 255))
    return default_img

def circle_mask_avatar(avatar_img: Image.Image, size: int = 180) -> Image.Image:
    """Recorta la imagen de perfil en forma de círculo suave."""
    avatar_img = avatar_img.resize((size, size), Image.Resampling.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, size, size], fill=255)
    
    circular_avatar = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    circular_avatar.paste(avatar_img, (0, 0), mask=mask)
    return circular_avatar

async def generate_welcome_card(
    member_name: str,
    server_name: str,
    member_count: int,
    avatar_url: str,
    is_welcome: bool = True
) -> io.BytesIO:
    """
    Genera una tarjeta gráfica profesional de bienvenida o despedida (1000x420 px).
    Estilo Neón Cyberpunk Obsidian a juego con Rafa Music Pro.
    """
    width = 1000
    height = 420
    
    # 1. Fondo base oscuro obsidian
    img = Image.new("RGBA", (width, height), (10, 8, 22, 255))
    
    # 2. Resplandor radial de fondo
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    primary_color = (0, 240, 255) if is_welcome else (255, 69, 0)       # Cian vs Rojo/Naranja
    accent_color = (138, 43, 226) if is_welcome else (180, 20, 90)     # Púrpura vs Carmesí
    
    # Halos de neón
    for r in range(400, 30, -8):
        alpha = int(35 * (1 - r/400))
        glow_draw.ellipse([180 - r, height//2 - r, 180 + r, height//2 + r], fill=(*primary_color, alpha))
        glow_draw.ellipse([width - 150 - r, height//2 - r, width - 150 + r, height//2 + r], fill=(*accent_color, alpha))

    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # 3. Marco exterior con bordes de neón
    border_margin = 12
    draw.rounded_rectangle(
        [border_margin, border_margin, width - border_margin, height - border_margin],
        radius=25,
        fill=(14, 11, 28, 230),
        outline=(*primary_color, 200),
        width=3
    )

    # Línea decorativa superior con degradado
    for x in range(border_margin + 20, width - border_margin - 20):
        t = (x - border_margin) / (width - 2 * border_margin)
        r_c = int(primary_color[0] * (1 - t) + accent_color[0] * t)
        g_c = int(primary_color[1] * (1 - t) + accent_color[1] * t)
        b_c = int(primary_color[2] * (1 - t) + accent_color[2] * t)
        draw.line([(x, border_margin + 4), (x, border_margin + 8)], fill=(r_c, g_c, b_c, 255))

    # 4. Avatar del usuario
    avatar_raw = await fetch_avatar_image(avatar_url)
    avatar_size = 200
    circular_avatar = circle_mask_avatar(avatar_raw, size=avatar_size)

    avatar_x = 75
    avatar_y = (height - avatar_size) // 2

    # Resplandor y anillo exterior para el avatar
    for r in range(12, 0, -2):
        draw.ellipse(
            [avatar_x - r, avatar_y - r, avatar_x + avatar_size + r, avatar_y + avatar_size + r],
            outline=(*primary_color, int(80 * (1 - r/12))),
            width=2
        )
    
    # Anillo brillante del avatar
    draw.ellipse(
        [avatar_x - 5, avatar_y - 5, avatar_x + avatar_size + 5, avatar_y + avatar_size + 5],
        outline=(*accent_color, 255),
        width=6
    )
    
    # Pegar avatar recortado
    img.paste(circular_avatar, (avatar_x, avatar_y), mask=circular_avatar)
    draw = ImageDraw.Draw(img)

    # 5. Textos informativos
    font_bold = "C:/Windows/Fonts/ariblk.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:/Windows/Fonts/arialbd.ttf"
        
    font_header = ImageFont.truetype(font_bold, 48)
    font_username = ImageFont.truetype(font_bold, 36)
    font_sub = ImageFont.truetype(font_bold, 24)
    font_badge = ImageFont.truetype(font_bold, 20)

    text_start_x = avatar_x + avatar_size + 50

    # Título principal
    header_text = "¡BIENVENIDO/A!" if is_welcome else "¡HASTA LUEGO!"
    hy = 75
    
    # Resplandor del título
    t_glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    tg_draw = ImageDraw.Draw(t_glow)
    for off in range(10, 0, -2):
        tg_draw.text((text_start_x, hy), header_text, font=font_header, fill=(*primary_color, 40))
    img = Image.alpha_composite(img, t_glow.filter(ImageFilter.GaussianBlur(4)))
    draw = ImageDraw.Draw(img)

    draw.text((text_start_x + 3, hy + 3), header_text, font=font_header, fill=(10, 5, 20, 255))
    draw.text((text_start_x, hy), header_text, font=font_header, fill=(*primary_color, 255))

    # Nombre de usuario (recortado si es muy largo)
    clean_name = member_name[:24]
    uy = hy + 68
    draw.text((text_start_x + 2, uy + 2), clean_name, font=font_username, fill=(10, 5, 20, 255))
    draw.text((text_start_x, uy), clean_name, font=font_username, fill=(255, 255, 255, 255))

    # Nombre del servidor
    sy = uy + 55
    server_text = f"a {server_name[:26]}" if is_welcome else f"de {server_name[:26]}"
    draw.text((text_start_x, sy), server_text, font=font_sub, fill=(180, 180, 210, 255))

    # Badge de contador de miembros
    by = sy + 55
    count_text = f"MIEMBRO #{member_count}" if is_welcome else f"QUEDAN {member_count} MIEMBROS"
    
    badge_w = 280
    badge_h = 42
    badge_box = [text_start_x, by, text_start_x + badge_w, by + badge_h]
    
    draw.rounded_rectangle(badge_box, radius=12, fill=(20, 16, 36, 230), outline=(*accent_color, 255), width=2)
    draw.text((text_start_x + 20, by + 9), count_text, font=font_badge, fill=(255, 255, 255, 255))

    # 6. Destellos y estrellas decorativas
    def draw_star(cx, cy, r_out, r_in, col):
        pts = []
        for i in range(8):
            ang = i * math.pi / 4
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=col)

    draw_star(width - 90, 80, 16, 4, (*primary_color, 255))
    draw_star(width - 150, height - 90, 14, 4, (*accent_color, 255))
    draw_star(text_start_x + 460, hy + 15, 12, 3, (255, 255, 255, 200))

    # Exportar a buffer de memoria en formato PNG
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
