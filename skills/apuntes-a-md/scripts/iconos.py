# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf"]
# ///
"""Iconos de Bioicons con licencia controlada: buscar, descargar bajo demanda, registrar y pasar a PDF.

Uso:
    uv run scripts/iconos.py catalogo                       # descarga el catálogo (~290 KB)
    uv run scripts/iconos.py buscar TÉRMINO [...]           # busca en el catálogo descargado
    uv run scripts/iconos.py info NOMBRE [--autor A]        # licencia, autor, URL y tamaño (sin descargar)
    uv run scripts/iconos.py descargar NOMBRE [--autor A] [--fichero SVG]
    uv run scripts/iconos.py comprobar                      # ICONOS.md <-> iconos/
    uv run scripts/iconos.py pdf ICONO.svg -o salida.pdf [--paleta] [--sin-fondo]

Licencias: solo CC0, MIT, BSD y CC-BY 3.0/4.0. **CC-BY-SA nunca**: ni se descarga ni se registra.

- `catalogo` y `descargar` son las únicas órdenes que descargan algo. Quien use el
  script (persona o agente) pide permiso antes, diciendo nombre, origen y tamaño
  (los da `info`).
- `descargar` guarda el SVG original sin tocar en iconos/<licencia>/<Nombre>.svg y
  añade su fila a iconos/ICONOS.md. Nunca sobrescribe. Con --fichero registra un SVG
  que ya se ha descargado a mano.
- `comprobar` falla si hay un icono sin fila, una fila sin icono, una licencia que no
  coincide con su carpeta o algo CC-BY-SA.
- `pdf` convierte un icono a PDF vectorial (PyMuPDF) para componerlo en TikZ con
  \\includegraphics y etiquetas, como los recortes vectoriales. --paleta pasa sus colores
  saturados a los de la paleta (azul, rojo, verde, negro); los pastel se respetan.

Exit: 0 bien, 1 fallo (licencia, red, registro), 2 uso incorrecto.
"""

import argparse
import colorsys
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
ICONOS = SKILL / "iconos"
REGISTRO = ICONOS / "ICONOS.md"
CATALOGO = ICONOS / ".catalogo.json"
BASE = "https://raw.githubusercontent.com/duerrsimon/bioicons/main/static/icons"
CATALOGO_URL = f"{BASE}/icons.json"
LICENCIAS = {"cc-0": "CC0", "mit": "MIT", "bsd": "BSD", "cc-by-3.0": "CC-BY 3.0", "cc-by-4.0": "CC-BY 4.0"}
CABECERA = """# Iconos

Iconos de [Bioicons](https://bioicons.com/) usados en las figuras. Cada icono conserva su licencia original; esta tabla es su atribución.
Solo se admiten **CC0, MIT, BSD y CC-BY** (con atribución). **CC-BY-SA nunca.** La comprueba `scripts/iconos.py comprobar`.

| Archivo | Nombre en Bioicons | Autor | Licencia | Origen | Modificado | Usado en |
|---|---|---|---|---|---|---|
"""
FILA = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|")
PALETA = {"azul": (15, 77, 146), "rojo": (182, 67, 66), "verde": (59, 125, 59), "negro": (39, 39, 39)}


def error(msg: str, code: int = 1) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return code


def es_sa(licencia: str) -> bool:
    return "sa" in licencia.lower().replace("-", " ").split()


def url_de(e: dict) -> str:
    # En el repo de Bioicons los espacios del autor son "_" ("Marcel Tisch" -> Marcel_Tisch);
    # las tildes ("Cléber-Gomes") van codificadas en la URL
    partes = (e["license"], e["category"], e["author"].replace(" ", "_"), f"{e['name']}.svg")
    return BASE + "/" + "/".join(urllib.parse.quote(p) for p in partes)


def catalogo() -> list[dict] | None:
    if not CATALOGO.exists():
        return None
    return json.loads(CATALOGO.read_text(encoding="utf-8"))


def entrada(nombre: str, autor: str | None) -> tuple[dict | None, str]:
    cat = catalogo()
    if cat is None:
        return None, "falta el catálogo: `iconos.py catalogo` (descarga ~290 KB; pide permiso antes)"
    hits = [e for e in cat if e["name"] == nombre and (autor is None or e["author"] == autor)]
    if not hits:
        return None, f"«{nombre}» no está en el catálogo"
    if len(hits) > 1:
        return None, f"«{nombre}» es ambiguo; elige --autor entre {sorted(e['author'] for e in hits)}"
    return hits[0], ""


def filas() -> list[tuple[str, str, str, str]]:
    if not REGISTRO.exists():
        return []
    return [m.groups() for l in REGISTRO.read_text(encoding="utf-8").splitlines() if (m := FILA.match(l))]


def registrar(rel: str, e: dict) -> None:
    if not REGISTRO.exists():
        REGISTRO.parent.mkdir(parents=True, exist_ok=True)
        REGISTRO.write_text(CABECERA, encoding="utf-8", newline="\n")
    fila = f"| `{rel}` | {e['name']} | {e['author']} | {LICENCIAS[e['license']]} | [bioicons]({url_de(e)}) | no | — |\n"
    with REGISTRO.open("a", encoding="utf-8", newline="\n") as f:
        f.write(fila)


# ---------------------------------------------------------------- órdenes

def cmd_catalogo(_) -> int:
    try:
        datos = urllib.request.urlopen(CATALOGO_URL, timeout=30).read()
        n = len(json.loads(datos))
    except (urllib.error.URLError, ValueError) as e:
        return error(f"no se pudo descargar el catálogo: {e}")
    CATALOGO.parent.mkdir(parents=True, exist_ok=True)
    CATALOGO.write_bytes(datos)
    print(f"catálogo: {n} iconos, {len(datos) / 1024:.0f} KB → {CATALOGO}")
    return 0


def cmd_buscar(a) -> int:
    cat = catalogo()
    if cat is None:
        return error("falta el catálogo: `iconos.py catalogo` (descarga ~290 KB; pide permiso antes)")
    for t in a.terminos:
        hits = [e for e in cat if t.lower() in f"{e['name']} {e['category']}".lower()]
        print(f"\n### «{t}»: {len(hits)}")
        for e in hits[:25]:
            lic = e["license"]
            marca = "❌ CC-BY-SA, no se usa" if es_sa(lic) else ("✅" if lic in LICENCIAS else f"❓ {lic}")
            print(f"  {e['name']:<34} {lic:<10} {e['author']:<24} {e['category']:<22} {marca}")
    return 0


def cmd_info(a) -> int:
    e, msg = entrada(a.nombre, a.autor)
    if not e:
        return error(msg, 2)
    url = url_de(e)
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, method="HEAD"), timeout=30)
        tam = f"{int(r.headers.get('Content-Length', 0)) / 1024:.1f} KB"
    except urllib.error.URLError as err:
        tam = f"? ({err})"
    usable = "NO: CC-BY-SA" if es_sa(e["license"]) else ("sí" if e["license"] in LICENCIAS else "NO: licencia desconocida")
    print(f"nombre:   {e['name']}\nautor:    {e['author']}\nlicencia: {e['license']}  (usable: {usable})\n"
          f"categoría:{e['category']}\norigen:   {url}\ntamaño:   {tam}")
    return 0 if usable == "sí" else 1


def cmd_descargar(a) -> int:
    e, msg = entrada(a.nombre, a.autor)
    if not e:
        return error(msg, 2)
    if es_sa(e["license"]) or e["license"] not in LICENCIAS:
        return error(f"«{e['name']}» es {e['license']}: no se usa (solo CC0, MIT, BSD y CC-BY)")
    rel = f"{e['license']}/{e['name']}.svg"
    destino = ICONOS / rel
    if destino.exists() or any(f[0] == rel for f in filas()):
        return error(f"{rel} ya existe; no se sobrescribe")
    if a.fichero:
        datos = Path(a.fichero).read_bytes()
    else:
        try:
            datos = urllib.request.urlopen(url_de(e), timeout=30).read()
        except urllib.error.URLError as err:
            return error(f"no se pudo descargar {url_de(e)}: {err}")
    if b"<svg" not in datos[:4096]:
        return error("lo descargado no es un SVG")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_bytes(datos)
    registrar(rel, e)
    print(f"{rel}: {len(datos) / 1024:.1f} KB · {LICENCIAS[e['license']]} · {e['author']} → registrado en ICONOS.md")
    return 0


def cmd_comprobar(_) -> int:
    fallos = []
    registradas = filas()
    rels = [f[0] for f in registradas]
    for rel, nombre, autor, lic in registradas:
        if es_sa(lic) or "SA" in lic.upper().split("-"):
            fallos.append(f"{rel}: licencia {lic} (CC-BY-SA no se admite)")
        carpeta = rel.split("/")[0]
        if LICENCIAS.get(carpeta) != lic:
            fallos.append(f"{rel}: la fila dice {lic} pero está en la carpeta {carpeta}/")
        if not (ICONOS / rel).exists():
            fallos.append(f"{rel}: está en ICONOS.md pero el fichero no existe")
        if not autor or autor == "—":
            fallos.append(f"{rel}: sin autor (la atribución lo necesita)")
    for p in sorted(ICONOS.rglob("*.svg")):
        rel = p.relative_to(ICONOS).as_posix()
        if rel.split("/")[0] not in LICENCIAS:
            fallos.append(f"{rel}: carpeta de licencia no admitida")
        if rel not in rels:
            fallos.append(f"{rel}: icono sin fila en ICONOS.md")
    dup = {r for r in rels if rels.count(r) > 1}
    fallos += [f"{r}: fila repetida" for r in sorted(dup)]
    if fallos:
        print("ICONOS: FALLOS")
        for f in fallos:
            print(f"  ✗ {f}")
        return 1
    print(f"ICONOS: OK ({len(registradas)} iconos registrados, licencias correctas, ningún CC-BY-SA)")
    return 0


def a_paleta(m: re.Match) -> str:
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    rgb = tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hh, s, v = colorsys.rgb_to_hsv(*rgb)
    if s < 0.25:
        out = PALETA["negro"] if v < 0.5 else None
    elif v > 0.9 and s < 0.45:          # pastel: se respeta
        out = None
    else:
        hue = hh * 360
        clave = "rojo" if hue < 30 or hue >= 330 else "verde" if 70 <= hue < 170 else "azul" if 170 <= hue < 270 else None
        out = PALETA[clave] if clave else None
    return m.group(0) if out is None else "#%02x%02x%02x" % out


def css_en_linea(texto: str) -> str:
    """Copia las reglas de clase de los <style> (.st0{fill:#FCFCFC}) al style de cada elemento.

    Los SVG exportados de Illustrator dan los colores por clase y PyMuPDF ignora los
    <style>: sin esto salen negros o vacíos (DNA_double_helix, Chromosome)."""
    reglas: dict[str, str] = {}
    for bloque in re.findall(r"<style[^>]*>(.*?)</style>", texto, flags=re.S):
        bloque = re.sub(r"/\*.*?\*/|<!\[CDATA\[|\]\]>", "", bloque, flags=re.S)
        for selectores, decl in re.findall(r"([^{}]+)\{([^}]*)\}", bloque):
            for sel in selectores.split(","):
                if m := re.fullmatch(r"\s*\.([\w-]+)\s*", sel):
                    reglas[m.group(1)] = reglas.get(m.group(1), "") + decl.strip().rstrip(";") + ";"
    if not reglas:
        return texto

    def poner(m: re.Match) -> str:
        etiqueta = m.group(0)
        clases = re.search(r'\sclass="([^"]*)"', etiqueta)
        decl = "".join(reglas.get(c, "") for c in clases.group(1).split()) if clases else ""
        if not decl:
            return etiqueta
        if (st := re.search(r'\sstyle="([^"]*)"', etiqueta)):     # el style propio manda: va después
            return etiqueta.replace(st.group(0), f' style="{decl}{st.group(1)}"')
        return re.sub(r"(/?>)$", f' style="{decl}"\\1', etiqueta)

    return re.sub(r"<[a-zA-Z][^<>]*\sclass=\"[^\"]*\"[^<>]*>", poner, texto)


def sin_illustrator(texto: str) -> str:
    """Illustrator mete el dibujo en un <switch> cuyo primer hijo es un <foreignObject>
    con datos propios; PyMuPDF elige ese hijo y el icono sale vacío."""
    texto = re.sub(r"<foreignObject\b.*?</foreignObject>", "", texto, flags=re.S)
    return re.sub(r"</?switch\b[^>]*>", "", texto)


def sin_fondo(texto: str) -> str:
    """Quita los rellenos casi blancos (fondos tipo lámina): en modo oscuro serían un recuadro."""
    def blanco(h: str) -> bool:
        h = "".join(c * 2 for c in h) if len(h) == 3 else h
        return all(int(h[i:i + 2], 16) >= 0xF0 for i in (0, 2, 4))

    def quitar(m: re.Match) -> str:
        f = re.search(r'fill(?:="|:\s*)#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b', m.group(0))
        return "" if f and blanco(f.group(1)) else m.group(0)

    return re.sub(r"<(?:path|rect|polygon)\b[^>]*/>", quitar, texto)


def caja_visible(pagina):
    """Rectángulo (en pt) de los píxeles no transparentes de la página, con 1 pt de margen."""
    import pymupdf

    escala = 2
    pix = pagina.get_pixmap(alpha=True, matrix=pymupdf.Matrix(escala, escala))
    a = pix.samples[pix.n - 1::pix.n]                       # canal alfa
    w, h = pix.width, pix.height
    filas = [y for y in range(h) if any(a[y * w:(y + 1) * w])]
    if not filas:
        return None
    cols = [x for x in range(w) if any(a[x::w][filas[0]:filas[-1] + 1])]
    r = pymupdf.Rect(cols[0], filas[0], cols[-1] + 1, filas[-1] + 1) / escala
    return (r + (-1, -1, 1, 1)) & pagina.rect


def cmd_pdf(a) -> int:
    import pymupdf

    svg = Path(a.svg)
    if not svg.is_file():
        return error(f"no existe {svg}", 2)
    texto = css_en_linea(sin_illustrator(svg.read_text(encoding="utf-8")))
    if a.sin_fondo:
        texto = sin_fondo(texto)
    if a.paleta:
        texto = re.sub(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b", a_paleta, texto)
    try:
        doc = pymupdf.open(stream=texto.encode("utf-8"), filetype="svg")
        tmp = pymupdf.open("pdf", doc.convert_to_pdf())
        # Recorta a lo que se ve: algunos iconos vienen sobre una página A4 con el dibujo en
        # una esquina, o son un PNG con márgenes transparentes. Se mira el canal alfa.
        caja = caja_visible(tmp[0])
        if caja is None:
            return error(f"{svg.name}: el PDF ha salido vacío (¿estructura SVG no soportada?)")
        for im in tmp[0].get_image_info():
            print(f"AVISO: {svg.name} no es vectorial: lleva una imagen de {im['width']}×{im['height']} px. "
                  f"Se ve bien a tamaño de pantalla, pero no escala como un vector.", file=sys.stderr)
        pdf = pymupdf.open()
        pdf.new_page(width=caja.width, height=caja.height).show_pdf_page(
            pymupdf.Rect(0, 0, caja.width, caja.height), tmp, 0, clip=caja)
    except Exception as e:  # PyMuPDF lanza tipos variados con SVG raros
        return error(f"PyMuPDF no pudo convertir {svg.name}: {e}")
    salida = Path(a.o)
    salida.parent.mkdir(parents=True, exist_ok=True)
    pdf.save(salida)
    extras = [x for x, on in (("paleta", a.paleta), ("sin fondo", a.sin_fondo)) if on]
    print(f"{salida}: {caja.width:.0f}×{caja.height:.0f} pt" + (f" ({', '.join(extras)})" if extras else ""))
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)
    sub.add_parser("catalogo", help="descarga el catálogo de Bioicons")
    b = sub.add_parser("buscar", help="busca por nombre o categoría")
    b.add_argument("terminos", nargs="+")
    for nombre in ("info", "descargar"):
        s = sub.add_parser(nombre)
        s.add_argument("nombre")
        s.add_argument("--autor")
        if nombre == "descargar":
            s.add_argument("--fichero", help="registra un SVG ya descargado a mano en vez de descargarlo")
    sub.add_parser("comprobar", help="comprueba ICONOS.md contra iconos/")
    d = sub.add_parser("pdf", help="SVG -> PDF vectorial para \\includegraphics")
    d.add_argument("svg")
    d.add_argument("-o", required=True)
    d.add_argument("--paleta", action="store_true")
    d.add_argument("--sin-fondo", action="store_true", help="quita los rellenos casi blancos (fondos)")
    a = p.parse_args()
    return {"catalogo": cmd_catalogo, "buscar": cmd_buscar, "info": cmd_info, "descargar": cmd_descargar,
            "comprobar": cmd_comprobar, "pdf": cmd_pdf}[a.orden](a)


if __name__ == "__main__":
    sys.exit(main())
