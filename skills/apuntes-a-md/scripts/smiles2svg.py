# /// script
# requires-python = ">=3.12"
# dependencies = ["rdkit"]
# ///
"""SMILES -> SVG con RDKit, validando y avisando de estereoquímica.

Uso:
    uv run scripts/smiles2svg.py "<SMILES>" -o <ruta.svg> [--legend TEXTO] [--size 300x220] [--preview] [--sin-asterisco]

Los "*" del SMILES se dibujan como R, R', R''... y los carbonos quirales sin
configuración asignada llevan un "*" al lado (desactivable con --sin-asterisco).

stdout: JSON con el SMILES canónico y la estereoquímica detectada.
stderr: avisos legibles.
Exit: 0 OK (aunque haya avisos), 1 SMILES inválido (no escribe nada), 2 uso incorrecto.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from rdkit import Chem, RDLogger
from rdkit.Chem.Draw import rdMolDraw2D


def parse_size(text: str) -> tuple[int, int]:
    try:
        w, h = text.lower().split("x")
        return int(w), int(h)
    except ValueError:
        raise argparse.ArgumentTypeError(f"tamaño inválido '{text}', usa ANCHOxALTO (p. ej. 300x220)")


def stereo_report(mol: Chem.Mol) -> dict:
    centers = Chem.FindMolChiralCenters(mol, includeUnassigned=True, useLegacyImplementation=False)
    stereocenters = [{"atom": idx, "label": label} for idx, label in centers]

    double_bonds = []
    for bond in mol.GetBonds():
        if bond.GetBondType() != Chem.BondType.DOUBLE:
            continue
        stereo = bond.GetStereo()
        if stereo == Chem.BondStereo.STEREONONE:
            # Puede tener isomería E/Z aunque no esté especificada
            info = [si for si in Chem.FindPotentialStereo(mol)
                    if si.type == Chem.StereoType.Bond_Double and si.centeredOn == bond.GetIdx()]
            if not info:
                continue
            label = "?"
        else:
            label = {Chem.BondStereo.STEREOE: "E", Chem.BondStereo.STEREOTRANS: "E",
                     Chem.BondStereo.STEREOZ: "Z", Chem.BondStereo.STEREOCIS: "Z"}.get(stereo, "?")
        double_bonds.append({"bond": bond.GetIdx(),
                             "atoms": [bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()],
                             "label": label})

    return {
        "stereocenters": stereocenters,
        "unassigned_stereocenters": sum(1 for c in stereocenters if c["label"] == "?"),
        "stereo_double_bonds": double_bonds,
    }


def label_for_drawing(mol: Chem.Mol, report: dict, mark_chiral: bool) -> Chem.Mol:
    """Copia de la molécula solo para dibujar: R, R', R''... en los '*' y '*' en los quirales sin asignar."""
    mol = Chem.Mol(mol)
    dummies = [a for a in mol.GetAtoms() if a.GetAtomicNum() == 0]
    for i, atom in enumerate(dummies):
        atom.SetProp("atomLabel", "R" + "'" * i)
    if mark_chiral:
        for center in report["stereocenters"]:
            if center["label"] == "?":
                mol.GetAtomWithIdx(center["atom"]).SetProp("atomNote", "*")
    return mol


def draw(mol: Chem.Mol, size: tuple[int, int], legend: str, drawer_cls) -> rdMolDraw2D.MolDraw2D:
    drawer = drawer_cls(*size)
    opts = drawer.drawOptions()
    opts.addStereoAnnotation = True  # muestra (R)/(S), (E)/(Z) en el dibujo
    opts.clearBackground = False     # fondo transparente: se ve bien en tema oscuro de Obsidian
    opts.annotationFontScale = 0.9   # el '*' de carbono quiral, legible
    # Paleta Apuntes.md (la misma que las figuras TikZ y el CSS): O rojo, N azul, resto neutro
    opts.updateAtomPalette({8: (0.714, 0.263, 0.259),    # #B64342
                            7: (0.059, 0.302, 0.573),    # #0F4D92
                            6: (0.153, 0.153, 0.153),    # #272727
                            0: (0.153, 0.153, 0.153)})   # R, R'
    opts.bondLineWidth = 2
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol, legend=legend)
    drawer.FinishDrawing()
    return drawer


def main() -> int:
    # La consola de Windows no es UTF-8 por defecto: sin esto las tildes salen rotas
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("smiles")
    parser.add_argument("-o", "--output", required=True, type=Path)
    parser.add_argument("--legend", default="")
    parser.add_argument("--size", type=parse_size, default=(300, 220))
    parser.add_argument("--preview", action="store_true", help="genera también un PNG temporal para revisar a ojo")
    parser.add_argument("--sin-asterisco", action="store_true",
                        help="no marcar con '*' los carbonos quirales sin configuración asignada")
    args = parser.parse_args()

    if args.output.suffix.lower() != ".svg":
        parser.error("la salida debe ser un .svg")
    if not args.legend.isascii():
        # RDKit dibuja el texto con su propia fuente y pierde α, β, Δ...: el nombre va en el alt de la nota
        parser.error("--legend solo admite ASCII (escribe 'beta', no 'β'); el nombre completo va en el alt de la imagen")

    RDLogger.DisableLog("rdApp.*")
    mol = Chem.MolFromSmiles(args.smiles)
    if mol is None:
        print(f"ERROR: SMILES inválido: {args.smiles}", file=sys.stderr)
        print(json.dumps({"ok": False, "input": args.smiles, "error": "SMILES inválido"}, ensure_ascii=False))
        return 1

    report = stereo_report(mol)
    drawn = label_for_drawing(mol, report, mark_chiral=not args.sin_asterisco)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    svg = draw(drawn, args.size, args.legend, rdMolDraw2D.MolDraw2DSVG).GetDrawingText()
    args.output.write_text(svg, encoding="utf-8")

    preview = None
    if args.preview:
        png = draw(drawn, (args.size[0] * 2, args.size[1] * 2), args.legend, rdMolDraw2D.MolDraw2DCairo)
        preview = Path(tempfile.gettempdir()) / f"{args.output.stem}-preview.png"
        preview.write_bytes(png.GetDrawingText())

    result = {"ok": True, "input": args.smiles, "canonical": Chem.MolToSmiles(mol),
              "svg": str(args.output), **report, "preview": str(preview) if preview else None}
    print(json.dumps(result, ensure_ascii=False))

    n_centers = len(report["stereocenters"])
    n_dbl = len(report["stereo_double_bonds"])
    if n_centers or n_dbl:
        print(f"AVISO: {n_centers} estereocentro(s) ({report['unassigned_stereocenters']} sin asignar) y "
              f"{n_dbl} doble(s) enlace(s) con posible E/Z. Comprueba contra el original: si la configuración "
              f"no está dibujada, el dibujo plano con '*' en el C quiral es lo correcto; si está dibujada pero "
              f"no se lee, SMILES sin estereo + callout [!warning].", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
