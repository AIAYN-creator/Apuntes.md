# /// script
# requires-python = ">=3.12"
# dependencies = ["pymupdf", "pillow"]
# ///
"""Recorta regiones de un escaneo (PDF o imagen) a PNG.

Uso:
    # 1) Ver la página con una cuadrícula para estimar coordenadas
    uv run scripts/crop.py <escaneo> --page N --render <salida.png> [--grid] [--dpi 110]

    # 2) Recortar una región (coordenadas en fracciones 0-1 de la página)
    uv run scripts/crop.py <escaneo> --page N --box X0 Y0 X1 Y1 -o <crop-NN.png> [--dpi 200] [--pad 0.01]

--page empieza en 1 y se ignora para imágenes (png, jpg...).
stdout: ruta del PNG generado. Exit: 0 OK, 1 error de lectura, 2 uso incorrecto.
"""

import argparse
import sys
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

GRID_STEP = 0.1


def load_page(path: Path, page: int, dpi: int) -> Image.Image:
    """Rasteriza la página pedida (PDF) o abre la imagen tal cual."""
    if path.suffix.lower() == ".pdf":
        with pymupdf.open(path) as doc:
            if not 1 <= page <= doc.page_count:
                raise ValueError(f"el PDF tiene {doc.page_count} página(s), pediste la {page}")
            pix = doc[page - 1].get_pixmap(dpi=dpi)
            return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    img = Image.open(path)
    img.load()
    return img.convert("RGB")


def draw_grid(img: Image.Image) -> Image.Image:
    """Cuadrícula etiquetada cada 0.1 para que Claude estime las fracciones de --box."""
    img = img.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    font = ImageFont.load_default(size=max(12, w // 60))
    steps = round(1 / GRID_STEP)
    for i in range(1, steps):
        f = i * GRID_STEP
        x, y = round(f * w), round(f * h)
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 110), width=1)
        draw.line([(0, y), (w, y)], fill=(255, 0, 0, 110), width=1)
        label = f"{f:.1f}"
        draw.text((x + 3, 3), label, fill=(200, 0, 0, 255), font=font)
        draw.text((3, y + 3), label, fill=(200, 0, 0, 255), font=font)
    return img


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("scan", type=Path)
    parser.add_argument("--page", type=int, default=1)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--render", type=Path, metavar="SALIDA.png", help="rasteriza la página entera")
    mode.add_argument("--box", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    parser.add_argument("-o", "--output", type=Path, help="PNG de salida del recorte (con --box)")
    parser.add_argument("--grid", action="store_true", help="con --render: superpone la cuadrícula de coordenadas")
    parser.add_argument("--dpi", type=int, help="resolución de rasterizado de PDFs (110 con --render, 200 con --box)")
    parser.add_argument("--pad", type=float, default=0.01, help="margen extra alrededor de --box (fracción, def. 0.01)")
    args = parser.parse_args()

    if args.box is not None:
        if args.output is None:
            parser.error("--box necesita -o/--output")
        x0, y0, x1, y1 = args.box
        if not all(0 <= v <= 1 for v in args.box) or x0 >= x1 or y0 >= y1:
            parser.error("--box son fracciones 0-1 con X0 < X1 e Y0 < Y1")
    out = args.render or args.output
    if out.suffix.lower() != ".png":
        parser.error("la salida debe ser un .png")
    dpi = args.dpi or (110 if args.render else 200)

    if not args.scan.exists():
        print(f"ERROR: no existe {args.scan}", file=sys.stderr)
        return 1
    try:
        img = load_page(args.scan, args.page, dpi)
    except Exception as exc:  # PDF corrupto, imagen ilegible, página fuera de rango
        print(f"ERROR: no se pudo leer {args.scan}: {exc}", file=sys.stderr)
        return 1

    out.parent.mkdir(parents=True, exist_ok=True)
    if args.render:
        (draw_grid(img) if args.grid else img).save(out)
    else:
        w, h = img.size
        x0, y0, x1, y1 = args.box
        pad = args.pad
        box = (round(max(0.0, x0 - pad) * w), round(max(0.0, y0 - pad) * h),
               round(min(1.0, x1 + pad) * w), round(min(1.0, y1 + pad) * h))
        img.crop(box).save(out, optimize=True)

    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
