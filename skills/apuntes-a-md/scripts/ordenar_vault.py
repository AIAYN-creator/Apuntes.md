# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml"]
# ///
"""Ordena las notas de apuntes del vault en <Asignatura>/ según su frontmatter.

Uso:
    uv run scripts/ordenar_vault.py <vault> [--desde CARPETA ...] [--aplicar]

Sin --aplicar solo muestra el plan (simulación). Con --aplicar mueve.

Qué se considera "nota de apuntes": un .md con frontmatter que tiene `asignatura`,
`tema` y `fuente`. Todo lo demás (MOCs, notas personales, plantillas) no se toca.

Para cada nota:
- destino: <vault>/<Asignatura>/<mismo-nombre>.md  (el nombre del fichero no cambia:
  así no se rompen los [[enlaces]] que haya hacia ella).
- su carpeta de assets (assets/<nombre>/) se mueve con ella, de modo que los
  enlaces relativos `assets/<nombre>/...` siguen funcionando sin editar la nota.
- --desde añade carpetas de origen fuera del vault (p. ej. pruebas/salida): sus
  notas se mueven al vault.

Nunca edita el contenido de una nota y nunca sobrescribe: si el destino existe,
lo marca como conflicto y no mueve esa nota.

Exit: 0 todo bien, 1 hay conflictos o avisos que revisar, 2 uso incorrecto.
"""

import argparse
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
ILLEGAL = re.compile(r'[<>:"/\\|?*]')


@dataclass
class Note:
    path: Path
    asignatura: str
    asset_links: list[str] = field(default_factory=list)


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
            return str(p.relative_to(self.vault))
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


def find_notes(root: Path) -> list[Note]:
    notes = []
    for path in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts[:-1]):
            continue
        fm = read_frontmatter(path)
        if not fm or not all(fm.get(k) for k in REQUIRED):
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        notes.append(Note(path, str(fm["asignatura"]).strip(), ASSET_LINK.findall(text)))
    return notes


def fold(name: str) -> str:
    """Clave para comparar asignaturas: sin tildes, sin mayúsculas, sin espacios extra."""
    nfkd = unicodedata.normalize("NFKD", name)
    return " ".join("".join(c for c in nfkd if not unicodedata.combining(c)).lower().split())


def folder_names(vault: Path, notes: list[Note], plan: Plan) -> dict[str, str]:
    """Decide el nombre de carpeta de cada asignatura, reutilizando carpetas existentes."""
    existing = {fold(d.name): d.name for d in vault.iterdir() if d.is_dir() and d.name not in SKIP_DIRS}
    spellings: dict[str, Counter] = defaultdict(Counter)
    for n in notes:
        spellings[fold(n.asignatura)][n.asignatura] += 1

    chosen = {}
    for key, counter in spellings.items():
        if key in existing:
            name = existing[key]
        else:
            name = counter.most_common(1)[0][0]
        name = ILLEGAL.sub("-", name).strip(". ")
        variants = set(counter) - {name}
        if variants:
            plan.warnings.append(f"asignatura escrita de varias formas {sorted(variants | {name})} → carpeta '{name}'. "
                                 f"Unifica el frontmatter si quieres (este script no lo edita).")
        chosen[key] = name
    return chosen


def build_plan(vault: Path, sources: list[Path]) -> Plan:
    plan = Plan(vault)
    notes = [n for root in [vault, *sources] for n in find_notes(root)]
    folders = folder_names(vault, notes, plan)
    claimed: dict[Path, Path] = {}

    for note in notes:
        folder = vault / folders[fold(note.asignatura)]
        target = folder / note.path.name
        stem = note.path.stem
        src_assets = note.path.parent / "assets" / stem
        dst_assets = folder / "assets" / stem

        # Enlaces a assets: deben vivir en assets/<nombre-de-la-nota>/ para poder moverlos juntos
        foreign = sorted({l for l in note.asset_links if not l.startswith(f"assets/{stem}/")})
        missing = sorted({l for l in note.asset_links if not (note.path.parent / l).exists()})
        if missing:
            plan.warnings.append(f"{plan.rel(note.path)}: enlaces a assets que no existen: {missing}")

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
        if src_assets.exists():
            plan.asset_moves.append((src_assets, dst_assets))

    # Carpetas de assets sin nota (solo informa)
    moved_assets = {src for src, _ in plan.asset_moves}
    for root in [vault, *sources]:
        for assets_dir in root.rglob("assets"):
            if not assets_dir.is_dir() or ".obsidian" in assets_dir.parts:
                continue
            for sub in assets_dir.iterdir():
                if sub.is_dir() and sub not in moved_assets and not (assets_dir.parent / f"{sub.name}.md").exists():
                    plan.warnings.append(f"assets huérfanos (sin nota {sub.name}.md al lado): {plan.rel(sub)}")
    return plan


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


def apply_plan(plan: Plan) -> None:
    for folder in plan.folders_to_create:
        folder.mkdir(parents=True, exist_ok=True)
    for src, dst in plan.asset_moves:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(src, dst)
    for src, dst in plan.moves:
        shutil.move(src, dst)
    # Limpia carpetas assets/ que hayan quedado vacías en el origen
    for src, _ in plan.asset_moves:
        parent = src.parent
        if parent.name == "assets" and parent.exists() and not any(parent.iterdir()):
            parent.rmdir()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vault", type=Path)
    parser.add_argument("--desde", type=Path, nargs="+", default=[], metavar="CARPETA",
                        help="carpetas de origen fuera del vault cuyas notas se traen al vault")
    parser.add_argument("--aplicar", action="store_true", help="ejecuta los movimientos (sin esto, solo simula)")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not vault.is_dir():
        parser.error(f"no existe el vault {vault}")
    sources = [s.resolve() for s in args.desde]
    for s in sources:
        if not s.is_dir():
            parser.error(f"no existe la carpeta de origen {s}")

    plan = build_plan(vault, sources)
    if args.aplicar:
        apply_plan(plan)
    show(plan, args.aplicar)
    return 1 if plan.conflicts or plan.warnings else 0


if __name__ == "__main__":
    sys.exit(main())
