#!/usr/bin/env python3
"""
Genera una copia de index.html por sección con sus propias etiquetas de vista previa
(Open Graph / Twitter) para que Discord, X, WhatsApp, etc. muestren la tarjeta correcta.

Uso (desde la carpeta raíz del repo, donde está index.html):
    python3 generar_previews.py

Vuelve a ejecutarlo cada vez que cambies index.html (las copias deben mantenerse al día).
"""
import re, html
from pathlib import Path
from urllib.parse import quote

SITE = "https://lmcstudios.art"
IMG_DEFAULT = "assets/avatars/banerlmcst.png"
SUFFIX = " | LMC Studios ™"
HOME_TITLE = "LMC Studios ™ | Estudio creativo de eventos y experiencias de Minecraft"

# ---- Edita aquí título / descripción de cada sección ----
# La imagen de cada sección (assets/og/<sección>.png, 1200x630) se genera con: python3 tools/make_og.py
SECTIONS = {
    "servicios": ("Servicios", "De la idea al evento: diseño, desarrollo, producción y promoción de eventos y servidores de Minecraft.", None),
    "proyectos": ("Proyectos", "Eventos, servidores y experiencias de Minecraft en las que ha participado LMC Studios ™, solo o junto a otros equipos.", None),
    "launcher": ("LMC Launcher (beta)", "Nuestro launcher está en beta, de uso exclusivo para eventos de LMC Studios ™.", None),
    "estudio": ("Equipo", "Conoce al equipo de desarrollo y administración detrás de cada evento de LMC Studios ™.", None),
    "partners": ("Partners", "Los partners y patrocinadores que apoyan a LMC Studios ™.", None),
    "contacto": ("Contacto", "¿Tienes una idea para tu evento, servidor o experiencia de Minecraft? Escríbenos y la hacemos realidad.", None),
    "aviso-legal": ("Aviso legal", "Aviso legal de LMC Studios ™.", None),
    "privacidad": ("Aviso de privacidad", "Cómo LMC Studios ™ trata tus datos personales.", None),
    "cookies": ("Política de cookies", "Información sobre las cookies que usa lmcstudios.art.", None),
}

def esc(s): return html.escape(s, quote=True)
def img_url(rel): return f"{SITE}/{quote(rel)}"

def set_meta(doc, *, title, desc, url, image, alt, dims=None):
    def sub(pattern, repl):
        nonlocal doc
        doc, n = re.subn(pattern, lambda m: repl, doc, count=1)
        assert n, f"No se encontró: {pattern}"
    sub(r"<title>.*?</title>", f"<title>{esc(title)}</title>")
    sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{esc(desc)}">')
    sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">')
    sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{esc(title)}">')
    sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{esc(desc)}">')
    sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">')
    sub(r'<meta property="og:image" content="[^"]*">', f'<meta property="og:image" content="{image}">')
    sub(r'<meta property="og:image:alt" content="[^"]*">', f'<meta property="og:image:alt" content="{esc(alt)}">')
    sub(r'<meta name="twitter:title" content="[^"]*">', f'<meta name="twitter:title" content="{esc(title)}">')
    sub(r'<meta name="twitter:description" content="[^"]*">', f'<meta name="twitter:description" content="{esc(desc)}">')
    sub(r'<meta name="twitter:image" content="[^"]*">', f'<meta name="twitter:image" content="{image}">')
    sub(r'<meta name="twitter:image:alt" content="[^"]*">', f'<meta name="twitter:image:alt" content="{esc(alt)}">')
    # medidas de la imagen: solo se declaran cuando se conocen (las de las secciones, 1200x630)
    doc = re.sub(r'<meta property="og:image:(?:width|height)" content="[^"]*">\n?', '', doc)
    if dims:
        doc = re.sub(r'(<meta property="og:image" content="[^"]*">)', lambda m: m.group(1) + f'\n<meta property="og:image:width" content="{dims[0]}">\n<meta property="og:image:height" content="{dims[1]}">', doc, count=1)
    return doc

def patch_shared(doc):
    # El título de inicio ya no depende del <title> de la página en la que se cargó
    doc = re.sub(r"const base = document\.title;", f"const base = {HOME_TITLE!r};".replace("'", "'"), doc, count=1)
    # Con carpetas, GitHub Pages sirve /seccion/ (con barra final): normalizar al comparar
    doc = doc.replace("if (href === location.pathname) {",
                      "if (href === location.pathname.replace(/(.)\\/+$/, '$1')) {", 1)
    return doc

def parse_projects(doc):
    out = []
    for m in re.finditer(r"^  \{name:'((?:[^'\\]|\\.)*)'(.*?)(?=^  \{name:'|^\];)", doc, re.S | re.M):
        name = m.group(1).replace("\\'", "'")
        body = m.group(2)
        g = lambda k: (re.search(k + r":'((?:[^'\\]|\\.)*)'", body) or [None, ""])[1].replace("\\'", "'")
        slug = g("slug") or re.sub(r"^-|-$", "", re.sub(r"[^a-z0-9]+", "-",
               __import__("unicodedata").normalize("NFD", name).encode("ascii", "ignore").decode().lower()))
        out.append(dict(name=name, slug=slug, img=g("img"), desc=g("desc"), censored="censored:true" in body))
    return out

def main():
    root = Path(__file__).parent
    src = (root / "index.html").read_text(encoding="utf-8")
    src = patch_shared(src)
    (root / "index.html").write_text(src, encoding="utf-8")

    def write(path, content):
        p = root / path / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        print("OK", path)

    for slug, (name, desc, image) in SECTIONS.items():
        write(slug, set_meta(src, title=name + SUFFIX, desc=desc, url=f"{SITE}/{slug}",
                             image=img_url(image or f"assets/og/{slug}.png"), alt=f"{name} · LMC Studios ™", dims=(1200, 630)))

    for p in parse_projects(src):
        if p["censored"] or not p["img"] or p["img"].startswith(".."):
            image, title, desc = img_url(IMG_DEFAULT), "Próximamente" + SUFFIX, "Algo nuevo viene de LMC Studios ™. ¿Estás preparado?"
        else:
            image, title, desc = img_url("assets/avatars/" + p["img"]), p["name"] + SUFFIX, p["desc"] or "Proyecto de LMC Studios ™."
        write(f"proyecto/{p['slug']}", set_meta(src, title=title, desc=desc, url=f"{SITE}/proyecto/{p['slug']}",
                                                 image=image, alt=p["name"]))

if __name__ == "__main__":
    main()
