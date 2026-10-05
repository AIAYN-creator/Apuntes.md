# Apuntes.md

Una skill para agentes de IA (probada con Claude Code) que convierte **apuntes escritos a mano y escaneados** en notas Markdown listas para un vault de **Obsidian**: texto limpio, fórmulas en LaTeX, estructuras químicas, diagramas redibujados y, lo más importante, **sin inventar nada**.

```
Escaneo (PDF/imagen) → agente + skill → nota.md + assets/ → Obsidian
```

No hay API ni app propia: quien lee la hoja es el agente dentro de la sesión. Los scripts solo hacen lo que el agente no puede hacer a ojo: dibujar moléculas, compilar diagramas y recortar el escaneo.

![Apunte a mano vs. figura redibujada por la skill](galeria/proceso/04-van-der-waals-a-mano-vs-tikz.png)

👉 **[Galería](galeria/)**: 4 temas reales de Bioquímica, con las páginas originales y comparativas antes/después.

**Estado: v2.0.0.** Los **4 primeros temas de Bioquímica**, 11 páginas a mano, convertidos en una nota por tema, con estética didáctica y **verificados palabra por palabra** contra la transcripción. Funciona con cualquier agente compatible con Agent Skills. Ver la [galería](galeria/) y el [CHANGELOG](CHANGELOG.md).

## Qué hace

| En el apunte | En la nota |
|---|---|
| Texto a mano | Markdown con encabezados. La letra difícil se lee **con el contexto**, sin corregir ni reescribir nada |
| Fórmulas | LaTeX (`$...$`, `$$...$$`) |
| Estructuras químicas | SMILES validado con RDKit → SVG. Los grupos R se dibujan como R/R′ y los carbonos quirales sin configuración llevan `*` |
| Diagramas, gráficas, cargas parciales, micelas… | Redibujados en **TikZ/chemfig** → SVG, con todas las etiquetas del original |
| Lo ambiguo | Recorte del original dentro de un aviso `[!warning]`, para que el arreglo sea inmediato |
| Lo dudoso | `==palabra (?)==` o `[!warning]`. **Nunca inventado** |

**Una nota por tema** (`Bioquímica - Tema 1.md`), con índice navegable y una **estética didáctica** (definiciones, puntos importantes, fórmulas destacadas, tablas…) que **no cambia ni una palabra**: se comprueba con un script. Todas las reglas están en [`SKILL.md`](skills/apuntes-a-md/SKILL.md).

### Cómo trabaja

1. **Localiza** cada elemento sobre una cuadrícula y lee la letra por franjas ampliadas.
   ![Cuadrícula de localización](galeria/proceso/01-cuadricula-pag6-aminoacidos.png)
2. **Escribe** la nota elemento a elemento, en el orden del original.
3. **Verifica** cada molécula y figura contra el recorte del original, mirando el SVG final y no un intermedio.
4. **Resume** lo que ha marcado como dudoso y sus decisiones de estereoquímica.

## Requisitos (Windows)

| Programa | Para qué | Instalar |
|---|---|---|
| **[uv](https://docs.astral.sh/uv/)** | Ejecuta los scripts de Python. Cada script declara sus dependencias (RDKit, PyMuPDF, Pillow, PyYAML) y uv las instala solo, sin venv que crear. Si no tienes **Python ≥ 3.12**, uv también lo descarga | `winget install astral-sh.uv` |
| **MiKTeX** | Compila las figuras: `pdflatex`, `dvisvgm`, `pdftocairo` y `pdffonts` | `winget install MiKTeX.MiKTeX`; después, en *MiKTeX Console → Settings*, pon "Install missing packages on-the-fly" en **Always** |
| **Git Bash** | Ejecuta `tikz2svg.sh` | `winget install Git.Git` |
| **Edge o Chrome** *(opcional)* | Preview del SVG final, para comprobar que no se pierde texto. Sin navegador, el preview sale del PDF y no garantiza que el SVG lo tenga todo | Edge viene con Windows |

Los paquetes de LaTeX de la plantilla de figuras (`lmodern`, `helvet`, `sansmath`, `chemfig`, `mhchem`, `pgfplots`…) los descarga MiKTeX la primera vez que se usan. Por eso conviene compilar una figura de prueba con conexión a internet.

Para comprobar que todo está en su sitio:

```bash
uv --version && pdflatex --version && dvisvgm --version && pdftocairo -v
```

**Para usar la skill hace falta además:**
- un agente que pueda ver imágenes/PDF, ejecutar comandos y escribir ficheros (ver la sección siguiente);
- [Obsidian](https://obsidian.md/) para leer las notas (ver [Configurar Obsidian](#configurar-obsidian)).

## Instalación (cualquier agente)

La skill sigue el formato abierto **[Agent Skills](https://agentskills.io)** (`SKILL.md` + `scripts/`), que entienden Claude Code, Gemini CLI, Codex, Cursor, Copilot y otros. Instalarla es enlazar la misma carpeta allí donde cada agente busca sus skills:

```powershell
.\instalar.ps1 -Agentes claude,gemini,codex
```

| Agente | Carpeta de skills | Alternativa propia |
|---|---|---|
| Claude Code | `~/.claude/skills/` | — |
| Gemini CLI | `~/.gemini/skills/` o `~/.agents/skills/` | `gemini skills install <ruta>/skills/apuntes-a-md --consent` |
| Codex | `~/.codex/skills/` | — |

El instalador crea *junctions*, así que los cambios del repo se ven al instante sin copiar nada. Con `-WhatIf` muestra lo que haría sin tocar nada.

El agente tiene que poder **ver imágenes/PDF**, **ejecutar comandos** y **escribir ficheros**.

### Uso

Basta con pedirle algo como *"pasa a Markdown las págs. 6–7 de este escaneo a mi vault"*. En Claude Code también vale `/apuntes-a-md`.

**Lo que hay que darle:**
- el PDF o la imagen, y qué páginas son de qué tema;
- la asignatura, si no se lee en la hoja;
- la ruta del vault.

Si falta algo, la skill lo pregunta antes de escribir nada.

**Al terminar da:**
- la nota;
- el resultado de la verificación de contenido;
- cuántas dudas ha marcado;
- sus decisiones de estereoquímica.

**Si trabajas sobre el repo** con un agente, las instrucciones están en [`AGENTS.md`](AGENTS.md). `CLAUDE.md` y `GEMINI.md` solo lo importan.

> Probada a fondo con Claude Code. En Gemini CLI y Codex la instalación sigue su documentación oficial, pero todavía no se ha probado una conversión completa.

## Scripts

| Script | Qué hace |
|---|---|
| `smiles2svg.py` | Valida el SMILES, dibuja el SVG y devuelve un JSON con los estereocentros (asignados o no) |
| `tikz2svg.sh` | `.tex` → SVG (`pdflatex` + `dvisvgm`, o `pdftocairo` si la figura incrusta un recorte). Falla si el texto se fuera a perder; `--preview` renderiza el SVG final |
| `crop.py` | Cuadrícula de coordenadas y recortes del escaneo |
| `recorte_vectorial.py` | Dibujos de **tableta**: exporta los trazos del autor de una zona como SVG nítido, con opción de pasarlos a la paleta |
| `verificar_contenido.py` | Comprueba que la estética no ha cambiado ni una palabra: compara la transcripción fiel con la nota final |
| `ordenar_vault.py` | Coloca las notas y sus assets en `Universidad/Química/<curso>/<Asignatura>/`. Simula por defecto, nunca sobrescribe y pregunta si las fechas son de otro curso |

## Configurar Obsidian

**No hace falta ningún plugin.** SVG, fórmulas (MathJax), callouts y resaltados se ven de serie. Los diagramas TikZ llegan ya compilados, así que no hace falta TikZJax.

1. **Fragmentos CSS:** copia los dos ficheros de [`obsidian/`](skills/apuntes-a-md/obsidian/) a `<vault>/.obsidian/snippets/` y actívalos en *Ajustes → Apariencia → Fragmentos CSS*:
   - `apuntes-estetica.css`: callouts de definición, importante, fórmula, ficha y sesión, y los colores de la paleta.
   - `svg-modo-oscuro.css`: para ver los SVG en el tema oscuro.
2. **Ajustes → Archivos y enlaces:** activa *Actualizar enlaces internos automáticamente* y pon *Formato de los nuevos enlaces* en **Ruta relativa al archivo**.

## Estructura

```
skills/apuntes-a-md/   SKILL.md, scripts/, templates/, obsidian/
galeria/proceso/       capturas de cómo trabaja la skill
pruebas/               escaneos y salidas de prueba (no se suben)
```

## Hoja de ruta

- **v1.0.0** ✅ Conversión fiel de apuntes a mano a Markdown + Obsidian.
- **v2.0.0** ✅ Skill independiente del agente, una nota por tema, estética didáctica que no toca el contenido (verificada con un script), estilo común de figuras y los 4 temas de Bioquímica.
- **v2.1** Dibujos figurativos con iconos de [Bioicons](https://bioicons.com/) (solo CC0, MIT/BSD y CC-BY con atribución) o con recortes vectoriales del propio dibujo de tableta.
- **v3** Reordenar el vault: arquitectura de carpetas (`Universidad/Química/<curso>/<Asignatura>/`), enlaces internos entre temas, tags e índices por asignatura.

## Licencia

[MIT](LICENSE)
