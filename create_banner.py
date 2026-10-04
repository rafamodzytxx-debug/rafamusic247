"""
Generador de Banner de Perfil para RafaModzYT King of c+++
Crea un banner neón de alta calidad para Discord (960x360)
"""

import math
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_profile_banner(output_path="assets/banner.png"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    width = 960
    height = 360
    
    # Base oscura obsidian
    img = Image.new('RGBA', (width, height), (11, 9, 22, 255))
    
    # Resplandor radial de fondo
    glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    
    # Halo púrpura y cian en el fondo
    for r in range(350, 20, -5):
        alpha = int(40 * (1 - r/350))
        glow_draw.ellipse([width//2 - r, height//2 - r, width//2 + r, height//2 + r], fill=(138, 43, 226, alpha))
        
    for r in range(200, 10, -4):
        alpha = int(45 * (1 - r/200))
        glow_draw.ellipse([width*2//3 - r, height//2 - r, width*2//3 + r, height//2 + r], fill=(0, 240, 255, alpha))

    img = Image.alpha_composite(img, glow)
    draw = ImageDraw.Draw(img)

    # Ondas de sonido decorativas en el fondo
    eq_layer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    eq_draw = ImageDraw.Draw(eq_layer)
    bars_count = 35
    spacing = 18
    bar_w = 8
    start_x = width - (bars_count * spacing) - 40
    
    for i in range(bars_count):
        bx = start_x + i * spacing
        h = int(30 + 80 * abs(math.sin(i * 0.35)))
        t = i / bars_count
        col = (int(0 + 255 * t), int(240 * (1 - t)), 255)
        eq_draw.rounded_rectangle([bx, height - 70 - h, bx + bar_w, height - 70], radius=4, fill=(*col, 100))

    img = Image.alpha_composite(img, eq_layer)
    draw = ImageDraw.Draw(img)

    # Fuentes
    font_bold = "C:/Windows/Fonts/ariblk.ttf"
    if not os.path.exists(font_bold):
        font_bold = "C:/Windows/Fonts/arialbd.ttf"
        
    font_title = ImageFont.truetype(font_bold, 62)
    font_sub = ImageFont.truetype(font_bold, 36)
    font_badge = ImageFont.truetype(font_bold, 22)

    # Texto: RafaModzYT
    # En la parte derecha/centro (la esquina izquierda es donde se posiciona el avatar en Discord)
    text_x = 290
    text_y = 65

    # Resplandor del título
    glow_text = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    gt_draw = ImageDraw.Draw(glow_text)
    
    title_text = "RafaModzYT"
    for off in range(16, 0, -2):
        gt_draw.text((text_x, text_y), title_text, font=font_title, fill=(0, 240, 255, 30))
        gt_draw.text((text_x + 3, text_y + 3), title_text, font=font_title, fill=(138, 43, 226, 30))

    img = Image.alpha_composite(img, glow_text.filter(ImageFilter.GaussianBlur(6)))
    draw = ImageDraw.Draw(img)

    # Texto principal 3D: RafaModzYT
    draw.text((text_x + 4, text_y + 4), title_text, font=font_title, fill=(15, 10, 30, 255))
    draw.text((text_x + 2, text_y + 2), title_text, font=font_title, fill=(138, 43, 226, 255))
    draw.text((text_x, text_y), title_text, font=font_title, fill=(255, 255, 255, 255))

    # Subtítulo: King of c+++
    sub_y = text_y + 85
    sub_text = "King of c+++"
    
    # Resplandor subtítulo
    sub_glow = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    sg_draw = ImageDraw.Draw(sub_glow)
    for off in range(12, 0, -2):
        sg_draw.text((text_x, sub_y), sub_text, font=font_sub, fill=(255, 0, 180, 40))
        sg_draw.text((text_x + 2, sub_y + 2), sub_text, font=font_sub, fill=(0, 240, 255, 40))
        
    img = Image.alpha_composite(img, sub_glow.filter(ImageFilter.GaussianBlur(5)))
    draw = ImageDraw.Draw(img)

    draw.text((text_x + 3, sub_y + 3), sub_text, font=font_sub, fill=(10, 5, 25, 255))
    draw.text((text_x + 1, sub_y + 1), sub_text, font=font_sub, fill=(255, 0, 128, 255))
    draw.text((text_x, sub_y), sub_text, font=font_sub, fill=(0, 240, 255, 255))

    # Badge / Etiqueta inferior: "CREATOR & DEVELOPER • 24/7 MUSIC"
    badge_box = [text_x, sub_y + 68, text_x + 480, sub_y + 108]
    draw.rounded_rectangle(badge_box, radius=14, fill=(20, 15, 38, 220), outline=(138, 43, 226, 255), width=2)
    draw.text((text_x + 22, sub_y + 75), "CREATOR & DEVELOPER • 24/7 MUSIC PRO", font=font_badge, fill=(255, 255, 255, 255))

    # Línea de neón horizontal en el borde superior
    for x in range(width):
        t = x / width
        col = (int(0 + 255 * t), int(240 * (1 - t)), 255)
        draw.line([(x, 0), (x, 3)], fill=(*col, 255))

    # Estrellas de destello
    def draw_star(cx, cy, r_out, r_in, col):
        pts = []
        for i in range(8):
            ang = i * math.pi / 4
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        draw.polygon(pts, fill=col)

    draw_star(text_x + 400, text_y + 10, 18, 5, (0, 240, 255, 255))
    draw_star(text_x + 290, sub_y + 15, 14, 4, (255, 0, 180, 255))
    draw_star(width - 80, 50, 22, 6, (0, 240, 255, 200))

    img.save(output_path, "PNG")
    return output_path

if __name__ == "__main__":
    create_profile_banner()
