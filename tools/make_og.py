#!/usr/bin/env python3
"""Genera las imagenes de vista previa (Discord, X, WhatsApp...) de cada seccion de lmcstudios.art.
Usa el logo de LMC Studios de assets/avatars/banerlmcst.png, el nombre de la seccion en grande,
la direccion debajo y un detalle en rojo. Medida 1200x630. Salida: assets/og/<seccion>.png
Los nombres se editan en NAMES (abajo). Las paginas de proyecto siguen usando la imagen de cada proyecto.
Uso (desde la carpeta del sitio): python3 tools/make_og.py   y luego   python3 generar_previews.py
Necesita Pillow:  pip install pillow"""
import pathlib
import pathlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H = 1200, 630
RED = (179, 38, 45)
def font(size, weight=800, here=None):
    here = pathlib.Path(here or __file__).resolve().parent
    for p, var in ((here / 'BricolageGrotesque.ttf', True), (pathlib.Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'), False)):
        try:
            f = ImageFont.truetype(str(p), size)
            if var:
                vals = []
                for a in f.get_variation_axes():
                    n = a['name'].decode() if isinstance(a['name'], bytes) else a['name']
                    vals.append(weight if 'eight' in n else (min(max(size / 4, a['minimum']), a['maximum']) if 'ptical' in n else a['default']))
                f.set_variation_by_axes(vals)
            return f
        except Exception:
            continue
    return ImageFont.load_default()
def tw(d, text, f, tracking):
    return sum(d.textlength(c, font=f) for c in text) + tracking * (len(text) - 1)
def spaced(d, cx, cy, text, f, fill, tracking=0):
    x = cx - tw(d, text, f, tracking) / 2
    for c in text:
        d.text((x, cy), c, font=f, fill=fill, anchor='lm')
        x += d.textlength(c, font=f) + tracking
def fit(d, text, maxw, start, minsize, tracking, weight=800, here=None):
    s = start
    while True:
        f = font(s, weight, here)
        if tw(d, text, f, tracking) <= maxw or s <= minsize: return f, s
        s -= 4

root = pathlib.Path(__file__).resolve().parent.parent
SITE = 'lmcstudios.art'
TAGLINE = 'EVENTOS Y EXPERIENCIAS DE MINECRAFT'
NAMES = {  # carpeta -> texto que sale en la imagen
    'inicio': None,
    'servicios': 'SERVICIOS', 'proyectos': 'PROYECTOS', 'launcher': 'LAUNCHER', 'estudio': 'EQUIPO',
    'partners': 'PARTNERS', 'contacto': 'CONTACTO', 'aviso-legal': 'AVISO LEGAL',
    'privacidad': 'PRIVACIDAD', 'cookies': 'COOKIES',
}
GREY = (139, 144, 150)

src = Image.open(root / 'assets' / 'avatars' / 'banerlmcst.png').convert('RGB')
sx = src.width / 1456
logo = src.crop((round(135 * sx), round(340 * sx), round(1330 * sx), round(540 * sx)))   # "LMC [gato] STUDIOS"
ImageDraw.Draw(logo).rectangle((round(850 * sx) - round(135 * sx), 0, round(985 * sx) - round(135 * sx), round(357 * sx) - round(340 * sx)), fill=(0, 0, 0))   # quita la punta del logo de partner

def logo_w(w):
    return logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)

out = root / 'assets' / 'og'
out.mkdir(parents=True, exist_ok=True)
for slug, name in NAMES.items():
    im = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(im)
    addr = SITE if slug == 'inicio' else f'{SITE}/{slug}'
    lg = logo_w(1000 if slug == 'inicio' else 560)
    if slug == 'inicio':
        f, s = font(34, 500), 34
        items = [('img', lg.height), ('gap', 50), ('rule', 3), ('gap', 40), ('txt', 34), ('gap', 34), ('addr', 30)]
    else:
        f, s = fit(d, name, 900, 120, 56, 6)
        items = [('img', lg.height), ('gap', 44), ('rule', 3), ('gap', 38), ('txt', s), ('gap', 34), ('addr', 30)]
    total = sum(h for _, h in items); y = (H - total) // 2
    for kind, h in items:
        if kind == 'img': im.paste(lg, ((W - lg.width) // 2, y))
        elif kind == 'rule': d.rectangle((W // 2 - 28, y, W // 2 + 28, y + 2), fill=RED)
        elif kind == 'txt':
            if slug == 'inicio': spaced(d, W // 2, y + h // 2, TAGLINE, font(32, 600), (230, 232, 235), 7)
            else: spaced(d, W // 2, y + h // 2, name, f, (244, 245, 247), 6)
        elif kind == 'addr': spaced(d, W // 2, y + h // 2, addr, font(28, 500), GREY, 1)
        y += h
    im.save(out / f'{slug}.png', optimize=True)
    print('og:', slug)
