#!/usr/bin/env bash
# TikZ/chemfig (.tex standalone completo) -> .svg al lado, con el mismo nombre base.
#
# Uso:
#   bash scripts/tikz2svg.sh <ruta/fig-NN-desc.tex> [--preview]
#
# Cadena: pdflatex -> dvisvgm --pdf --no-fonts --exact-bbox (fallback: pdftocairo -svg).
# Los auxiliares (.aux, .log, .pdf) van a un temporal: assets/ solo recibe el .svg.
# stdout: ruta del SVG (y del PNG de preview si se pide).
# stderr: errores de LaTeX (líneas '!' del log con contexto).
# Exit: 0 OK, 1 fallo de compilación/conversión, 2 uso incorrecto.

set -uo pipefail

usage() { echo "uso: bash scripts/tikz2svg.sh <figura.tex> [--preview]" >&2; exit 2; }

tex="" preview=0
for arg in "$@"; do
  case "$arg" in
    --preview) preview=1 ;;
    -h|--help) usage ;;
    -*) echo "opción desconocida: $arg" >&2; usage ;;
    *) [[ -z "$tex" ]] && tex="$arg" || usage ;;
  esac
done
[[ -n "$tex" ]] || usage
[[ -f "$tex" ]] || { echo "no existe: $tex" >&2; exit 2; }
[[ "$tex" == *.tex ]] || { echo "la entrada debe ser un .tex" >&2; exit 2; }

for cmd in pdflatex dvisvgm pdftocairo; do
  command -v "$cmd" >/dev/null || { echo "falta '$cmd' en el PATH (¿MiKTeX instalado?)" >&2; exit 1; }
done

# MiKTeX es nativo de Windows: necesita rutas C:\..., no /c/...
winpath() { if command -v cygpath >/dev/null; then cygpath -w "$1"; else echo "$1"; fi; }

dir="$(cd "$(dirname "$tex")" && pwd)"
name="$(basename "$tex" .tex)"
svg="$dir/$name.svg"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# Compilar desde el directorio del .tex por si hace \input de algo relativo
(
  cd "$dir" &&
  pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory="$(winpath "$tmp")" "$name.tex" >/dev/null 2>&1
)
pdf="$tmp/$name.pdf"
if [[ ! -s "$pdf" ]]; then
  echo "ERROR: pdflatex falló al compilar $tex" >&2
  if [[ -f "$tmp/$name.log" ]]; then
    grep -A4 '^!' "$tmp/$name.log" | head -30 >&2
  fi
  exit 1
fi

pages="$(pdfinfo "$(winpath "$pdf")" 2>/dev/null | awk '/^Pages:/ {print $2}')"
if [[ -n "$pages" && "$pages" != "1" ]]; then
  echo "AVISO: el PDF tiene $pages páginas; solo se convierte la primera. ¿Usas la opción 'tikz' de standalone?" >&2
fi

if ! dvisvgm --pdf --no-fonts --exact-bbox --page=1 -o "$(winpath "$svg")" "$(winpath "$pdf")" >/dev/null 2>&1 \
   || [[ ! -s "$svg" ]]; then
  echo "AVISO: dvisvgm falló, uso pdftocairo como fallback" >&2
  pdftocairo -svg -f 1 -l 1 "$(winpath "$pdf")" "$(winpath "$svg")" || { echo "ERROR: no se pudo convertir a SVG" >&2; exit 1; }
fi

winpath "$svg"

if (( preview )); then
  png_base="$(winpath "$(dirname "$tmp")")\\$name-preview"
  pdftocairo -png -r 200 -singlefile "$(winpath "$pdf")" "$png_base"
  echo "$png_base.png"
fi
