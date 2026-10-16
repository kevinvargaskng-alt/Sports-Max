"""
Módulo de Generación de Imágenes y Afiches con Inteligencia Artificial
Exclusivo para el Administrador del Sistema Deportivo SENA Centro Minero.
"""
import os
import io
import math
import random
import uuid
import json
import logging
import urllib.request
import urllib.parse
from PIL import Image, ImageDraw, ImageFont, ImageOps
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger('django')

# Mapeo de resoluciones por relación de aspecto
DIMENSIONES_ASPECTO = {
    '1:1': (1024, 1024),
    '16:9': (1024, 576),
    '9:16': (576, 1024),
    '4:3': (1024, 768),
    '3:4': (768, 1024),
}

# Modificadores de estilo visual para modelos de difusión
MODIFICADORES_ESTILO = {
    'fotorealista': 'single centered subject, hyperrealistic photograph, professional studio camera, sharp focus, 8k resolution, dramatic lighting, perfect anatomy, no text, no watermark, no collage, no split screen',
    'deportivo_sena': 'official modern sports branding poster, SENA Centro Minero institutional colors, athletic composition, high resolution',
    'ilustracion_3d': 'single centered subject, modern 3D digital illustration, Pixar and Blender aesthetic, smooth clay render, clean volumetric lighting, no text, no watermark, no collage',
    'arte_digital': 'single centered subject, epic athletic energy, digital concept art, vibrant contrast, dramatic lighting, high definition, no text, no watermark',
    'minimalista': 'clean minimalist sports design, elegant vector lines, modern sports aesthetic, no text, no watermark'
}

NOMBRES_ESTILO = {
    'fotorealista': 'Fotorealista HD',
    'deportivo_sena': 'Afiche Deportivo SENA',
    'ilustracion_3d': 'Ilustración 3D',
    'arte_digital': 'Arte Digital Dinámico',
    'minimalista': 'Minimalista Moderno'
}


def es_administrador(user) -> bool:
    """Verifica si el usuario es un administrador autenticado del sistema."""
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    return bool(user.is_staff or user.is_superuser or getattr(user, 'rol', '') == 'admin')


import re

DICCIONARIO_DEPORTES_EN = {
    'fútbol sala': 'intense indoor futsal football match, dynamic player in yellow kit shooting futsal ball on indoor wooden court',
    'futbol sala': 'intense indoor futsal football match, dynamic player in yellow kit shooting futsal ball on indoor wooden court',
    'futsal': 'intense indoor futsal match, athletic player running on indoor court, dynamic action',
    'microfútbol': 'indoor microfutbol soccer match, players on polished court, high energy sports moment',
    'microfutbol': 'indoor microfutbol soccer match, players on polished court, high energy sports moment',
    'voleibol': 'professional volleyball match, athletic player jumping high for a spike at the net, indoor arena',
    'voley': 'professional volleyball match, athletic player jumping high for a spike at the net, indoor arena',
    'baloncesto': 'dynamic basketball game, athletic player in motion driving to the hoop, modern indoor arena',
    'basket': 'dynamic basketball game, athletic player in motion driving to the hoop, modern indoor arena',
    'ajedrez': 'dramatic competitive chess match, focus on ornate chess pieces on wooden board, cinematic lighting',
    'atletismo': 'track and field sprint race, muscular athlete bursting out of starting blocks, sunny stadium track',
    'tenis de mesa': 'table tennis ping pong match, player smashing the ball across the table, fast motion blur',
    'taekwondo': 'taekwondo martial arts tournament, fighter executing a high jumping kick in dojang',
    'natación': 'swimming championship race, swimmer diving into crystal blue competition pool, splashing water',
    'natacion': 'swimming championship race, swimmer diving into crystal blue competition pool, splashing water',
    'gimnasio': 'intense athletic fitness workout, athlete lifting heavy barbell with chalk in modern gym',
    'trofeo': 'gleaming golden championship sports trophy cup on a pedestal with dramatic spotlights',
    'medalla': 'gold champion sports medal with vibrant ribbon on athletic texture background',
    'tux': 'cute sporty penguin mascot wearing athletic SENA sports jersey and sneakers',
    'mascota': 'energetic athletic animal mascot celebrating in sports uniform on a stadium pitch',
}


def es_afiche_deportivo(prompt: str, estilo: str) -> bool:
    """
    Detecta si la solicitud corresponde al afiche con fixture/programación oficial del SENA.
    Solo se activa si el usuario seleccionó explícitamente el estilo 'deportivo_sena'
    o si en el prompt pide explícitamente el afiche oficial/institucional del SENA.
    """
    if estilo == 'deportivo_sena':
        return True
    # Si el usuario eligió cualquier otro estilo explícito (fotorealista, arte_digital, 3d, etc.),
    # respetamos su estilo visual para que FLUX genere una obra gráfica única.
    if estilo and estilo not in ['deportivo_sena', 'auto']:
        return False

    p = (prompt or '').lower()
    gatillos_estrictos = [
        'afiche sena', 'cartel sena', 'afiche oficial sena', 'afiche institucional',
        'fixture interfichas', 'programacion sena', 'afiche deportivo sena'
    ]
    return any(g in p for g in gatillos_estrictos)


def limpiar_prompt_para_difusion(prompt: str) -> str:
    """Limpia palabras como 'afiche', 'póster', 'cartel' que inducen a los modelos a generar collages y texto deforme."""
    p = prompt.strip()
    patrones_a_remover = [
        r'^(generar|genera|crear|crea|dibuja|hazme|haz|un|una)\s+',
        r'\b(afiche\s+oficial\s+para|afiche\s+de|afiche\s+del|afiche\s+para|afiche)\b',
        r'\b(cartel\s+oficial\s+para|cartel\s+de|cartel\s+del|cartel\s+para|cartel)\b',
        r'\b(poster\s+de|poster\s+para|poster)\b',
        r'\b(flyer\s+de|flyer\s+para|flyer)\b',
    ]
    for pat in patrones_a_remover:
        p = re.sub(pat, '', p, flags=re.IGNORECASE).strip()
    return p


def optimizar_prompt_con_gemini(prompt_usuario: str, estilo: str = 'fotorealista') -> str:
    """
    Usa Gemini 2.5 Flash para expandir y enriquecer el prompt del usuario,
    garantizando un único sujeto central y prohibiendo collages y textos deformes.
    """
    prompt_limpio = limpiar_prompt_para_difusion(prompt_usuario)
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        mod = MODIFICADORES_ESTILO.get(estilo, '')
        return f"{prompt_limpio}, {mod}"

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        instruccion = (
            "You are an expert art director for AI image generation. "
            "Convert the user's sports/general concept into a vivid, cinematic English prompt for a diffusion model. "
            "CRITICAL RULES:\n"
            "1. Focus on a SINGLE scene and a SINGLE centered athletic subject or action. NEVER create collages, multi-panel, or split-screen images.\n"
            "2. NEVER include text, logos, or posters inside the image to prevent distorted lettering.\n"
            "3. If the user mentions futsal or fútbol sala, describe an indoor futsal court with wooden floor and futsal ball.\n"
            "4. Always append: 'single centered subject, cinematic sports photography, dynamic lighting, sharp focus, 8k, no text, no watermark, no collage'.\n"
            "Output ONLY the final English prompt text, no quotes, no explanations."
        )

        nombre_estilo = NOMBRES_ESTILO.get(estilo, estilo)
        mensaje = f"User concept: '{prompt_limpio}'. Desired visual style: {nombre_estilo}."

        payload = {
            "systemInstruction": {"parts": [{"text": instruccion}]},
            "contents": [{"role": "user", "parts": [{"text": mensaje}]}],
            "generationConfig": {
                "temperature": 0.5,
                "maxOutputTokens": 150,
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            prompt_optimizado = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            if prompt_optimizado:
                return prompt_optimizado
    except Exception as e:
        logger.warning(f"[GeneradorImagen] No se pudo optimizar con Gemini: {e}")

    # Fallback inteligente usando diccionario
    p_lower = prompt_limpio.lower()
    for k, v in DICCIONARIO_DEPORTES_EN.items():
        if k in p_lower:
            mod = MODIFICADORES_ESTILO.get(estilo, '')
            return f"{v}, {mod}"

    modificador = MODIFICADORES_ESTILO.get(estilo, '')
    return f"{prompt_limpio}, single centered subject, {modificador}" if modificador else prompt_limpio


# ============================================================
#  DIBUJADO VECTORIAL DE BANDERAS
# ============================================================

def _dibujar_bandera(draw, x, y, w, h, codigo_pais: str):
    """Dibuja banderas limpias vectoriales de países o fichas."""
    codigo = (codigo_pais or '').upper().strip()
    draw.rectangle([x, y, x + w, y + h], outline=(190, 190, 190), width=1)

    if codigo in ['COLOMBIA', 'COL']:
        draw.rectangle([x, y, x + w, y + h * 0.5], fill=(255, 209, 0))
        draw.rectangle([x, y + h * 0.5, x + w, y + h * 0.75], fill=(0, 56, 147))
        draw.rectangle([x, y + h * 0.75, x + w, y + h], fill=(206, 17, 38))
    elif codigo in ['BRASIL', 'BRA']:
        draw.rectangle([x, y, x + w, y + h], fill=(0, 156, 59))
        cx, cy = x + w // 2, y + h // 2
        draw.polygon([(x + 4, cy), (cx, y + 3), (x + w - 4, cy), (cx, y + h - 3)], fill=(255, 223, 0))
        draw.ellipse([cx - h // 4, cy - h // 4, cx + h // 4, cy + h // 4], fill=(0, 39, 118))
    elif codigo in ['URUGUAY', 'URU']:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        for i in range(1, 9, 2):
            draw.rectangle([x, y + int(i * (h / 9)), x + w, y + int((i + 1) * (h / 9))], fill=(0, 56, 168))
        draw.rectangle([x, y, x + int(w * 0.4), y + int(h * 0.45)], fill=(255, 255, 255))
        draw.ellipse([x + 3, y + 3, x + int(w * 0.35), y + int(h * 0.4)], fill=(255, 209, 0))
    elif codigo in ['USA', 'ESTADOS UNIDOS']:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        for i in range(1, 13, 2):
            draw.rectangle([x, y + int(i * (h / 13)), x + w, y + int((i + 1) * (h / 13))], fill=(179, 25, 66))
        draw.rectangle([x, y, x + int(w * 0.45), y + int(h * 0.54)], fill=(10, 49, 97))
    elif codigo in ['JAPON', 'JAPÓN', 'JPN']:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        cx, cy = x + w // 2, y + h // 2
        r = min(w, h) // 3.2
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(188, 0, 45))
    elif codigo in ['ALEMANIA', 'GER']:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(0, 0, 0))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(221, 0, 0))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(255, 206, 0))
    elif codigo in ['PORTUGAL', 'POR']:
        draw.rectangle([x, y, x + int(w * 0.4), y + h], fill=(0, 102, 0))
        draw.rectangle([x + int(w * 0.4), y, x + w, y + h], fill=(255, 0, 0))
        cx, cy = x + int(w * 0.4), y + h // 2
        draw.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=(255, 209, 0))
    elif codigo in ['PAISES BAJOS', 'PAÍSES BAJOS', 'NED', 'HOLANDA']:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(174, 28, 40))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(255, 255, 255))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(33, 70, 139))
    elif codigo in ['ARGENTINA', 'ARG']:
        draw.rectangle([x, y, x + w, y + int(h * 0.33)], fill=(117, 170, 219))
        draw.rectangle([x, y + int(h * 0.33), x + w, y + int(h * 0.66)], fill=(255, 255, 255))
        draw.rectangle([x, y + int(h * 0.66), x + w, y + h], fill=(117, 170, 219))
        cx, cy = x + w // 2, y + h // 2
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 209, 0))
    elif codigo in ['FRANCIA', 'FRA']:
        draw.rectangle([x, y, x + int(w * 0.33), y + h], fill=(0, 38, 84))
        draw.rectangle([x + int(w * 0.33), y, x + int(w * 0.66), y + h], fill=(255, 255, 255))
        draw.rectangle([x + int(w * 0.66), y, x + w, y + h], fill=(237, 41, 57))
    elif codigo in ['ESPAÑA', 'ESPAÑA', 'ESP']:
        draw.rectangle([x, y, x + w, y + int(h * 0.25)], fill=(170, 21, 27))
        draw.rectangle([x, y + int(h * 0.25), x + w, y + int(h * 0.75)], fill=(241, 191, 0))
        draw.rectangle([x, y + int(h * 0.75), x + w, y + h], fill=(170, 21, 27))
    elif codigo in ['INGLATERRA', 'ENG']:
        draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255))
        draw.rectangle([x + int(w * 0.42), y, x + int(w * 0.58), y + h], fill=(206, 17, 38))
        draw.rectangle([x, y + int(h * 0.42), x + w, y + int(h * 0.58)], fill=(206, 17, 38))
    elif codigo in ['MEXICO', 'MÉXICO', 'MEX']:
        draw.rectangle([x, y, x + int(w * 0.33), y + h], fill=(0, 104, 71))
        draw.rectangle([x + int(w * 0.33), y, x + int(w * 0.66), y + h], fill=(255, 255, 255))
        draw.rectangle([x + int(w * 0.66), y, x + w, y + h], fill=(206, 17, 38))
    else:
        # Bandera institucional SENA
        draw.rectangle([x, y, x + w, y + int(h * 0.5)], fill=(0, 150, 60))
        draw.rectangle([x, y + int(h * 0.5), x + w, y + h], fill=(255, 255, 255))
        draw.ellipse([x + w // 2 - 5, y + h // 2 - 5, x + w // 2 + 5, y + h // 2 + 5], fill=(255, 120, 0))


# ============================================================
#  MOTOR DE AFICHES DEPORTIVOS OFICIALES DEL SENA
# ============================================================

def _dibujar_logo_sena_oficial(draw, x1, y1, x2, y2, font_sena, font_sub):
    """Dibuja la caja institucional con el logo y símbolo oficial del SENA Centro Minero."""
    draw.rounded_rectangle([x1, y1, x2, y2], radius=14, fill=(255, 255, 255), outline=(210, 210, 210), width=1)
    cx = (x1 + x2) // 2
    # Texto SENA
    draw.text((cx - 48, y1 + 10), 'SENA', font=font_sena, fill=(0, 148, 62))
    # Símbolo oficial SENA (persona geométrica corriendo)
    sym_y = y1 + 58
    green = (0, 148, 62)
    draw.ellipse([cx - 5, sym_y, cx + 5, sym_y + 10], fill=green)
    draw.rectangle([cx - 19, sym_y + 13, cx + 19, sym_y + 17], fill=green)
    draw.rectangle([cx - 3, sym_y + 17, cx + 3, sym_y + 36], fill=green)
    draw.polygon([(cx - 2, sym_y + 17), (cx - 18, sym_y + 36), (cx - 22, sym_y + 33), (cx - 5, sym_y + 17)], fill=green)
    draw.polygon([(cx + 2, sym_y + 17), (cx + 18, sym_y + 36), (cx + 22, sym_y + 33), (cx + 5, sym_y + 17)], fill=green)
    # Texto CENTRO MINERO
    draw.text((cx - 52, y2 - 22), 'CENTRO MINERO', font=font_sub, fill=(25, 35, 50))


def generar_afiche_oficial_sena(prompt: str, ancho: int = 1080, alto: int = 1560) -> Image.Image:
    """
    Genera un afiche deportivo oficial del SENA Centro Minero idéntico al afiche de referencia:
    - Banderines internacionales superiores
    - Logo oficial SENA Centro Minero con símbolo institucional
    - Gran título de impacto con relieve 3D: PARTIDOS INAUGURALES / TORNEO INTERFICHAS
    - Subtítulo con cinta tricolor de Colombia y balón 3D
    - Programación real de partidos con banderas, nombres y números de ficha
    - Horarios y llamado de aviso importante
    - Gráfico de atletas en acción (Colombia vs rival)
    - Pie de página institucional con siluetas de celebración y lemas oficiales
    """
    W, H = ancho, alto
    img = Image.new('RGB', (W, H), (248, 247, 242))
    draw = ImageDraw.Draw(img)

    # Confetti festivo sutil en el fondo superior (dinámico en cada generación)
    confetti_colors = [(255, 193, 7), (220, 53, 69), (13, 110, 253), (25, 135, 84), (255, 255, 255)]
    for _ in range(85):
        cx = random.randint(20, W - 20)
        cy = random.randint(30, 420)
        cr = random.randint(3, 7)
        draw.ellipse([cx, cy, cx + cr, cy + cr], fill=random.choice(confetti_colors))

    # Cargar fuentes del sistema
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

    # 1. BANDERINES SUPERIORES
    flags_list = ['BRA', 'ARG', 'ESP', 'ENG', 'FRA', 'GER', 'POR', 'JPN', 'MEX', 'USA', 'KOR', 'NED', 'COL', 'URU']
    random.shuffle(flags_list)
    fw = W // len(flags_list)
    fh = 32
    for i, cod in enumerate(flags_list):
        fx = i * fw
        _dibujar_bandera(draw, fx, 0, fw, fh, cod)
        draw.polygon([(fx, fh), (fx + fw, fh), (fx + fw // 2, fh + 16)], fill=(225, 225, 225), outline=(170, 170, 170))
        _dibujar_bandera(draw, fx + 2, fh, fw - 4, 12, cod)

    # 2. CAJA LOGO OFICIAL SENA CENTRO MINERO
    _dibujar_logo_sena_oficial(draw, W - 235, 52, W - 35, 175, f_impact_l, f_bold_s)

    # 3. ENCABEZADO
    draw.text((50, 56), "¡ATENCIÓN COMUNIDAD SENA!", font=f_bold_xl, fill=(195, 25, 25))

    # Badge 'ESTÁS INVITADO A LOS'
    draw.rounded_rectangle([50, 106, 450, 146], radius=20, fill=(12, 28, 52))
    draw.text((80, 114), "★  ESTÁS INVITADO A LOS  ★", font=f_bold_m, fill=(255, 210, 0))

    # Determinar títulos dinámicos y disciplina a partir del prompt
    p_lower = (prompt or '').lower()
    deporte_tag = 'futbol'
    if 'fútbol sala' in p_lower or 'futbol sala' in p_lower or 'futsal' in p_lower:
        t1, t2, sub = "TORNEO", "FÚTBOL SALA", "INTERFICHAS 2026"
        deporte_tag = 'futsal'
    elif 'microfútbol' in p_lower or 'microfutbol' in p_lower:
        t1, t2, sub = "TORNEO", "MICROFÚTBOL", "INTERFICHAS 2026"
        deporte_tag = 'futsal'
    elif 'voleibol' in p_lower or 'voley' in p_lower:
        t1, t2, sub = "TORNEO", "DE VOLEIBOL", "INTERFICHAS 2026"
        deporte_tag = 'voleibol'
    elif 'baloncesto' in p_lower or 'basket' in p_lower:
        t1, t2, sub = "TORNEO", "BALONCESTO", "INTERFICHAS 2026"
        deporte_tag = 'baloncesto'
    elif 'ajedrez' in p_lower:
        t1, t2, sub = "TORNEO", "DE AJEDREZ", "INTERFICHAS 2026"
        deporte_tag = 'ajedrez'
    elif 'atletismo' in p_lower:
        t1, t2, sub = "CAMPEONATO", "ATLETISMO", "INTERFICHAS 2026"
        deporte_tag = 'atletismo'
    elif 'tenis' in p_lower or 'ping pong' in p_lower:
        t1, t2, sub = "TORNEO", "TENIS DE MESA", "INTERFICHAS 2026"
        deporte_tag = 'tenis'
    elif 'mundialito' in p_lower:
        t1, t2, sub = "MUNDIALITO", "INTERFICHAS", "FÚTBOL 8 - 2026"
        deporte_tag = 'futbol'
    elif 'final' in p_lower:
        t1, t2, sub = "GRAN FINAL", "INTERFICHAS", "DE ESTA SEMANA"
        deporte_tag = 'futbol'
    elif 'inaugural' in p_lower or 'partidos' in p_lower:
        t1, t2, sub = "PARTIDOS", "INAUGURALES", "DE ESTA SEMANA"
        deporte_tag = 'futbol'
    else:
        palabras = [w for w in re.sub(r'[^\w\s]', '', prompt).strip().upper().split() if len(w) > 2 and w not in ['AFICHE', 'OFICIAL', 'PARA', 'DEL', 'LOS', 'LAS', 'CON', 'UNA', 'ESTE', 'TORNEO']]
        if len(palabras) >= 2:
            t1 = "TORNEO"
            t2 = " ".join(palabras[:2])
            sub = "CENTRO MINERO 2026"
        else:
            t1, t2, sub = "TORNEO", "INTERFICHAS", "CENTRO MINERO 2026"

    # Sombra 3D y relieve en títulos
    draw.text((54, 162), t1, font=f_impact_xxl, fill=(10, 25, 45))
    draw.text((50, 158), t1, font=f_impact_xxl, fill=(12, 38, 75))

    draw.text((54, 244), t2, font=f_impact_xxl, fill=(0, 80, 35))
    draw.text((50, 240), t2, font=f_impact_xxl, fill=(0, 148, 62))

    # Subtítulo en caja oscura
    draw.rounded_rectangle([50, 335, 470, 388], radius=10, fill=(12, 28, 52))
    draw.text((70, 342), sub, font=f_impact_l, fill=(255, 255, 255))

    # Cinta tricolor nacional debajo del subtítulo
    draw.rectangle([50, 394, 470, 400], fill=(255, 209, 0))
    draw.rectangle([50, 400, 470, 404], fill=(0, 56, 147))
    draw.rectangle([50, 404, 470, 408], fill=(206, 17, 38))

    # Balón 3D o icono de la disciplina junto al título
    ball_path = 'static/img/afiche_balon_3d.png'
    if deporte_tag == 'baloncesto':
        ball_path = 'static/img/sports_basketball.png'
    elif deporte_tag == 'voleibol':
        ball_path = 'static/img/sports_volleyball.png'

    full_bp = os.path.join(settings.BASE_DIR, ball_path)
    if os.path.exists(full_bp):
        try:
            balon_im = Image.open(full_bp).convert('RGBA').resize((115, 115), Image.Resampling.LANCZOS)
            img.paste(balon_im, (490, 305), balon_im)
        except Exception:
            pass

    # 4. AVISO IMPORTANTE (MEGÁFONO)
    callout_box = [W - 370, 200, W - 40, 310]
    draw.rounded_rectangle(callout_box, radius=14, fill=(12, 28, 52), outline=(255, 255, 255), width=2)
    draw.text((W - 350, 212), "📢  AVISO OFICIAL:", font=f_bold_m, fill=(255, 210, 0))
    draw.text((W - 350, 240), "LOS PARTIDOS SE JUGARÁN", font=f_bold_s, fill=(255, 255, 255))
    draw.text((W - 350, 260), "DESPUÉS DEL ACTO INAUGURAL", font=f_bold_s, fill=(255, 210, 0))
    draw.text((W - 350, 280), "EN EL CENTRO MINERO", font=f_bold_s, fill=(255, 255, 255))

    # 5. ATLETA / JUGADORES EN ACCIÓN SEGÚN EL DEPORTE (LADO DERECHO)
    atleta_path = 'static/img/afiche_atleta_futbol.jpg'
    if deporte_tag == 'futsal':
        atleta_path = 'static/img/afiche_atleta_futsal.jpg'
    elif deporte_tag == 'baloncesto':
        atleta_path = 'static/img/sports_basketball.png'
    elif deporte_tag == 'voleibol':
        atleta_path = 'static/img/sports_volleyball.png'

    full_ap = os.path.join(settings.BASE_DIR, atleta_path)
    if not os.path.exists(full_ap):
        full_ap = os.path.join(settings.BASE_DIR, 'static/img/afiche_atleta_futbol.jpg')

    if os.path.exists(full_ap):
        try:
            atleta_im = Image.open(full_ap).convert('RGBA')
            atleta_im = ImageOps.fit(atleta_im, (440, 560), Image.Resampling.LANCZOS)
            # Máscara de fusión suave
            mask = Image.new('L', (440, 560), 255)
            mask_draw = ImageDraw.Draw(mask)
            for x in range(50):
                alpha = int(255 * (x / 50.0))
                mask_draw.line([(x, 0), (x, 560)], fill=alpha)
            for y in range(50):
                alpha = int(255 * (y / 50.0))
                mask_draw.line([(0, 560 - y), (440, 560 - y)], fill=min(alpha, 255))
            img.paste(atleta_im, (W - 450, 340), mask)
        except Exception:
            pass

    # 6. PROGRAMACIÓN DE PARTIDOS DINÁMICA CON DATOS REALES DEL SISTEMA
    partidos_data = []
    try:
        from interfichas.models import PartidoInterfichas, EquipoInterfichas
        partidos_db = list(PartidoInterfichas.objects.select_related('equipo_local', 'equipo_visitante').all())
        if len(partidos_db) >= 4:
            # Seleccionar 4 partidos aleatorios de los 30 registrados
            partidos_azar = random.sample(partidos_db, 4)
            partidos_data = [
                {
                    'fecha': 'MIÉRCOLES 10 DE JUNIO',
                    'sub': 'DESPUÉS DEL ACTO INAUGURAL',
                    'enfrentamientos': [
                        {
                            'eq1': partidos_azar[0].equipo_local.nombre_equipo,
                            'f1': getattr(partidos_azar[0].equipo_local, 'ficha', '3196477'),
                            'c1': partidos_azar[0].equipo_local.nombre_equipo,
                            'eq2': partidos_azar[0].equipo_visitante.nombre_equipo,
                            'f2': getattr(partidos_azar[0].equipo_visitante, 'ficha', '3142184'),
                            'c2': partidos_azar[0].equipo_visitante.nombre_equipo,
                        },
                        {
                            'eq1': partidos_azar[1].equipo_local.nombre_equipo,
                            'f1': getattr(partidos_azar[1].equipo_local, 'ficha', '3321349'),
                            'c1': partidos_azar[1].equipo_local.nombre_equipo,
                            'eq2': partidos_azar[1].equipo_visitante.nombre_equipo,
                            'f2': getattr(partidos_azar[1].equipo_visitante, 'ficha', '3474886'),
                            'c2': partidos_azar[1].equipo_visitante.nombre_equipo,
                        },
                    ],
                    'hora': None
                },
                {
                    'fecha': 'JUEVES 11 DE JUNIO',
                    'sub': None,
                    'enfrentamientos': [
                        {
                            'eq1': partidos_azar[2].equipo_local.nombre_equipo,
                            'f1': getattr(partidos_azar[2].equipo_local, 'ficha', '3412727'),
                            'c1': partidos_azar[2].equipo_local.nombre_equipo,
                            'eq2': partidos_azar[2].equipo_visitante.nombre_equipo,
                            'f2': getattr(partidos_azar[2].equipo_visitante, 'ficha', '3412713'),
                            'c2': partidos_azar[2].equipo_visitante.nombre_equipo,
                        },
                    ],
                    'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
                },
                {
                    'fecha': 'VIERNES 12 DE JUNIO',
                    'sub': None,
                    'enfrentamientos': [
                        {
                            'eq1': partidos_azar[3].equipo_local.nombre_equipo,
                            'f1': getattr(partidos_azar[3].equipo_local, 'ficha', '3171066'),
                            'c1': partidos_azar[3].equipo_local.nombre_equipo,
                            'eq2': partidos_azar[3].equipo_visitante.nombre_equipo,
                            'f2': getattr(partidos_azar[3].equipo_visitante, 'ficha', '3412729'),
                            'c2': partidos_azar[3].equipo_visitante.nombre_equipo,
                        },
                    ],
                    'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
                }
            ]
        elif EquipoInterfichas.objects.count() >= 6:
            equipos_db = list(EquipoInterfichas.objects.all())
            eq_azar = random.sample(equipos_db, min(8, len(equipos_db)))
            partidos_data = [
                {
                    'fecha': 'MIÉRCOLES 10 DE JUNIO',
                    'sub': 'DESPUÉS DEL ACTO INAUGURAL',
                    'enfrentamientos': [
                        {'eq1': eq_azar[0].nombre_equipo, 'f1': eq_azar[0].ficha, 'c1': eq_azar[0].nombre_equipo,
                         'eq2': eq_azar[1].nombre_equipo, 'f2': eq_azar[1].ficha, 'c2': eq_azar[1].nombre_equipo},
                        {'eq1': eq_azar[2].nombre_equipo, 'f1': eq_azar[2].ficha, 'c1': eq_azar[2].nombre_equipo,
                         'eq2': eq_azar[3].nombre_equipo, 'f2': eq_azar[3].ficha, 'c2': eq_azar[3].nombre_equipo},
                    ],
                    'hora': None
                },
                {
                    'fecha': 'JUEVES 11 DE JUNIO',
                    'sub': None,
                    'enfrentamientos': [
                        {'eq1': eq_azar[4].nombre_equipo, 'f1': eq_azar[4].ficha, 'c1': eq_azar[4].nombre_equipo,
                         'eq2': eq_azar[5].nombre_equipo, 'f2': eq_azar[5].ficha, 'c2': eq_azar[5].nombre_equipo},
                    ],
                    'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
                }
            ]
    except Exception as ex:
        logger.warning(f"[GeneradorImagen] Error al cargar partidos de BD: {ex}")

    if not partidos_data:
        partidos_data = [
            {
                'fecha': 'MIÉRCOLES 10 DE JUNIO',
                'sub': 'DESPUÉS DEL ACTO INAUGURAL',
                'enfrentamientos': [
                    {'eq1': 'URUGUAY', 'f1': '3196477', 'c1': 'URU', 'eq2': 'ESTADOS UNIDOS', 'f2': '3142184', 'c2': 'USA'},
                    {'eq1': 'COLOMBIA', 'f1': '3321349', 'c1': 'COL', 'eq2': 'JAPÓN', 'f2': '3474886', 'c2': 'JPN'},
                ],
                'hora': None
            },
            {
                'fecha': 'JUEVES 11 DE JUNIO',
                'sub': None,
                'enfrentamientos': [
                    {'eq1': 'ALEMANIA', 'f1': '3412727', 'c1': 'GER', 'eq2': 'PORTUGAL', 'f2': '3412713', 'c2': 'POR'},
                ],
                'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
            },
            {
                'fecha': 'VIERNES 12 DE JUNIO',
                'sub': None,
                'enfrentamientos': [
                    {'eq1': 'BRASIL', 'f1': '3171066', 'c1': 'BRA', 'eq2': 'PAÍSES BAJOS', 'f2': '3412729', 'c2': 'NED'},
                ],
                'hora': '9:30 a.m. - ESTAR 10 MINUTOS ANTES PARA ALISTARSE'
            }
        ]

    current_y = 430
    card_w = 580

    for grupo in partidos_data:
        # Píldora de fecha
        draw.rounded_rectangle([50, current_y, 50 + 260, current_y + 36], radius=8, fill=(0, 120, 50))
        draw.text((62, current_y + 8), grupo['fecha'], font=f_bold_m, fill=(255, 255, 255))

        if grupo.get('sub'):
            draw.rounded_rectangle([50 + 270, current_y, 50 + 560, current_y + 36], radius=8, fill=(225, 110, 0))
            draw.text((50 + 280, current_y + 9), grupo['sub'], font=f_bold_s, fill=(255, 255, 255))

        current_y += 44

        # Tarjetas de cada partido
        for match in grupo['enfrentamientos']:
            mc_box = [50, current_y, 50 + card_w, current_y + 58]
            draw.rounded_rectangle(mc_box, radius=12, fill=(255, 255, 255), outline=(215, 215, 215), width=1)
            draw.line([(50, current_y + 58), (50 + card_w, current_y + 58)], fill=(195, 195, 195), width=2)

            _dibujar_bandera(draw, 62, current_y + 12, 48, 34, match.get('c1', 'COL'))
            draw.text((120, current_y + 10), match.get('eq1', 'EQUIPO 1').upper(), font=f_bold_m, fill=(20, 25, 35))
            draw.text((120, current_y + 32), f"FICHA {match.get('f1', '0000000')}", font=f_bold_s, fill=(80, 90, 105))

            draw.text((320, current_y + 12), "VS", font=f_impact_l, fill=(0, 140, 55))

            draw.text((400, current_y + 10), match.get('eq2', 'EQUIPO 2').upper(), font=f_bold_m, fill=(20, 25, 35))
            draw.text((400, current_y + 32), f"FICHA {match.get('f2', '0000000')}", font=f_bold_s, fill=(80, 90, 105))
            _dibujar_bandera(draw, 50 + card_w - 60, current_y + 12, 48, 34, match.get('c2', 'BRA'))

            current_y += 66

        if grupo.get('hora'):
            draw.rounded_rectangle([50, current_y, 50 + 440, current_y + 32], radius=8, fill=(0, 110, 45))
            draw.text((65, current_y + 7), f"🕒  {grupo['hora'].upper()}", font=f_bold_s, fill=(255, 255, 255))
            current_y += 40

        current_y += 14

    # 7. PIE DE PÁGINA INSTITUCIONAL / MOTIVACIONAL
    footer_h = 320
    footer_top = H - footer_h
    draw.rectangle([0, footer_top, W, H], fill=(10, 22, 40))

    # Siluetas vectoriales de hinchada celebrando
    for bx in range(0, W, 22):
        by = footer_top + 45 - int(math.sin(bx * 0.05) * 18)
        draw.ellipse([bx, by, bx + 16, by + 16], fill=(18, 34, 58))
        draw.line([(bx + 8, by + 16), (bx + 8, footer_top + 90)], fill=(18, 34, 58), width=8)
        draw.line([(bx + 8, by + 24), (bx - 4, by - 6)], fill=(18, 34, 58), width=4)
        draw.line([(bx + 8, by + 24), (bx + 20, by - 6)], fill=(18, 34, 58), width=4)

    lema_1 = "ACOMPAÑEMOS A NUESTROS EQUIPOS EN ESTA GRAN FIESTA DEPORTIVA QUE NOS UNE."
    lema_2 = "¡VIVAMOS EL DEPORTE, LA DIVERSIDAD Y EL ESPÍRITU SENA!"
    lema_3 = "¡UNIDOS POR EL DEPORTE, UNIDOS POR EL SENA!"

    draw.text((W // 2, footer_top + 105), lema_1, font=f_bold_l, fill=(255, 255, 255), anchor="mm")
    draw.text((W // 2, footer_top + 155), lema_2, font=f_bold_l, fill=(255, 215, 0), anchor="mm")
    draw.text((W // 2, footer_top + 225), lema_3, font=f_impact_xl, fill=(52, 211, 153), anchor="mm")

    return img


# ============================================================
#  FUNCIÓN PRINCIPAL: generar_imagen_ia
# ============================================================

def generar_imagen_ia(prompt: str, aspecto: str = '1:1', estilo: str = 'fotorealista',
                      usuario=None, optimizar: bool = True, seed: int = None) -> dict:
    """
    Genera una imagen o afiche con Inteligencia Artificial aplicando parámetros específicos.
    Requiere que el usuario sea administrador.
    
    - Si es afiche deportivo/institucional: Genera el cartel oficial SENA con tipografía perfecta.
    - Si es foto/render/ilustración: Genera un sujeto único de alta fidelidad sin textos deformes ni collages.
    """
    if not es_administrador(usuario):
        return {
            'success': False,
            'error': 'Permiso denegado. La generación de imágenes con IA está reservada exclusivamente para el Administrador del Sistema.'
        }

    prompt_limpio = (prompt or '').strip()
    if not prompt_limpio:
        return {
            'success': False,
            'error': 'Debes especificar una descripción o prompt para generar la imagen.'
        }

    aspecto_normalizado = aspecto if aspecto in DIMENSIONES_ASPECTO else '1:1'
    ancho, alto = DIMENSIONES_ASPECTO[aspecto_normalizado]

    media_dir = os.path.join(settings.MEDIA_ROOT, 'ia_generadas')
    os.makedirs(media_dir, exist_ok=True)
    filename = f"tux_gen_{int(timezone.now().timestamp())}_{uuid.uuid4().hex[:8]}.jpg"
    file_path = os.path.join(media_dir, filename)

    # ── CASO A: AFICHE DEPORTIVO INSTITUCIONAL (GUÍA IMAGEN 3) ──
    if es_afiche_deportivo(prompt_limpio, estilo):
        try:
            img_afiche = generar_afiche_oficial_sena(prompt_limpio, ancho=1080, alto=1560)
            # Para afiches deportivos, mantener la proporción vertical completa del póster institucional
            img_final = img_afiche

            img_final.convert('RGB').save(file_path, 'JPEG', quality=95)
            image_url = f"{settings.MEDIA_URL}ia_generadas/{filename}"

            # Registrar auditoría
            try:
                from usuarios.models import HistorialAccion
                HistorialAccion.objects.create(
                    usuario=usuario,
                    modulo='IA_ASISTENTE',
                    accion='Generación de Afiche Oficial SENA',
                    descripcion=f"Afiche Deportivo Oficial generado para: {prompt_limpio[:120]}"
                )
            except Exception:
                pass

            return {
                'success': True,
                'image_url': image_url,
                'filename': filename,
                'prompt_original': prompt_limpio,
                'prompt_final': 'Afiche Oficial Deportivo SENA Centro Minero',
                'aspecto': aspecto_normalizado,
                'estilo': 'deportivo_sena',
                'estilo_nombre': 'Afiche Deportivo SENA',
                'ancho': img_final.width,
                'alto': img_final.height,
            }
        except Exception as e:
            logger.error(f"[GeneradorImagen] Error en afiche oficial: {e}")

    # ── CASO B: FOTOGRAFÍA / ILUSTRACIÓN REALISTA CON FLUX ──
    try:
        # Enriquecer prompt con directivas anti-collage y anti-texto
        if optimizar:
            prompt_final = optimizar_prompt_con_gemini(prompt_limpio, estilo)
        else:
            modificador = MODIFICADORES_ESTILO.get(estilo, '')
            prompt_final = f"{prompt_limpio}, single subject, {modificador}"

        # Garantizar que no genere texto deforme ni collages
        prompt_final += ", no text, no watermark, no logo, no split screen, no collage, single centered subject"

        prompt_encoded = urllib.parse.quote(prompt_final)
        
        # Probar generación con FLUX y nologo
        seed_val = seed if seed is not None else random.randint(1, 999999)
        urls_a_probar = [
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={ancho}&height={alto}&seed={seed_val}&model=flux&nologo=true",
            f"https://image.pollinations.ai/prompt/{prompt_encoded}?width={ancho}&height={alto}&seed={seed_val}&nologo=true",
            f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt_limpio + ' single centered subject professional photography 8k')}?width={ancho}&height={alto}&seed={seed_val}&nologo=true"
        ]

        image_bytes = None
        for u in urls_a_probar:
            try:
                req = urllib.request.Request(
                    u,
                    headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
                )
                with urllib.request.urlopen(req, timeout=25) as resp:
                    data = resp.read()
                    if data and len(data) > 1000:
                        image_bytes = data
                        break
            except Exception as ex:
                logger.warning(f"[GeneradorImagen] Intento falló: {ex}")
                continue

        if image_bytes:
            img = Image.open(io.BytesIO(image_bytes))
            # Si hay marca de agua residual en el borde inferior, recortar 36px
            w_orig, h_orig = img.size
            if h_orig > 100:
                img = img.crop((0, 0, w_orig, h_orig - 36))
            img_fitted = ImageOps.fit(img, (ancho, alto), method=Image.Resampling.LANCZOS)
        else:
            # Si no hay conexión externa, generar afiche institucional
            img_fitted = generar_afiche_oficial_sena(prompt_limpio, ancho=ancho, alto=alto)

        img_fitted.convert('RGB').save(file_path, 'JPEG', quality=95)
        image_url = f"{settings.MEDIA_URL}ia_generadas/{filename}"

        try:
            from usuarios.models import HistorialAccion
            HistorialAccion.objects.create(
                usuario=usuario,
                modulo='IA_ASISTENTE',
                accion='Generación de Imagen con IA',
                descripcion=f"Prompt: {prompt_limpio[:120]} | Estilo: {NOMBRES_ESTILO.get(estilo, estilo)}"
            )
        except Exception:
            pass

        return {
            'success': True,
            'image_url': image_url,
            'filename': filename,
            'prompt_original': prompt_limpio,
            'prompt_final': prompt_final,
            'aspecto': aspecto_normalizado,
            'estilo': estilo,
            'estilo_nombre': NOMBRES_ESTILO.get(estilo, estilo),
            'ancho': ancho,
            'alto': alto,
        }

    except Exception as e:
        logger.error(f"[GeneradorImagen] Error general: {e}")
        return {
            'success': False,
            'error': f"No se pudo generar la imagen en este momento: {str(e)}"
        }
