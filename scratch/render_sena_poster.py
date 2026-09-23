import os
import sys
import math
import random
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H = 1080, 1560
img = Image.new('RGB', (W, H), (248, 247, 242))
draw = ImageDraw.Draw(img)

# Confetti sutil en el fondo
random.seed(42)
confetti_colors = [(255, 193, 7), (220, 53, 69), (13, 110, 253), (25, 135, 84), (255, 255, 255)]
for _ in range(85):
    cx = random.randint(20, W - 20)
    cy = random.randint(30, 420)
    cr = random.randint(3, 7)
    draw.ellipse([cx, cy, cx + cr, cy + cr], fill=random.choice(confetti_colors))

# Fuentes del sistema
try:
    f_impact_xxl = ImageFont.truetype('C:\\Windows\\Fonts\\impact.ttf', 78)
    f_impact_xl = ImageFont.truetype('C:\\Windows\\Fonts\\impact.ttf', 56)
    f_impact_l = ImageFont.truetype('C:\\Windows\\Fonts\\impact.ttf', 42)
    f_bold_xl = ImageFont.truetype('C:\\Windows\\Fonts\\arialbd.ttf', 32)
    f_bold_l = ImageFont.truetype('C:\\Windows\\Fonts\\arialbd.ttf', 23)
    f_bold_m = ImageFont.truetype('C:\\Windows\\Fonts\\arialbd.ttf', 18)
    f_bold_s = ImageFont.truetype('C:\\Windows\\Fonts\\arialbd.ttf', 14)
except Exception:
    f_impact_xxl = f_impact_xl = f_impact_l = f_bold_xl = f_bold_l = f_bold_m = f_bold_s = ImageFont.load_default()

def dibujar_bandera(draw, x, y, w, h, cod):
    cod = str(cod).upper()
    if 'COL' in cod:
        draw.rectangle([x, y, x + w, y + int(h * 0.5)], fill=(255, 209, 0))
        draw.rectangle([x, y + int(h * 0.5), x + w, y + int(h * 0.75)], fill=(0, 56, 147))
        draw.rectangle([x, y + int(h * 0.75), x + w, y + h], fill=(206, 17, 38))
    elif 'BRA' in cod:
        draw.rectangle([x, y, x + w, y + h], fill=(0, 156, 59))
        cx, cy = x + w // 2, y + h // 2
        draw.polygon([(x + 4, cy), (cx, y + 3), (x + w - 4, cy), (cx, y + h - 3)], fill=(255, 223, 0))
        draw.ellipse([cx - h // 4, cy - h // 4, cx + h // 4, cy + h // 4], fill=(0, 39, 118))
    elif 'URU' in cod:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        for i in range(1, 9, 2):
            draw.rectangle([x, y + int(i * (h / 9)), x + w, y + int((i + 1) * (h / 9))], fill=(0, 56, 168))
        draw.rectangle([x, y, x + int(w * 0.4), y + int(h * 0.45)], fill=(255, 255, 255))
        draw.ellipse([x + 2, y + 2, x + int(w * 0.35), y + int(h * 0.4)], fill=(255, 209, 0))
    elif 'ESTADOS' in cod or 'USA' in cod:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        for i in range(1, 13, 2):
            draw.rectangle([x, y + int(i * (h / 13)), x + w, y + int((i + 1) * (h / 13))], fill=(179, 25, 66))
        draw.rectangle([x, y, x + int(w * 0.45), y + int(h * 0.54)], fill=(10, 49, 97))
    elif 'JAP' in cod or 'JPN' in cod:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        cx, cy = x + w // 2, y + h // 2
        r = min(w, h) // 3.2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(188, 0, 45))
    elif 'ALE' in cod or 'GER' in cod:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(0, 0, 0))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(221, 0, 0))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(255, 206, 0))
    elif 'POR' in cod:
        draw.rectangle([x, y, x + int(w * 0.4), y + h], fill=(0, 102, 0))
        draw.rectangle([x + int(w * 0.4), y, x + w, y + h], fill=(255, 0, 0))
        cx, cy = x + int(w * 0.4), y + h // 2
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 209, 0))
    elif 'BAJOS' in cod or 'NED' in cod or 'HOL' in cod:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(174, 28, 40))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(255, 255, 255))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(33, 70, 139))
    elif 'ARG' in cod:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(117, 170, 219))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(255, 255, 255))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(117, 170, 219))
        cx, cy = x + w // 2, y + h // 2
        draw.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 209, 0))
    else:
        draw.rectangle([x, y, x + w, y + int(h * 0.5)], fill=(0, 150, 60))
        draw.rectangle([x, y + int(h * 0.5), x + w, y + h], fill=(255, 255, 255))

# 1. BANDERINES SUPERIORES
flags = ['BRA', 'ARG', 'ESP', 'ENG', 'FRA', 'GER', 'POR', 'JPN', 'MEX', 'USA', 'KOR', 'NED', 'COL', 'URU']
fw = W // len(flags)
fh = 32
for i, cod in enumerate(flags):
    fx = i * fw
    dibujar_bandera(draw, fx, 0, fw, fh, cod)
    draw.polygon([(fx, fh), (fx + fw, fh), (fx + fw // 2, fh + 16)], fill=(225, 225, 225), outline=(170, 170, 170))
    dibujar_bandera(draw, fx + 2, fh, fw - 4, 12, cod)

# 2. LOGO OFICIAL SENA CENTRO MINERO
bx1, by1, bx2, by2 = W - 235, 52, W - 35, 175
draw.rounded_rectangle([bx1, by1, bx2, by2], radius=14, fill=(255, 255, 255), outline=(210, 210, 210), width=1)
cx = (bx1 + bx2) // 2
draw.text((cx - 48, by1 + 10), 'SENA', font=f_impact_l, fill=(0, 148, 62))
# Símbolo oficial SENA
sym_y = by1 + 58
green = (0, 148, 62)
draw.ellipse([cx - 5, sym_y, cx + 5, sym_y + 10], fill=green)
draw.rectangle([cx - 19, sym_y + 13, cx + 19, sym_y + 17], fill=green)
draw.rectangle([cx - 3, sym_y + 17, cx + 3, sym_y + 36], fill=green)
draw.polygon([(cx - 2, sym_y + 17), (cx - 18, sym_y + 36), (cx - 22, sym_y + 33), (cx - 5, sym_y + 17)], fill=green)
draw.polygon([(cx + 2, sym_y + 17), (cx + 18, sym_y + 36), (cx + 22, sym_y + 33), (cx + 5, sym_y + 17)], fill=green)
draw.text((cx - 52, by2 - 22), 'CENTRO MINERO', font=f_bold_s, fill=(25, 35, 50))

# 3. ENCABEZADO
draw.text((50, 56), '¡ATENCIÓN COMUNIDAD SENA!', font=f_bold_xl, fill=(195, 25, 25))
draw.rounded_rectangle([50, 106, 450, 146], radius=20, fill=(12, 28, 52))
draw.text((80, 114), '★  ESTÁS INVITADO A LOS  ★', font=f_bold_m, fill=(255, 210, 0))

# 4. TÍTULOS 3D
draw.text((54, 162), 'PARTIDOS', font=f_impact_xxl, fill=(10, 25, 45))
draw.text((50, 158), 'PARTIDOS', font=f_impact_xxl, fill=(12, 38, 75))

draw.text((54, 244), 'INAUGURALES', font=f_impact_xxl, fill=(0, 80, 35))
draw.text((50, 240), 'INAUGURALES', font=f_impact_xxl, fill=(0, 148, 62))

draw.rounded_rectangle([50, 335, 470, 388], radius=10, fill=(12, 28, 52))
draw.text((70, 342), 'DE ESTA SEMANA', font=f_impact_l, fill=(255, 255, 255))
draw.rectangle([50, 394, 470, 400], fill=(255, 209, 0))
draw.rectangle([50, 400, 470, 404], fill=(0, 56, 147))
draw.rectangle([50, 404, 470, 408], fill=(206, 17, 38))

# Balón 3D junto al título
balon_p = r'c:\Users\varga\OneDrive\Desktop\Django\static\img\afiche_balon_3d.png'
if os.path.exists(balon_p):
    b_img = Image.open(balon_p).convert('RGBA').resize((115, 115), Image.Resampling.LANCZOS)
    img.paste(b_img, (490, 305), b_img)

# 5. CALLOUT AVISO
callout_box = [W - 370, 200, W - 40, 310]
draw.rounded_rectangle(callout_box, radius=14, fill=(12, 28, 52), outline=(255, 255, 255), width=2)
draw.text((W - 350, 212), '📢  AVISO OFICIAL:', font=f_bold_m, fill=(255, 210, 0))
draw.text((W - 350, 240), 'LOS PARTIDOS SE JUGARÁN', font=f_bold_s, fill=(255, 255, 255))
draw.text((W - 350, 260), 'DESPUÉS DEL ACTO INAUGURAL', font=f_bold_s, fill=(255, 210, 0))
draw.text((W - 350, 280), 'EN EL CENTRO MINERO', font=f_bold_s, fill=(255, 255, 255))

# 6. ATLETAS EN ACCIÓN
atleta_p = r'c:\Users\varga\OneDrive\Desktop\Django\static\img\afiche_atleta_futbol.jpg'
if os.path.exists(atleta_p):
    atl = Image.open(atleta_p).convert('RGBA')
    atl = ImageOps.fit(atl, (440, 560), Image.Resampling.LANCZOS)
    
    # Mascara suave
    mask = Image.new('L', (440, 560), 255)
    mask_draw = ImageDraw.Draw(mask)
    for x in range(50):
        alpha = int(255 * (x / 50.0))
        mask_draw.line([(x, 0), (x, 560)], fill=alpha)
    for y in range(50):
        alpha = int(255 * (y / 50.0))
        mask_draw.line([(0, 560 - y), (440, 560 - y)], fill=min(alpha, 255))
    
    img.paste(atl, (W - 450, 340), mask)

# 7. PARTIDOS CON FORMATO DEL AFICHE DE REFERENCIA
partidos = [
    {
        'fecha': 'MIÉRCOLES 10 DE JUNIO',
        'sub': 'DESPUÉS DEL ACTO INAUGURAL',
        'duelos': [
            ('URUGUAY', '3196477', 'URU', 'ESTADOS UNIDOS', '3142184', 'USA'),
            ('COLOMBIA', '3321349', 'COL', 'JAPÓN', '3474886', 'JPN')
        ],
        'hora': None
    },
    {
        'fecha': 'JUEVES 11 DE JUNIO',
        'sub': None,
        'duelos': [
            ('ALEMANIA', '3412727', 'GER', 'PORTUGAL', '3412713', 'POR')
        ],
        'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
    },
    {
        'fecha': 'VIERNES 12 DE JUNIO',
        'sub': None,
        'duelos': [
            ('BRASIL', '3171066', 'BRA', 'PAÍSES BAJOS', '3412729', 'NED')
        ],
        'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
    }
]

cy = 430
card_w = 580
for p in partidos:
    # Encabezado fecha
    draw.rounded_rectangle([50, cy, 50 + 260, cy + 36], radius=8, fill=(0, 120, 50))
    draw.text((62, cy + 8), p['fecha'], font=f_bold_m, fill=(255, 255, 255))
    if p['sub']:
        draw.rounded_rectangle([50 + 270, cy, 50 + 560, cy + 36], radius=8, fill=(225, 110, 0))
        draw.text((50 + 280, cy + 9), p['sub'], font=f_bold_s, fill=(255, 255, 255))
    cy += 44
    
    for eq1, f1, c1, eq2, f2, c2 in p['duelos']:
        draw.rounded_rectangle([50, cy, 50 + card_w, cy + 58], radius=12, fill=(255, 255, 255), outline=(215, 215, 215), width=1)
        draw.line([(50, cy + 58), (50 + card_w, cy + 58)], fill=(195, 195, 195), width=2)
        
        dibujar_bandera(draw, 62, cy + 12, 48, 34, c1)
        draw.text((120, cy + 10), eq1, font=f_bold_m, fill=(20, 25, 35))
        draw.text((120, cy + 32), f'FICHA {f1}', font=f_bold_s, fill=(80, 90, 105))
        
        draw.text((320, cy + 12), 'VS', font=f_impact_l, fill=(0, 140, 55))
        
        draw.text((400, cy + 10), eq2, font=f_bold_m, fill=(20, 25, 35))
        draw.text((400, cy + 32), f'FICHA {f2}', font=f_bold_s, fill=(80, 90, 105))
        dibujar_bandera(draw, 50 + card_w - 60, cy + 12, 48, 34, c2)
        cy += 66
    
    if p['hora']:
        draw.rounded_rectangle([50, cy, 50 + 440, cy + 32], radius=8, fill=(0, 110, 45))
        draw.text((65, cy + 7), p['hora'].upper(), font=f_bold_s, fill=(255, 255, 255))
        cy += 40
    cy += 14

# 8. PIE DE PÁGINA
footer_top = H - 320
draw.rectangle([0, footer_top, W, H], fill=(10, 22, 40))

# Siluetas de hinchada
for bx in range(0, W, 22):
    by = footer_top + 45 - int(math.sin(bx * 0.05) * 18)
    draw.ellipse([bx, by, bx + 16, by + 16], fill=(18, 34, 58))
    draw.line([(bx + 8, by + 16), (bx + 8, footer_top + 90)], fill=(18, 34, 58), width=8)
    draw.line([(bx + 8, by + 24), (bx - 4, by - 6)], fill=(18, 34, 58), width=4)
    draw.line([(bx + 8, by + 24), (bx + 20, by - 6)], fill=(18, 34, 58), width=4)

# Balón en esquina izquierda inferior con flags
if os.path.exists(balon_p):
    b_foot = Image.open(balon_p).convert('RGBA').resize((95, 95), Image.Resampling.LANCZOS)
    img.paste(b_foot, (45, footer_top + 185), b_foot)

lema_1 = 'ACOMPAÑEMOS A NUESTROS EQUIPOS EN ESTA GRAN FIESTA DEPORTIVA QUE NOS UNE.'
lema_2 = '¡VIVAMOS EL DEPORTE, LA DIVERSIDAD Y EL ESPÍRITU SENA!'
lema_3 = '¡UNIDOS POR EL DEPORTE, UNIDOS POR EL SENA!'

draw.text((W // 2, footer_top + 105), lema_1, font=f_bold_l, fill=(255, 255, 255), anchor='mm')
draw.text((W // 2, footer_top + 155), lema_2, font=f_bold_l, fill=(255, 215, 0), anchor='mm')
draw.text((W // 2, footer_top + 225), lema_3, font=f_impact_xl, fill=(52, 211, 153), anchor='mm')

out_p = r'c:\Users\varga\OneDrive\Desktop\Django\media\ia_generadas\afiche_sena_perfeccionado.jpg'
img.save(out_p, 'JPEG', quality=95)
print('Afiche perfeccionado guardado con exito:', out_p)
