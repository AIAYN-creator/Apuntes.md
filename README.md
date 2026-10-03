# Apuntes.md

Skills para Claude (Claude Code) que convierten apuntes escritos a mano y escaneados en notas Markdown listas para un vault de Obsidian.

```
Escaneo (PDF/imagen) → Claude + skill → nota.md + assets/ → Obsidian
```

Sin API ni app propia: quien interpreta la hoja es Claude dentro de la sesión. Los scripts solo hacen lo que Claude no puede hacer a ojo: dibujar moléculas, compilar diagramas y recortar el escaneo.

## Skills

| Skill | Fase | Qué hace |
|---|---|---|
| [`apuntes-a-md`](skills/apuntes-a-md/) | 1 | Escaneo → `.md` con texto, LaTeX, estructuras (RDKit → SVG), diagramas (TikZ/chemfig → SVG) y recortes del original. Lo dudoso se marca, nunca se inventa. |
| [`enlazar-vault`](skills/enlazar-vault/) | 2 | Segunda pasada sobre notas ya convertidas: enlaces internos, tags y MOC por asignatura. *Pendiente.* |

## Requisitos (Windows)

- **Python ≥ 3.12** y **[uv](https://docs.astral.sh/uv/)**: los scripts declaran sus dependencias inline (PEP 723) y se ejecutan con `uv run`; no hay venv que crear.
- **MiKTeX** con "Install missing packages on-the-fly: Always" (incluye `pdflatex`, `dvisvgm` y `pdftocairo`).
- **Git Bash** para `tikz2svg.sh`.

## Instalación de la skill en Claude Code

Enlaza la carpeta de la skill en `~/.claude/skills/` con un *junction* (así los cambios del repo se ven al instante, sin copiar):

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\apuntes-a-md" -Target "<ruta-al-repo>\skills\apuntes-a-md"
```

## Configurar Obsidian

**No necesitas ningún plugin.** Todo lo que generan las skills lo muestra Obsidian de serie:

| En la nota | Obsidian |
|---|---|
| Imágenes SVG/PNG con enlace Markdown relativo | ✅ de serie |
| Fórmulas `$...$` / `$$...$$` | ✅ de serie (MathJax) |
| Callouts `> [!warning]`, `> [!todo]` | ✅ de serie |
| Resaltado `==texto (?)==` | ✅ de serie |
| Diagramas TikZ | Se compilan a SVG antes, así que no hace falta TikZJax |

Solo hay que hacer dos cosas:

1. **Modo oscuro** (si lo usas): los SVG son líneas negras sobre fondo transparente. Copia [`svg-modo-oscuro.css`](skills/apuntes-a-md/obsidian/svg-modo-oscuro.css) a `<vault>/.obsidian/snippets/` y actívalo en *Ajustes → Apariencia → Fragmentos CSS*.
2. **Ajustes → Archivos y enlaces**:
   - *Actualizar enlaces internos automáticamente*: **activado**. Si mueves una nota a mano desde Obsidian, se actualizan sus enlaces a los assets.
   - *Formato de los nuevos enlaces*: **Ruta relativa al archivo**, el mismo formato que generan las skills.

## Ordenar el vault

`ordenar_vault.py` coloca las notas de apuntes en `<vault>/<Asignatura>/` según su frontmatter, moviendo también sus assets. Por defecto solo simula; nunca edita ni sobrescribe notas.

```bash
uv run skills/apuntes-a-md/scripts/ordenar_vault.py <vault> --desde pruebas/salida
uv run skills/apuntes-a-md/scripts/ordenar_vault.py <vault> --desde pruebas/salida --aplicar
```

## Estructura

```
skills/
  apuntes-a-md/      SKILL.md, templates/, scripts/, obsidian/
  enlazar-vault/     SKILL.md (Fase 2)
pruebas/
  escaneos/          hojas reales de prueba (no se suben)
  salida/            notas generadas en pruebas (no se suben)
```

Las convenciones (nombres de assets, frontmatter, marcas de duda, interfaz de los scripts) están documentadas en el propio `SKILL.md`.

## Licencia

[MIT](LICENSE)
