# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf"]
# ///
"""Recorte VECTORIAL: exporta a SVG los trazos de una zona de un PDF de tableta.

Uso:
    uv run scripts/recorte_vectorial.py <apuntes.pdf> --page N --box X0 Y0 X1 Y1 -o <rec-NN-desc.svg>
                                        [--paleta] [--tocar] [--preview]

Para dibujos figurativos de apuntes hechos en tableta (GoodNotes, Notability…), cuyo PDF
guarda cada trazo como vector: el resultado es el dibujo del autor, exacto y nítido a
cualquier tamaño. Si el PDF es un escaneo (imagen), no hay trazos: usa crop.py.

--box      fracciones 0-1 de la página (como crop.py; léelas en su cuadrícula).
--tocar    incluye también los trazos que solo tocan la caja (por defecto, solo los que
           caen enteros dentro, para no arrastrar texto vecino).
--paleta   pasa los colores saturados a la paleta Apuntes.md (azul, rojo, verde, negro).
           Los rellenos claros (pastel) se mantienen.
--preview  genera además un PNG del SVG resultante, para revisarlo a ojo.

stdout: ruta del SVG (y del PNG). stderr: avisos.
Exit: 0 OK, 1 sin trazos vectoriales en la caja o PDF ilegible, 2 uso incorrecto.
"""

import argparse
import colorsys
import sys
import tempfile
from pathlib import Path

import pymupdf

PALETA = {"azul": (15, 77, 146), "rojo": (182, 67, 66), "verde": (59, 125, 59), "negro": (39, 39, 39)}


def a_paleta(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    """Color saturado -> el de la paleta con el mismo tono; neutros oscuros -> negro; pastel, igual."""
    h, s, v = colorsys.rgb_to_hsv(*rgb)
    if s < 0.25:
        return tuple(c / 255 for c in PALETA["negro"]) if v < 0.5 else rgb
    if v > 0.9 and s < 0.45:  # relleno claro (bandas de color, sombreados): se respeta
        return rgb
    hue = h * 360
    if hue < 25 or hue >= 330:
        clave = "rojo"
    elif 70 <= hue < 170:
        clave = "verde"
    elif 170 <= hue < 270:
        clave = "azul"
    else:
        return rgb
    return tuple(c / 255 for c in PALETA[clave])


def hex_(rgb) -> str:
    return "#%02x%02x%02x" % tuple(round(255 * c) for c in rgb[:3])


def trazado(d: dict) -> str:
    """Un dibujo de PyMuPDF -> atributo d de SVG, como UN trazado continuo."""
    cmds, actual = [], None

    def mover(p):
        nonlocal actual
        if actual is None or abs(actual.x - p.x) > 0.01 or abs(actual.y - p.y) > 0.01:
            cmds.append(f"M{p.x:.1f} {p.y:.1f}")

    for it in d["items"]:
        if it[0] == "l":
            mover(it[1]); cmds.append(f"L{it[2].x:.1f} {it[2].y:.1f}"); actual = it[2]
        elif it[0] == "c":
            p, c1, c2, q = it[1:5]
            mover(p); cmds.append(f"C{c1.x:.1f} {c1.y:.1f} {c2.x:.1f} {c2.y:.1f} {q.x:.1f} {q.y:.1f}"); actual = q
        elif it[0] == "re":
            r = it[1]; cmds.append(f"M{r.x0:.1f} {r.y0:.1f}H{r.x1:.1f}V{r.y1:.1f}H{r.x0:.1f}Z"); actual = None
        elif it[0] == "qu":
            q = it[1]
            cmds.append(f"M{q.ul.x:.1f} {q.ul.y:.1f}L{q.ur.x:.1f} {q.ur.y:.1f}L{q.lr.x:.1f} {q.lr.y:.1f}L{q.ll.x:.1f} {q.ll.y:.1f}Z")
            actual = None
    if d.get("closePath"):
        cmds.append("Z")
    return "".join(cmds)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--page", type=int, required=True)
    ap.add_argument("--box", type=float, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--paleta", action="store_true")
    ap.add_argument("--tocar", action="store_true")
    ap.add_argument("--preview", action="store_true")
    a = ap.parse_args()

    x0, y0, x1, y1 = a.box
    if not all(0 <= v <= 1 for v in a.box) or x0 >= x1 or y0 >= y1:
        ap.error("--box son fracciones 0-1 con X0 < X1 e Y0 < Y1")
    if a.output.suffix.lower() != ".svg":
        ap.error("la salida debe ser un .svg")
    try:
        doc = pymupdf.open(a.pdf)
        page = doc[a.page - 1]
    except Exception as exc:
        print(f"ERROR: no se pudo leer {a.pdf} pág. {a.page}: {exc}", file=sys.stderr)
        return 1

    W, H = page.rect.width, page.rect.height
    caja = pymupdf.Rect(x0 * W, y0 * H, x1 * W, y1 * H)
    dibujos = page.get_drawings()
    if not dibujos:
        print("ERROR: esta página no tiene trazos vectoriales (¿escaneo en imagen?). Usa crop.py.", file=sys.stderr)
        return 1
    elegidos = [d for d in dibujos if (d["rect"].intersects(caja) if a.tocar else caja.contains(d["rect"]))]
    if not elegidos:
        print("ERROR: ningún trazo cae dentro de la caja. Revisa --box en la cuadrícula o prueba --tocar.", file=sys.stderr)
        return 1

    # Ajusta el lienzo a lo que de verdad se ha recortado, con un pequeño margen
    marco = pymupdf.Rect(elegidos[0]["rect"])
    for d in elegidos[1:]:
        marco |= d["rect"]
    marco = marco + (-4, -4, 4, 4)

    partes = []
    for d in elegidos:
        trazo, relleno = d.get("color"), d.get("fill")
        if a.paleta:
            trazo = a_paleta(trazo) if trazo else None
            relleno = a_paleta(relleno) if relleno else None
        attrs = [f'd="{trazado(d)}"', f'fill="{hex_(relleno) if relleno else "none"}"']
        if relleno and d.get("fill_opacity", 1) < 1:
            attrs.append(f'fill-opacity="{d["fill_opacity"]:.2f}"')
        if trazo:
            attrs += [f'stroke="{hex_(trazo)}"', f'stroke-width="{(d.get("width") or 1):.2f}"',
                      'stroke-linecap="round"', 'stroke-linejoin="round"']
            if d.get("stroke_opacity", 1) < 1:
                attrs.append(f'stroke-opacity="{d["stroke_opacity"]:.2f}"')
        partes.append(f'<path {" ".join(attrs)}/>')

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{marco.x0:.1f} {marco.y0:.1f} '
           f'{marco.width:.1f} {marco.height:.1f}" width="{marco.width * 2:.0f}" height="{marco.height * 2:.0f}">\n'
           + "\n".join(partes) + "\n</svg>\n")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(svg, encoding="utf-8")
    print(a.output)
    print(f"{len(elegidos)} trazos, {len(svg) // 1024} KB", file=sys.stderr)

    if a.preview:
        png = Path(tempfile.gettempdir()) / f"{a.output.stem}-preview.png"
        vista = pymupdf.open(stream=svg.encode("utf-8"), filetype="svg")
        vista[0].get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5), alpha=False).save(png)
        print(png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
