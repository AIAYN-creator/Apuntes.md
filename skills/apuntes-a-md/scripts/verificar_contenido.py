# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Comprueba que la estética no ha cambiado el contenido de una nota.

Uso:
    uv run scripts/verificar_contenido.py <transcripcion.md> <nota-final.md>

Compara las PALABRAS de las dos notas, en orden, ignorando todo lo que es forma:
frontmatter, formato Markdown (negritas, títulos, tablas, viñetas), comentarios
%% %%, el índice, las imágenes (y su alt), las líneas `smiles:`/`estereo:` y las
cabeceras de los callouts con etiqueta fija (Índice, Definición, Importante,
Fórmula, Ficha, Resolución, sesión). Un enlace interno [[destino|texto]] cuenta como `texto`,
así que la nota sigue verificándose después de enlazarla.

stdout: "OK: mismo contenido (N palabras, mismo orden)" o la lista de diferencias.
Exit: 0 mismo contenido, 1 hay diferencias, 2 uso incorrecto.
"""

import argparse
import difflib
import re
import sys
import unicodedata
from pathlib import Path

# Tipos y títulos de callout que la estética puede añadir (SKILL.md, sección 8.2)
ETIQUETAS = {"abstract", "indice", "índice", "definicion", "definición", "importante",
             "formula", "fórmula", "ficha", "sesion", "sesión", "resolucion", "resolución"}

TOKEN = re.compile(r"[\w$\\{}^()\[\]+−\-<>~'.,;:!?/⟹→·αβγδλμπσχΔ₀-₉⁺⁻]+")


def palabras(path: Path) -> list[str]:
    t = path.read_text(encoding="utf-8")
    t = re.sub(r"\A---\n.*?\n---\n", "", t, flags=re.S)            # frontmatter
    t = re.sub(r"%%.*?%%", " ", t, flags=re.S)                      # comentarios de Obsidian
    lineas = []
    for linea in t.splitlines():
        s = linea.lstrip("> ").strip()
        if s.startswith(("`smiles:", "`estereo:", "- [[#")):        # ficha e índice
            continue
        m = re.match(r"\[!(\w+)\][-+]?\s*(.*)", s)                  # cabecera de callout
        if m:
            tipo, titulo = m.group(1).lower(), m.group(2).strip()
            # Se ignora la etiqueta fija; cualquier otro título es contenido y se compara
            # (un "[!resolucion]- Solución" añadiría una palabra). La sesión lleva la fecha de la hoja.
            if titulo.lower() in ETIQUETAS or not titulo or tipo in ("sesion", "sesión"):
                continue
            s = titulo                                              # [!warning] Dudoso: … sí es contenido
        s = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", s)                 # imágenes Markdown, alt incluido
        s = re.sub(r"!\[\[[^\]]*\]\]", " ", s)                      # imágenes ![[...]] (Obsidian las crea al redimensionar)
        s = re.sub(r"\[\[[^\]|]*?\\?\|([^\]]*)\]\]", r"\1", s)      # enlaces [[destino|texto]] (y \| en tablas): cuenta el texto
        s = re.sub(r"\[\[([^\]|]*)\]\]", r"\1", s)                  # enlaces [[destino]]
        lineas.append(s)
    t = unicodedata.normalize("NFC", "\n".join(lineas))
    t = re.sub(r"[*_=`#|]|:?-{3,}:?", " ", t)                       # marcas de formato y tablas
    resultado = []
    for w in TOKEN.findall(t):
        if w == "-":                                                # viñeta
            continue
        w = w.replace("$$", "").strip(".,;:")                       # delimitadores y puntuación de borde
        if w:
            resultado.append(w)
    return resultado


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("transcripcion", type=Path)
    parser.add_argument("nota", type=Path)
    parser.add_argument("--contexto", type=int, default=6, help="palabras de contexto en cada diferencia")
    args = parser.parse_args()
    for p in (args.transcripcion, args.nota):
        if not p.is_file():
            parser.error(f"no existe: {p}")

    a, b = palabras(args.transcripcion), palabras(args.nota)
    if a == b:
        print(f"OK: mismo contenido ({len(a)} palabras, mismo orden)")
        return 0

    print(f"DIFERENCIAS: transcripción {len(a)} palabras, nota {len(b)} palabras")
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        antes = " ".join(a[max(0, i1 - args.contexto):i1])
        print(f"\n  [{op}] tras «…{antes}»")
        print(f"    transcripción: {' '.join(a[i1:i2]) or '∅'}")
        print(f"    nota:          {' '.join(b[j1:j2]) or '∅'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
