"""
Generador de Logo Profesional para Rafa Music Pro
Crea un logo de alta resolución (1024x1024) con estética Cyberpunk/Neón
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_rafa_music_logo(output_path="assets/logo.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    size = 1024
    center = size // 2
    
    # 1. Base oscura obsidian
    img = Image.new('RGBA', (size, size), (10, 8, 20, 255))
    
    # 2. Resplandor radial de fondo (Glow)
    glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Halo púrpura exterior
    for r in range(480, 50, -6):
        alpha = int(35 * (1 - r/480))
        glow_draw.ellipse([center - r, center - r, center + r, center + r], fill=(138, 43, 226, alpha))
        
    # Halo cian central
    for r in range(280, 20, -4):
        alpha = int(45 * (1 - r/280))
        glow_draw.ellipse([center - r, center - r, center + r, center + r], fill=(0, 240, 255, alpha))

    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # 3. Anillo exterior con gradiente de neón
    ring_radius = 440
    ring_thickness = 16
    for angle in range(360):
        rad = math.radians(angle)
        # Interpolación de color: Cian (0°) -> Magenta (180°) -> Púrpura (360°)
        t = (math.sin(rad) + 1) / 2
        r_c = int(0 * (1 - t) + 255 * t)
        g_c = int(240 * (1 - t) + 20 * t)
        b_c = int(255 * (1 - t) + 180 * t)
        
        # Puntos de arco
        x1 = center + (ring_radius - ring_thickness) * math.cos(rad)
        y1 = center + (ring_radius - ring_thickness) * math.sin(rad)
        x2 = center + ring_radius * math.cos(rad)
        y2 = center + ring_radius * math.sin(rad)
        draw.line([(x1, y1), (x2, y2)], fill=(r_c, g_c, b_c, 255), width=4)

    # 4. Diadema de Auriculares (Headphones headband)
    hp_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    hp_draw = ImageDraw.Draw(hp_layer)
    
    headband_box = [center - 280, center - 340, center + 280, center + 220]
    # Sombra/resplandor de diadema
    hp_draw.arc(headband_box, start=180, end=0, fill=(0, 240, 255, 120), width=32)
    hp_draw.arc(headband_box, start=180, end=0, fill=(138, 43, 226, 255), width=20)
    hp_draw.arc(headband_box, start=190, end=350, fill=(255, 255, 255, 200), width=6)

    # Almohadillas / Auriculares laterales (Earcups)
    # Izquierda
    left_cup = [center - 320, center - 60, center - 240, center + 140]
    hp_draw.rounded_rectangle(left_cup, radius=35, fill=(20, 15, 38, 255), outline=(0, 240, 255, 255), width=8)
    hp_draw.rounded_rectangle([center - 305, center - 30, center - 255, center + 110], radius=20, fill=(138, 43, 226, 200))
    
    # Derecha
    right_cup = [center + 240, center - 60, center + 320, center + 140]
    hp_draw.rounded_rectangle(right_cup, radius=35, fill=(20, 15, 38, 255), outline=(255, 0, 128, 255), width=8)
    hp_draw.rounded_rectangle([center + 255, center - 30, center + 305, center + 110], radius=20, fill=(138, 43, 226, 200))

    img = Image.alpha_composite(img, hp_layer)

    # 5. Ondas de ecualizador de sonido en el fondo central
    eq_layer = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    eq_draw = ImageDraw.Draw(eq_layer)
    bars = [40, 80, 140, 200, 260, 320, 280, 220, 150, 90, 50]
    bar_width = 16
    spacing = 36
    start_x = center - (len(bars) * spacing) // 2 + 10
    base_y = center + 50

    for i, h in enumerate(bars):
        bx = start_x + i * spacing
        # Color degradado cian a magenta
        t = i / len(bars)
        col = (int(0 + 255*t), int(240*(1-t)), int(255))
        # Barra superior e inferior
        eq_draw.rounded_rectangle([bx, base_y - h//2, bx + bar_width, base_y + h//2], radius=8, fill=(*col, 130))

    img = Image.alpha_composite(img, eq_layer)
    draw = ImageDraw.Draw(img)

    # 6. Gran Letra 'R' estilizada 3D Neón en el centro
    font_path = "C:/Windows/Fonts/ariblk.ttf"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/arialbd.ttf"
    
    font_large = ImageFont.truetype(font_path, 340)
    
    # Sombra profunda y resplandor
    r_text = "R"
    bbox = font_large.getbbox(r_text)
    w_r = bbox[2] - bbox[0]
    h_r = bbox[3] - bbox[1]
    rx = center - w_r // 2
    ry = center - h_r // 2 - 40

    # Glow layer para la R
    r_glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    r_glow_draw = ImageDraw.Draw(r_glow)
    for offset in range(25, 0, -3):
        r_glow_draw.text((rx, ry), r_text, font=font_large, fill=(0, 240, 255, 30))
        r_glow_draw.text((rx + 6, ry + 6), r_text, font=font_large, fill=(138, 43, 226, 30))
    
    img = Image.alpha_composite(img, r_glow.filter(ImageFilter.GaussianBlur(8)))
    draw = ImageDraw.Draw(img)

    # R cuerpo principal (Bisel 3D)
    draw.text((rx + 8, ry + 8), r_text, font=font_large, fill=(20, 10, 40, 255)) # Sombra negra
    draw.text((rx + 4, ry + 4), r_text, font=font_large, fill=(138, 43, 226, 255)) # Capa púrpura
    draw.text((rx, ry), r_text, font=font_large, fill=(255, 255, 255, 255)) # Capa blanca pura
    
    # Pequeño detalle de rayo o corte de neón en la R
    draw.line([(rx + 50, ry + 120), (rx + 180, ry + 120)], fill=(0, 240, 255, 255), width=8)

    # 7. Placa / Banner inferior: "RAFA MUSIC PRO"
    banner_y = center + 270
    banner_w = 540
    banner_h = 75
    banner_box = [center - banner_w//2, banner_y, center + banner_w//2, banner_y + banner_h]

    # Resplandor de banner
    b_glow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    b_glow_draw = ImageDraw.Draw(b_glow)
    b_glow_draw.rounded_rectangle(banner_box, radius=24, fill=(138, 43, 226, 90))
    img = Image.alpha_composite(img, b_glow.filter(ImageFilter.GaussianBlur(10)))
    draw = ImageDraw.Draw(img)

    # Fondo de banner
    draw.rounded_rectangle(banner_box, radius=24, fill=(18, 14, 34, 240), outline=(0, 240, 255, 255), width=4)
    
    # Texto del banner
    font_banner = ImageFont.truetype(font_path, 42)
    b_text = "RAFA MUSIC PRO"
    bb_box = font_banner.getbbox(b_text)
    bw = bb_box[2] - bb_box[0]
    bh = bb_box[3] - bb_box[1]
    
    draw.text((center - bw//2, banner_y + (banner_h - bh)//2 - 6), b_text, font=font_banner, fill=(255, 255, 255, 255))

    # 8. Detalles decorativos: Estrellas / Destellos de luz
    def draw_star(cx, cy, r_out, r_in, col):
        pts = []
        for i in range(8):
            ang = i * math.pi / 4
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=col)

    draw_star(center - 220, center - 240, 28, 8, (0, 240, 255, 255))
    draw_star(center + 230, center - 210, 22, 6, (255, 0, 180, 255))
    draw_star(center + 180, center + 200, 18, 5, (0, 240, 255, 220))

    # Guardar
    img.save(output_path, "PNG")
    print(f"✅ Logo guardado con éxito en: {output_path}")
    return output_path

if __name__ == "__main__":
    create_rafa_music_logo()
