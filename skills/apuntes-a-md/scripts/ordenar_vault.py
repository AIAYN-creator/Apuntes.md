# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Ordena las notas de apuntes del vault en Universidad/<carrera>/<curso>/<Asignatura>/.

Uso:
    uv run scripts/ordenar_vault.py <vault> [--desde CARPETA ...] [--excluir CARPETA ...]
                                    [--carrera Química] [--curso 2026-2027] [--aplicar]

Sin --aplicar solo muestra el plan (simulación). Con --aplicar mueve.

Qué se mueve:
- Notas de apuntes: .md con frontmatter que tiene `asignatura`, `tema` y `fuente`.
- MOCs de asignatura: .md con `tipo: moc` y `asignatura` (los crea la skill de enlazado).
Todo lo demás (notas personales, plantillas...) no se toca.

Destino de cada nota:
    <vault>/Universidad/<carrera>/<curso>/<Asignatura>/<mismo-nombre>.md
    <vault>/Universidad/<carrera>/<curso>/<Asignatura>/assets/<slug>/   (sus assets)
- El nombre del fichero no cambia: los [[enlaces]] hacia la nota no se rompen.
- La carpeta de assets se mueve con la nota: los enlaces relativos siguen valiendo.
- <curso>: el campo `curso:` de la nota si lo tiene; si no, --curso (por defecto
  2026-2027). Si las `fechas` de la nota caen en otro curso (empieza en septiembre),
  NO se mueve: se pide confirmarlo con un `curso:` en el frontmatter.
- --desde añade carpetas de origen fuera del vault (p. ej. pruebas/salida).
- --excluir deja fuera carpetas del vault (p. ej. notas viejas de prueba).

Nunca edita el contenido de una nota y nunca sobrescribe: si el destino existe,
lo marca como conflicto y no mueve esa nota.

Exit: 0 todo bien, 1 hay conflictos o avisos que revisar, 2 uso incorrecto.
"""

import argparse
import datetime as dt
import re
import shutil
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REQUIRED = ("asignatura", "tema", "fuente")
SKIP_DIRS = {".obsidian", ".trash", ".git", "assets"}
ASSET_LINK = re.compile(r"\]\((assets/[^)\s]+)\)")
EMBED = re.compile(r"!\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
ILLEGAL = re.compile(r'[<>:"/\\|?*]')
CURSO_RE = re.compile(r"^(\d{4})-(\d{4})$")


@dataclass
class Note:
    path: Path
    asignatura: str
    curso: str | None          # campo `curso:` del frontmatter
    fechas: list[dt.date]
    moc: bool
    asset_links: list[str] = field(default_factory=list)
    embeds: list[str] = field(default_factory=list)


@dataclass
class Plan:
    vault: Path
    moves: list[tuple[Path, Path]] = field(default_factory=list)       # (origen, destino) de notas
    asset_moves: list[tuple[Path, Path]] = field(default_factory=list)
    folders_to_create: set[Path] = field(default_factory=set)
    in_place: list[Path] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def rel(self, p: Path) -> str:
        """Ruta relativa al vault si está dentro; si no, la ruta tal cual."""
        try:
            return p.relative_to(self.vault).as_posix()
        except ValueError:
            return str(p)


def read_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return None
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return None
    try:
        data = yaml.safe_load(parts[0].lstrip("-").strip("\n"))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def as_dates(value) -> list[dt.date]:
    """`fechas: [..]` (v2) o `fecha: ..` (v1); ignora null y lo que no sea fecha."""
    items = value if isinstance(value, list) else [value]
    out = []
    for v in items:
        if isinstance(v, dt.datetime):
            out.append(v.date())
        elif isinstance(v, dt.date):
            out.append(v)
        elif isinstance(v, str):
            try:
                out.append(dt.date.fromisoformat(v.strip()))
            except ValueError:
                pass
    return out


def course_of(d: dt.date) -> str:
    """El curso empieza en septiembre: 2026-10-05 -> 2026-2027, 2027-03-01 -> 2026-2027."""
    start = d.year if d.month >= 9 else d.year - 1
    return f"{start}-{start + 1}"


def excluded(path: Path, root: Path, excludes: list[Path]) -> bool:
    if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
        return True
    return any(path.is_relative_to(e) for e in excludes)


def find_notes(root: Path, excludes: list[Path]) -> list[Note]:
    notes = []
    for path in root.rglob("*.md"):
        if excluded(path, root, excludes):
            continue
        fm = read_frontmatter(path)
        if not fm or not fm.get("asignatura"):
            continue
        moc = str(fm.get("tipo", "")).strip().lower() == "moc"
        if not moc and not all(fm.get(k) for k in REQUIRED):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        curso = str(fm["curso"]).strip() if fm.get("curso") else None
        fechas = as_dates(fm.get("fechas", fm.get("fecha")))
        notes.append(Note(path, str(fm["asignatura"]).strip(), curso, fechas, moc,
                          ASSET_LINK.findall(text), [e.strip() for e in EMBED.findall(text)]))
    return notes


def fold(name: str) -> str:
    """Clave para comparar nombres: sin tildes, sin mayúsculas, sin espacios extra."""
    nfkd = unicodedata.normalize("NFKD", name)
    return " ".join("".join(c for c in nfkd if not unicodedata.combining(c)).lower().split())


def safe(name: str) -> str:
    return ILLEGAL.sub("-", name).strip(". ")


def pick_curso(note: Note, default: str, plan: Plan) -> str | None:
    """Curso de la nota, o None si hay que preguntar (conflicto ya anotado)."""
    if note.curso:
        if not CURSO_RE.match(note.curso) or int(note.curso[5:]) != int(note.curso[:4]) + 1:
            plan.conflicts.append(f"{plan.rel(note.path)}: `curso: {note.curso}` no tiene la forma AAAA-AAAA+1")
            return None
        return note.curso
    by_date = sorted({course_of(d) for d in note.fechas})
    if by_date and by_date != [default]:
        plan.conflicts.append(
            f"{plan.rel(note.path)}: sus fechas son del curso {' y '.join(by_date)}, no del {default}. "
            f"Confirma el curso añadiendo `curso: …` al frontmatter y repite (no se mueve)")
        return None
    return default


def folder_names(base: Path, notes: list[Note], plan: Plan) -> dict[str, str]:
    """Nombre de carpeta de cada asignatura, reutilizando la que ya exista en el curso."""
    existing = {fold(d.name): d.name for d in base.iterdir() if d.is_dir()} if base.is_dir() else {}
    spellings: dict[str, Counter] = defaultdict(Counter)
    for n in notes:
        spellings[fold(n.asignatura)][n.asignatura] += 1

    chosen = {}
    for key, counter in spellings.items():
        name = safe(existing.get(key) or counter.most_common(1)[0][0])
        variants = set(counter) - {name}
        if variants:
            plan.warnings.append(f"asignatura escrita de varias formas {sorted(variants | {name})} → carpeta '{name}'. "
                                 f"Unifica el frontmatter si quieres (este script no lo edita).")
        chosen[key] = name
    return chosen


def assets_stem(note: Note) -> str:
    """Carpeta de assets de la nota: el slug (v2: "Bioquímica - Tema 1" -> bioquimica-tema-1)
    o, en notas de la v1, el nombre tal cual."""
    slug = re.sub(r"[^a-z0-9]+", "-", fold(note.path.stem)).strip("-")
    if any(l.startswith(f"assets/{slug}/") for l in note.asset_links) or (note.path.parent / "assets" / slug).is_dir():
        return slug
    return note.path.stem


def build_plan(vault: Path, sources: list[Path], excludes: list[Path], carrera: str, default_curso: str) -> Plan:
    plan = Plan(vault)
    notes = [n for root in [vault, *sources] for n in find_notes(root, excludes)]
    claimed: dict[Path, Path] = {}

    # Agrupa por curso para reutilizar las carpetas de asignatura de cada uno
    by_curso: dict[str, list[Note]] = defaultdict(list)
    for note in notes:
        curso = pick_curso(note, default_curso, plan)
        if curso:
            by_curso[curso].append(note)

    for curso, group in by_curso.items():
        base = vault / "Universidad" / safe(carrera) / curso
        folders = folder_names(base, group, plan)
        for note in group:
            folder = base / folders[fold(note.asignatura)]
            target = folder / note.path.name
            stem = assets_stem(note)
            src_assets = note.path.parent / "assets" / stem
            dst_assets = folder / "assets" / stem

            foreign = sorted({l for l in note.asset_links if not l.startswith(f"assets/{stem}/")})
            missing = sorted({l for l in note.asset_links if not (note.path.parent / l).exists()})
            if missing:
                plan.warnings.append(f"{plan.rel(note.path)}: enlaces a assets que no existen: {missing}")
            # ![[x.svg]] lo resuelve Obsidian por nombre: tiene que estar en la carpeta de assets de la nota
            lost = sorted({e for e in note.embeds if Path(e).suffix and not (src_assets / Path(e).name).exists()
                           and not (note.path.parent / e).exists()})
            if lost:
                plan.warnings.append(f"{plan.rel(note.path)}: ![[…]] que no están en assets/{stem}/: {lost}")

            if target.resolve() == note.path.resolve():
                plan.in_place.append(note.path)
                continue
            if foreign:
                plan.conflicts.append(f"{plan.rel(note.path)}: enlaza assets fuera de assets/{stem}/ {foreign}; "
                                      f"no se mueve para no romper enlaces")
                continue
            if target.exists() or target in claimed:
                other = claimed.get(target, target)
                plan.conflicts.append(f"{plan.rel(note.path)} → {plan.rel(target)}: ya existe ({plan.rel(other)}); no se sobrescribe")
                continue
            if src_assets.exists() and dst_assets.exists():
                plan.conflicts.append(f"{plan.rel(src_assets)} → {plan.rel(dst_assets)}: la carpeta de assets ya existe; no se mueve la nota")
                continue

            claimed[target] = note.path
            if not folder.exists():
                plan.folders_to_create.add(folder)
            plan.moves.append((note.path, target))
            if src_assets.exists() and not note.moc:
                plan.asset_moves.append((src_assets, dst_assets))

    check_embed_names(vault, notes, plan)
    report_orphans(vault, sources, excludes, plan)
    return plan


def check_embed_names(vault: Path, notes: list[Note], plan: Plan) -> None:
    """Un ![[fig-04.svg]] es ambiguo si hay varios ficheros con ese nombre en el vault:
    Obsidian podría enseñar el de otro tema."""
    counts = Counter(p.name for p in vault.rglob("*") if p.is_file() and ".obsidian" not in p.parts)
    for note in notes:
        dup = sorted({Path(e).name for e in note.embeds if counts[Path(e).name] > 1})
        if dup:
            plan.warnings.append(f"{plan.rel(note.path)}: ![[…]] con nombre repetido en el vault {dup}; "
                                 f"Obsidian puede enseñar el de otro tema. Usa la ruta: ![[assets/<tema>/…]]")


def report_orphans(vault: Path, sources: list[Path], excludes: list[Path], plan: Plan) -> None:
    moved = {src for src, _ in plan.asset_moves}
    for root in [vault, *sources]:
        for assets_dir in root.rglob("assets"):
            if (not assets_dir.is_dir() or ".obsidian" in assets_dir.parts
                    or any(assets_dir.is_relative_to(e) for e in excludes)):
                continue
            notes_here = {re.sub(r"[^a-z0-9]+", "-", fold(p.stem)).strip("-") for p in assets_dir.parent.glob("*.md")}
            notes_here |= {p.stem for p in assets_dir.parent.glob("*.md")}
            for sub in assets_dir.iterdir():
                if sub.is_dir() and sub not in moved and sub.name not in notes_here:
                    plan.warnings.append(f"assets huérfanos (sin su nota al lado): {plan.rel(sub)}")


def show(plan: Plan, apply: bool) -> None:
    rel = plan.rel
    print("== APLICADO ==" if apply else "== SIMULACIÓN (nada se ha movido; usa --aplicar) ==")
    for f in sorted(plan.folders_to_create):
        print(f"  + carpeta  {rel(f)}/")
    for src, dst in plan.moves:
        print(f"  → nota     {rel(src)}  ⟶  {rel(dst)}")
    for src, dst in plan.asset_moves:
        print(f"  → assets   {rel(src)}/  ⟶  {rel(dst)}/")
    print(f"  = ya en su sitio: {len(plan.in_place)} nota(s)")
    for c in plan.conflicts:
        print(f"  ✗ CONFLICTO {c}")
    for w in plan.warnings:
        print(f"  ! AVISO    {w}")
    if not (plan.moves or plan.conflicts or plan.warnings):
        print("  Todo en orden.")


def prune_empty(folder: Path, stop: Path) -> None:
    """Borra carpetas que hayan quedado vacías al vaciar el origen, sin pasar de `stop`."""
    while folder != stop and folder.is_dir() and not any(folder.iterdir()):
        folder.rmdir()
        folder = folder.parent


def apply_plan(plan: Plan, roots: list[Path]) -> None:
    for folder in plan.folders_to_create:
        folder.mkdir(parents=True, exist_ok=True)
    for src, dst in plan.asset_moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
    for src, dst in plan.moves:
        shutil.move(src, dst)
    for src, _ in [*plan.asset_moves, *plan.moves]:
        root = next((r for r in roots if src.is_relative_to(r)), None)
        if root:
            prune_empty(src.parent, root)


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vault", type=Path)
    parser.add_argument("--desde", type=Path, nargs="+", default=[], metavar="CARPETA",
                        help="carpetas de origen fuera del vault cuyas notas se traen al vault")
    parser.add_argument("--excluir", type=Path, nargs="+", default=[], metavar="CARPETA",
                        help="carpetas que no se tocan (p. ej. notas viejas de prueba)")
    parser.add_argument("--carrera", default="Química", help="carpeta de la carrera (por defecto: Química)")
    parser.add_argument("--curso", default="2026-2027",
                        help="curso de las notas sin campo `curso:` (por defecto: 2026-2027)")
    parser.add_argument("--aplicar", action="store_true", help="ejecuta los movimientos (sin esto, solo simula)")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.is_dir():
        parser.error(f"no existe el vault {vault}")
    if not CURSO_RE.match(args.curso) or int(args.curso[5:]) != int(args.curso[:4]) + 1:
        parser.error(f"--curso {args.curso}: tiene que ser AAAA-AAAA+1 (p. ej. 2026-2027)")
    sources = [s.resolve() for s in args.desde]
    for s in sources:
        if not s.is_dir():
            parser.error(f"no existe la carpeta de origen {s}")
    excludes = [(e if e.is_absolute() else vault / e).resolve() for e in args.excluir]

    plan = build_plan(vault, sources, excludes, args.carrera, args.curso)
    if args.aplicar:
        apply_plan(plan, [vault, *sources])
    show(plan, args.aplicar)
    return 1 if plan.conflicts or plan.warnings else 0


if __name__ == "__main__":
    sys.exit(main())
