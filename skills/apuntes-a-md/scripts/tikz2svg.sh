#!/usr/bin/env bash
# TikZ/chemfig (.tex standalone completo) -> .svg al lado, con el mismo nombre base.
#
# Uso:
#   bash scripts/tikz2svg.sh <ruta/fig-NN-desc.tex> [--preview]
#
# Cadena: pdflatex -> dvisvgm --pdf --no-fonts --exact-bbox (fallback: pdftocairo -svg).
# Los auxiliares (.aux, .log, .pdf) van a un temporal: assets/ solo recibe el .svg.
# --preview: PNG del SVG FINAL renderizado con Edge/Chrome headless (lo que verá Obsidian).
# Falla (exit 1) si el PDF lleva fuentes Type 3, porque su texto se perdería en el SVG.
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

# Compilar desde el directorio del .tex por si hace \input de algo relativo.
# \chemmove y "remember picture" necesitan DOS pasadas: en la primera las flechas
# no saben aún dónde están los átomos y salen descolocadas (sin dar error).
pasadas=1
grep -qE '\\chemmove|remember picture' "$tex" && pasadas=2
for ((i = 1; i <= pasadas; i++)); do
  (
    cd "$dir" &&
    pdflatex -interaction=nonstopmode -halt-on-error \
      -output-directory="$(winpath "$tmp")" "$name.tex" >/dev/null 2>&1
  )
done
pdf="$tmp/$name.pdf"
if [[ ! -s "$pdf" ]]; then
  echo "ERROR: pdflatex falló al compilar $tex" >&2
  if [[ -f "$tmp/$name.log" ]]; then
    grep -A4 '^!' "$tmp/$name.log" | head -30 >&2
  fi
  exit 1
fi

# Fuentes Type 3 (bitmap): dvisvgm las descarta en silencio y el SVG sale sin texto
# aunque el PDF se vea bien. Pasa con T1 sin una fuente vectorial (falta \usepackage{lmodern}).
type3="$(pdffonts "$(winpath "$pdf")" 2>/dev/null | grep -c 'Type 3')"
if [[ "$type3" != "0" ]]; then
  echo "ERROR: el PDF usa fuentes Type 3 (bitmap) y el texto se perdería en el SVG." >&2
  echo "       Añade \\usepackage{lmodern} tras \\usepackage[T1]{fontenc} (la plantilla ya lo trae)." >&2
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
  # El preview es del SVG FINAL (lo que verá Obsidian), no del PDF intermedio:
  # un fallo de conversión (texto perdido) solo se ve aquí. Se renderiza con Edge/Chrome headless.
  png="$(winpath "$(dirname "$tmp")")\\$name-preview.png"
  browser=""
  for b in "/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" \
           "/c/Program Files/Microsoft/Edge/Application/msedge.exe" \
           "/c/Program Files/Google/Chrome/Application/chrome.exe" \
           "$(command -v chromium 2>/dev/null)" "$(command -v google-chrome 2>/dev/null)"; do
    [[ -n "$b" && -x "$b" ]] && { browser="$b"; break; }
  done
  if [[ -n "$browser" ]]; then
    # Tamaño de ventana = tamaño del SVG (pt -> px a 96 ppp) más un margen
    read -r w h < <(head -c 600 "$svg" | sed -n "s/.*width='\([0-9.]*\)pt' height='\([0-9.]*\)pt'.*/\1 \2/p")
    w=$(awk -v v="${w:-600}" 'BEGIN{printf "%d", v*96/72+20}'); h=$(awk -v v="${h:-400}" 'BEGIN{printf "%d", v*96/72+20}')
    url="file:///$(winpath "$svg" | tr '\\' '/')"
    "$browser" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
      --window-size="$w,$h" --screenshot="$png" "$url" >/dev/null 2>&1
  fi
  if [[ ! -s "$(cygpath -u "$png" 2>/dev/null || echo "$png")" ]]; then
    echo "AVISO: sin Edge/Chrome; el preview es del PDF y NO garantiza que el SVG tenga todo el texto" >&2
    pdftocairo -png -r 200 -singlefile "$(winpath "$pdf")" "${png%.png}"
  fi
  echo "$png"
fi
