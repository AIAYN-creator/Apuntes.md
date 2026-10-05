# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Enlaza los temas de UNA asignatura: enlaces internos, tags y MOC, sin cambiar ni una palabra.

Uso:
    uv run scripts/enlazar.py inventario <carpeta-asignatura> [--buscar TÉRMINO ...]
    uv run scripts/enlazar.py aplicar <carpeta-asignatura> --plan plan.json [--escribir]

inventario: lista los temas y sus encabezados (los destinos posibles). Con --buscar,
    cuenta en qué tema y sección aparece cada término, solo donde se podría enlazar.

aplicar: sin --escribir solo simula y enseña el resumen. Con --escribir:
    - envuelve la PRIMERA mención de cada concepto en cada sección:
      `plegamiento` -> `[[Bioquímica - Tema 3#Plegamiento (folding)|plegamiento]]`
    - nunca enlaza en títulos, avisos/todo, índice, sesión, fórmulas, código,
      comentarios, imágenes, pies de figura, resaltados ==…== ni dentro de otro enlace,
      ni en la propia sección donde se define el concepto;
    - añade los tags `apuntes`, `<asignatura>` y `<asignatura>/tema-N` al frontmatter;
    - genera (o regenera) el MOC `<Asignatura>.md` con la tabla de temas y la de
      conceptos transversales.
    Antes de escribir comprueba que, quitando los enlaces, cada nota es idéntica a la
    original. Si no, no escribe nada.

plan.json:
    {"conceptos": [
      {"concepto": "efecto hidrofóbico",
       "formas": ["efecto hidrofóbico", "efectos hidrofóbicos"],   # cómo aparece en el texto
       "destino": "Bioquímica - Tema 1#Interacciones por efecto hidrofóbico",
       "mayusculas": false}                                         # true: distingue (pI, Cys)
    ]}

Exit: 0 bien, 1 avisos o diferencias, 2 plan o uso incorrecto.
"""

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

NO_ENLAZAR = {"warning", "todo", "abstract", "indice", "sesion", "formula", "danger", "caution", "bug", "failure"}
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
CALLOUT = re.compile(r"^\[!([^\]]+)\]")
# Lo que nunca se toca dentro de una línea
MASK = re.compile(r"\$\$.*?\$\$|\$[^$\n]+\$|`[^`\n]*`|!?\[\[[^\]]*\]\]|!?\[[^\]]*\]\([^)]*\)|==.*?==|%%.*?%%|<[^>\n]+>")
LINK = re.compile(r"(?<!!)\[\[([^\]|\\]*?)(\\?\|)([^\]]*)\]\]")
MARCA_MOC = "%% generado por enlazar.py: no lo edites a mano, se regenera %%"
ROMANOS = "I II III IV V VI VII VIII IX X XI XII".split()


def fold(s: str) -> str:
    nfkd = unicodedata.normalize("NFKD", s)
    return " ".join("".join(c for c in nfkd if not unicodedata.combining(c)).lower().split())


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", fold(s)).strip("-")


# ---------------------------------------------------------------- notas

@dataclass
class Nota:
    path: Path
    fm_text: str
    fm: dict
    lines: list[str]
    crlf: bool
    headings: list[tuple[int, int, str]] = field(default_factory=list)   # (línea, nivel, texto)
    seccion: list[int] = field(default_factory=list)                     # sección de cada línea (-1: antes del primer título)
    elegible: list[bool] = field(default_factory=list)

    @property
    def nombre(self) -> str:
        return self.path.stem

    @property
    def tema(self):
        return self.fm.get("tema")

    def texto(self) -> str:
        t = self.fm_text + "\n".join(self.lines)
        return t.replace("\n", "\r\n") if self.crlf else t


def leer(path: Path) -> Nota:
    raw = path.read_bytes().decode("utf-8")
    crlf = "\r\n" in raw
    text = raw.replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?\n)---\n", text, re.S)
    fm_text, fm = (m.group(0), yaml.safe_load(m.group(1)) or {}) if m else ("", {})
    nota = Nota(path, fm_text, fm if isinstance(fm, dict) else {}, text[len(fm_text):].split("\n"), crlf)
    analizar(nota)
    return nota


def analizar(n: Nota) -> None:
    """Secciones y líneas donde se puede enlazar."""
    n.headings, n.seccion, n.elegible = [], [], []
    sec, in_code, in_math, in_comment, saltar_callout, prev_img = -1, False, False, False, False, False
    for i, l in enumerate(n.lines):
        s = l.strip()
        citada = s.startswith(">")
        inner = re.sub(r"^(>\s?)+", "", s).strip() if citada else s
        if not citada:
            saltar_callout = False
        ok = True
        if in_code:
            ok = False
            in_code = not inner.startswith("```")
        elif inner.startswith("```"):
            ok, in_code = False, True
        elif in_math:
            ok = False
            in_math = not inner.endswith("$$")
        elif inner.startswith("$$"):
            ok = False
            in_math = not (len(inner) >= 4 and inner.endswith("$$"))
        elif in_comment:
            ok = False
            in_comment = "%%" not in inner
        elif inner.startswith("%%") and inner.count("%%") == 1:
            ok, in_comment = False, True
        elif not citada and (m := HEADING.match(s)):
            sec = len(n.headings)
            n.headings.append((i, len(m.group(1)), m.group(2)))
            ok = False
        elif citada and (m := CALLOUT.match(inner)):
            saltar_callout = slug(m.group(1)) in NO_ENLAZAR
            ok = False                                    # la cabecera del callout nunca
        elif citada:
            ok = not saltar_callout
        elif prev_img and re.fullmatch(r"([*_]).+\1", s):  # pie de figura en cursiva bajo una imagen
            ok = False
        prev_img = inner.startswith("![")
        n.seccion.append(sec)
        n.elegible.append(ok)


def rango_seccion(n: Nota, titulo: str) -> range | None:
    """Líneas de la sección `titulo`, con sus subsecciones."""
    for k, (i, nivel, texto) in enumerate(n.headings):
        if texto == titulo:
            fin = next((j for j, nv, _ in n.headings[k + 1:] if nv <= nivel), len(n.lines))
            return range(i, fin)
    return None


def cargar_asignatura(carpeta: Path) -> tuple[str, list[Nota], Path]:
    notas = []
    for p in sorted(carpeta.glob("*.md")):
        n = leer(p)
        if n.fm.get("asignatura") and n.fm.get("tema") is not None and str(n.fm.get("tipo", "")).lower() != "moc":
            notas.append(n)
    if not notas:
        sys.exit(f"ERROR: no hay notas de apuntes (con asignatura y tema) en {carpeta}")
    asignaturas = {fold(str(n.fm["asignatura"])) for n in notas}
    if len(asignaturas) > 1:
        sys.exit(f"ERROR: la carpeta mezcla asignaturas {sorted(asignaturas)}; los enlaces son solo dentro de una")
    notas.sort(key=lambda n: (float(n.tema) if str(n.tema).replace(".", "", 1).isdigit() else 1e9, n.nombre))
    asig = str(notas[0].fm["asignatura"]).strip()
    return asig, notas, carpeta / f"{asig}.md"


# ---------------------------------------------------------------- inventario

def huecos(linea: str) -> list[tuple[int, int]]:
    return [m.span() for m in MASK.finditer(linea)]


def libre(span: tuple[int, int], masks: list[tuple[int, int]]) -> bool:
    a, b = span
    return all(b <= x or a >= y for x, y in masks)


def patron(formas: list[str], mayusculas: bool) -> re.Pattern:
    alt = "|".join(re.escape(f) for f in sorted(formas, key=len, reverse=True))
    return re.compile(rf"(?<![\w])(?:{alt})(?![\w])", 0 if mayusculas else re.IGNORECASE)


def inventario(carpeta: Path, terminos: list[str]) -> int:
    asig, notas, moc = cargar_asignatura(carpeta)
    print(f"# {asig}: {len(notas)} temas" + (f" · MOC {moc.name} existe" if moc.exists() else ""))
    for n in notas:
        print(f"\n## {n.nombre}  (tema {n.tema})")
        for i, nivel, texto in n.headings:
            print(f"  {'  ' * (nivel - 1)}{'#' * nivel} {texto}   l.{i + 1}")
    for t in terminos:
        rx = patron([t], mayusculas=False)
        print(f"\n== «{t}» (solo donde se podría enlazar)")
        total = 0
        for n in notas:
            por_sec: dict[str, int] = {}
            for i, l in enumerate(n.lines):
                if not n.elegible[i]:
                    continue
                c = sum(1 for m in rx.finditer(l) if libre(m.span(), huecos(l)))
                if c:
                    s = n.headings[n.seccion[i]][2] if n.seccion[i] >= 0 else "(inicio)"
                    por_sec[s] = por_sec.get(s, 0) + c
            for s, c in por_sec.items():
                print(f"  T{n.tema} · {s}: {c}")
                total += c
        if not total:
            print("  (ninguna)")
    return 0


# ---------------------------------------------------------------- aplicar

@dataclass
class Concepto:
    nombre: str
    formas: list[str]
    destino: str
    nota: str
    titulo: str
    rx: re.Pattern


def leer_plan(path: Path, notas: list[Nota]) -> list[Concepto]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.exit(f"ERROR: plan ilegible: {e}")
    por_nombre = {n.nombre: n for n in notas}
    errores, conceptos = [], []
    for c in data.get("conceptos", []):
        nombre, destino = c.get("concepto", "?"), c.get("destino", "")
        formas = c.get("formas") or [nombre]
        nota, _, titulo = destino.partition("#")
        if nota not in por_nombre:
            errores.append(f"«{nombre}»: la nota «{nota}» no está en esta asignatura (los enlaces son solo dentro de ella)")
            continue
        if not titulo or rango_seccion(por_nombre[nota], titulo) is None:
            errores.append(f"«{nombre}»: «{nota}» no tiene el encabezado «{titulo}»")
            continue
        if re.search(r"[#|^:\[\]]|%%", titulo):
            errores.append(f"«{nombre}»: el encabezado «{titulo}» tiene caracteres que Obsidian no admite en un enlace")
            continue
        conceptos.append(Concepto(nombre, formas, destino, nota, titulo, patron(formas, bool(c.get("mayusculas")))))
    if errores:
        print("ERRORES EN EL PLAN (no se ha hecho nada):")
        for e in errores:
            print(f"  ✗ {e}")
        sys.exit(2)
    # Las formas más largas primero: "efecto hidrofóbico" antes que "hidrofóbico"
    conceptos.sort(key=lambda c: -max(map(len, c.formas)))
    return conceptos


def enlazar_nota(n: Nota, conceptos: list[Concepto], por_nombre: dict[str, Nota]) -> list[tuple[Concepto, int, str]]:
    hechos = []
    for c in conceptos:
        prohibidas = rango_seccion(por_nombre[c.nota], c.titulo) if c.nota == n.nombre else range(0)
        ya = {n.seccion[i] for i, l in enumerate(n.lines) if f"[[{c.destino}|" in l or f"[[{c.destino}\\|" in l}
        for i, l in enumerate(n.lines):
            sec = n.seccion[i]
            if not n.elegible[i] or i in prohibidas or sec in ya:
                continue
            masks = huecos(l)
            m = next((m for m in c.rx.finditer(l) if libre(m.span(), masks)), None)
            if not m:
                continue
            sep = "\\|" if l.lstrip().startswith("|") else "|"         # dentro de una tabla, el | va escapado
            n.lines[i] = f"{l[:m.start()]}[[{c.destino}{sep}{m.group(0)}]]{l[m.end():]}"
            ya.add(sec)
            hechos.append((c, i, m.group(0)))
    return hechos


def tags_de(n: Nota, asig: str) -> list[str]:
    return ["apuntes", slug(asig), f"{slug(asig)}/tema-{n.tema}"]


def poner_tags(n: Nota, tags: list[str]) -> list[str]:
    """Añade los tags que falten al frontmatter, sin tocar el resto. Devuelve los añadidos."""
    actuales = n.fm.get("tags") or []
    actuales = [actuales] if isinstance(actuales, str) else list(actuales)
    nuevos = [t for t in tags if t not in actuales]
    if not nuevos:
        return []
    todos = actuales + nuevos
    lineas = n.fm_text.split("\n")
    k = next((i for i, l in enumerate(lineas) if re.match(r"tags\s*:", l)), None)
    linea = f"tags: [{', '.join(todos)}]"
    if k is None:
        lineas.insert(len(lineas) - 2, linea)                        # antes del --- de cierre
    else:
        fin = k + 1
        while fin < len(lineas) and re.match(r"\s+-\s", lineas[fin]):
            fin += 1
        lineas[k:fin] = [linea]
    n.fm_text = "\n".join(lineas)
    n.fm["tags"] = todos
    return nuevos


def sin_enlaces(texto: str) -> str:
    return LINK.sub(lambda m: m.group(3), texto)


def cuerpo_sin_tags(n_texto: str) -> str:
    t = n_texto.replace("\r\n", "\n")
    m = re.match(r"\A---\n(.*?\n)---\n", t, re.S)
    if not m:
        return t
    fm = re.sub(r"^tags\s*:.*\n(?:\s+-\s.*\n)*", "", m.group(1), flags=re.M)
    return f"---\n{fm}---\n" + t[m.end():]


def fechas_txt(n: Nota) -> str:
    out = []
    for f in n.fm.get("fechas") or []:
        if isinstance(f, str):
            try:
                f = dt.date.fromisoformat(f)
            except ValueError:
                continue
        if isinstance(f, dt.date):
            out.append(f"{f.day}/{ROMANOS[f.month - 1]}/{f.year}")
    return " · ".join(out) or "—"


def paginas_txt(n: Nota) -> str:
    fuentes = n.fm.get("fuente") or []
    fuentes = [fuentes] if isinstance(fuentes, str) else fuentes
    out = []
    for f in fuentes:
        m = re.search(r"#p(\d+)(?:-(\d+))?", str(f))
        if m:
            out.append(m.group(1) + (f"–{m.group(2)}" if m.group(2) else ""))
    return ", ".join(out) or "—"


def generar_moc(asig: str, notas: list[Nota], conceptos: list[Concepto]) -> str:
    por_nombre = {n.nombre: n for n in notas}
    l = ["---", "tipo: moc", f"asignatura: {asig}", f"tags: [apuntes, {slug(asig)}]", "---",
         f"# {asig}", "", MARCA_MOC, "",
         "| Tema | Título | Fechas | Páginas |", "|---|---|---|---|"]
    for n in notas:
        l.append(f"| [[{n.nombre}\\|{n.tema}]] | {n.fm.get('titulo') or n.nombre} | {fechas_txt(n)} | {paginas_txt(n)} |")
    filas = []
    for c in sorted(conceptos, key=lambda c: fold(c.nombre)):
        # Por el texto enlazado, no solo por el destino: dos conceptos pueden compartir destino (pI y punto isoelectrónico)
        aparece = [n for n in notas if n.nombre != c.nota and any(
            m.group(1) == c.destino and c.rx.fullmatch(m.group(3)) for m in LINK.finditer("\n".join(n.lines)))]
        if aparece:
            filas.append(f"| {c.nombre} | [[{c.destino}\\|T{por_nombre[c.nota].tema}]] | "
                         f"{' · '.join(f'T{n.tema}' for n in aparece)} |")
    if filas:
        l += ["", "## Conceptos transversales", "", "| Concepto | Se define en | Aparece en |", "|---|---|---|", *filas]
    return "\n".join(l) + "\n"


def aplicar(carpeta: Path, plan: Path, escribir: bool) -> int:
    asig, notas, moc = cargar_asignatura(carpeta)
    conceptos = leer_plan(plan, notas)
    por_nombre = {n.nombre: n for n in notas}
    originales = {n.nombre: n.texto() for n in notas}

    if moc.exists() and MARCA_MOC not in moc.read_text(encoding="utf-8"):
        print(f"✗ {moc.name} existe y no lo generó este script: no se toca nada. Renómbralo o bórralo tú.")
        return 2

    print("== ESCRITO ==" if escribir else "== SIMULACIÓN (no se ha escrito nada; usa --escribir) ==")
    usados, avisos, total = set(), [], 0
    for n in notas:
        hechos = enlazar_nota(n, conceptos, por_nombre)
        nuevos_tags = poner_tags(n, tags_de(n, asig))
        total += len(hechos)
        print(f"\n{n.path.name}: {len(hechos)} enlace(s)" + (f" · tags + {nuevos_tags}" if nuevos_tags else ""))
        for c, i, texto in hechos:
            usados.add(c.nombre)
            sec = n.headings[n.seccion[i]][2] if n.seccion[i] >= 0 else "(inicio)"
            print(f"  l.{i + 1:<4} «{texto}» → {c.destino}   [sección: {sec}]")
        # Invariante: quitando los enlaces y los tags, la nota es idéntica a la original
        if sin_enlaces(cuerpo_sin_tags(n.texto())) != sin_enlaces(cuerpo_sin_tags(originales[n.nombre])):
            avisos.append(f"{n.path.name}: el texto ha cambiado al enlazar (fallo del script); no se escribe nada")

    sin_uso = [c.nombre for c in conceptos if c.nombre not in usados]
    if sin_uso:
        print(f"\nConceptos sin ninguna mención enlazable: {sin_uso}")
    moc_txt = generar_moc(asig, notas, conceptos)
    print(f"\nMOC {moc.name}: {'se regenera' if moc.exists() else 'nuevo'}\n" + "\n".join(f"  | {x}" for x in moc_txt.splitlines()))

    if avisos:
        for a in avisos:
            print(f"✗ {a}")
        return 1
    print(f"\nInvariante OK: {len(notas)} notas idénticas a las originales quitando enlaces y tags · {total} enlaces")
    if escribir:
        for n in notas:
            if n.texto() != originales[n.nombre]:
                n.path.write_bytes(n.texto().encode("utf-8"))
        moc.write_bytes(moc_txt.encode("utf-8"))
    return 0


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)
    pi = sub.add_parser("inventario", help="temas, encabezados y dónde aparece cada término")
    pi.add_argument("carpeta", type=Path)
    pi.add_argument("--buscar", nargs="+", default=[], metavar="TÉRMINO")
    pa = sub.add_parser("aplicar", help="enlaces + tags + MOC (simula sin --escribir)")
    pa.add_argument("carpeta", type=Path)
    pa.add_argument("--plan", type=Path, required=True)
    pa.add_argument("--escribir", action="store_true")
    a = p.parse_args()
    if not a.carpeta.is_dir():
        p.error(f"no existe la carpeta {a.carpeta}")
    if a.orden == "inventario":
        return inventario(a.carpeta, a.buscar)
    return aplicar(a.carpeta, a.plan, a.escribir)


if __name__ == "__main__":
    sys.exit(main())
