# Apuntes.md

Una skill para agentes de IA (probada con Claude Code) que convierte **apuntes escritos a mano y escaneados** en notas Markdown listas para un vault de **Obsidian**: texto limpio, fórmulas en LaTeX, estructuras químicas, diagramas redibujados y, lo más importante, **sin inventar nada**.

```
Escaneo (PDF/imagen) → agente + skill → nota.md + assets/ → Obsidian
```

No hay API ni app propia: quien lee la hoja es el agente dentro de la sesión. Los scripts solo hacen lo que el agente no puede hacer a ojo: dibujar moléculas, compilar diagramas y recortar el escaneo.

![Apunte a mano vs. figura redibujada por la skill](galeria/proceso/04-van-der-waals-a-mano-vs-tikz.png)

**Estado: v1.0.0.** Probada con apuntes reales de Bioquímica: una hoja con texto, fórmulas, estructuras y una gráfica se retoca en **menos de 5 minutos**, y la estereoquímica que no está en la hoja no se inventa. Ver [CHANGELOG](CHANGELOG.md).

## Qué hace

| En el apunte | En la nota |
|---|---|
| Texto a mano | Markdown con encabezados. La letra difícil se lee **con el contexto**, sin corregir ni reescribir nada |
| Fórmulas | LaTeX (`$...$`, `$$...$$`) |
| Estructuras químicas | SMILES validado con RDKit → SVG. Los grupos R se dibujan como R/R′ y los carbonos quirales sin configuración llevan `*` |
| Diagramas, gráficas, cargas parciales, micelas… | Redibujados en **TikZ/chemfig** → SVG, con todas las etiquetas del original |
| Lo ambiguo | Recorte del original dentro de un aviso `[!warning]`, para que el arreglo sea inmediato |
| Lo dudoso | `==palabra (?)==` o `[!warning]`. **Nunca inventado** |

Cada nota lleva un frontmatter mínimo (`asignatura`, `tema`, `fecha`, `fuente`). Todas las reglas están en [`SKILL.md`](skills/apuntes-a-md/SKILL.md).

### Cómo trabaja

1. **Localiza** cada elemento sobre una cuadrícula y lee la letra por franjas ampliadas.
   ![Cuadrícula de localización](galeria/proceso/01-cuadricula-pag6-aminoacidos.png)
2. **Escribe** la nota elemento a elemento, en el orden del original.
3. **Verifica** cada molécula y figura contra el recorte del original, mirando el SVG final y no un intermedio.
4. **Resume** lo que ha marcado como dudoso y sus decisiones de estereoquímica.

## Requisitos (Windows)

- **Python ≥ 3.12** y **[uv](https://docs.astral.sh/uv/)**: los scripts declaran sus dependencias inline (PEP 723) y se ejecutan con `uv run`, sin venv que crear.
- **MiKTeX** con "Install missing packages on-the-fly: Always" (trae `pdflatex`, `dvisvgm`, `pdftocairo` y `pdffonts`).
- **Git Bash** para `tikz2svg.sh`.
- **Edge o Chrome** (opcional, recomendado) para el preview del SVG final.

## Instalación (Claude Code)

Enlaza la carpeta de la skill en `~/.claude/skills/` con un *junction*. Así los cambios del repo se ven al instante, sin copiar:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\apuntes-a-md" -Target "<ruta-al-repo>\skills\apuntes-a-md"
```

Después basta con pedirle al agente algo como *"pasa a Markdown las págs. 6–7 de este escaneo a mi vault"*.

## Scripts

| Script | Qué hace |
|---|---|
| `smiles2svg.py` | Valida el SMILES, dibuja el SVG y devuelve un JSON con los estereocentros (asignados o no) |
| `tikz2svg.sh` | `.tex` → SVG (`pdflatex` + `dvisvgm`). Falla si el texto se fuera a perder; `--preview` renderiza el SVG final |
| `crop.py` | Cuadrícula de coordenadas y recortes del escaneo |
| `ordenar_vault.py` | *Experimental:* coloca las notas en `<Asignatura>/` según su frontmatter. Se rediseña en la v2 |

## Configurar Obsidian

**No hace falta ningún plugin.** SVG, fórmulas (MathJax), callouts y resaltados se ven de serie. Los diagramas TikZ llegan ya compilados, así que no hace falta TikZJax.

1. **Modo oscuro:** copia [`svg-modo-oscuro.css`](skills/apuntes-a-md/obsidian/svg-modo-oscuro.css) a `<vault>/.obsidian/snippets/` y actívalo en *Ajustes → Apariencia → Fragmentos CSS*.
2. **Ajustes → Archivos y enlaces:** activa *Actualizar enlaces internos automáticamente* y pon *Formato de los nuevos enlaces* en **Ruta relativa al archivo**.

## Estructura

```
skills/apuntes-a-md/   SKILL.md, scripts/, templates/, obsidian/
galeria/proceso/       capturas de cómo trabaja la skill
pruebas/               escaneos y salidas de prueba (no se suben)
```

## Hoja de ruta

- **v1.0.0** ✅ Conversión fiel de apuntes a mano a Markdown + Obsidian.
- **v2** (en diseño) Skill independiente del agente, estética didáctica acordada (sin tocar el contenido), figuras de más calidad y los temas completos de Bioquímica como entregable.

## Licencia

[MIT](LICENSE)
