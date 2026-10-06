# Changelog

## v2.1.0 — 2026-10-06

Los dibujos figurativos, la parte más floja de la v2, ya están a la altura del resto. **Criterio de vida superado:** revisión del usuario aprobada.

### Iconos de Bioicons, con licencia controlada
- `iconos.py`:
  - busca en el catálogo;
  - muestra la licencia, el autor y el tamaño **sin descargar**;
  - descarga **solo bajo demanda y con permiso**, y **rechaza CC-BY-SA**;
  - registra la atribución en `iconos/ICONOS.md` y comprueba las licencias.
- `iconos.py pdf` pasa el icono a PDF para componerlo en TikZ con las etiquetas en tipografía:
  - recorta al dibujo;
  - pasa los colores a la paleta (`--paleta`) y quita los fondos de lámina (`--sin-fondo`);
  - lee los colores por clase CSS de los SVG de Illustrator y avisa de los iconos que no son vectoriales.
- Iconos usados: 9, todos CC0 o CC-BY. Uno es derivado (un fosfolípido de una cola). La atribución va en el frontmatter de cada nota (`creditos`) y en la [galería](galeria/#créditos-de-iconos).

### Recorte vectorial del propio dibujo
- `recorte_vectorial.py` exporta los trazos de tableta de una zona como SVG/PDF nítido:
  - `--excluir` quita las etiquetas escritas a mano;
  - `--paleta` pasa los colores a la paleta;
  - el script imprime el marco del dibujo para colocar las etiquetas en TikZ.
- `tikz2svg.sh` usa `pdftocairo` cuando la figura incrusta un recorte (`dvisvgm` lo dejaba en blanco sin avisar).
- Regla: **si un icono pierde contenido del dibujo, gana el recorte.**

### Entregable
- Bioquímica, temas 1–4: las 9 figuras figurativas rehechas.
  - **3 con iconos:** jerarquía, lípidos y niveles de estructura.
  - **6 con recorte vectorial:** α-hélice, hoja β, plegamiento, renaturalización, purificación y columna.
- Las notas no cambian: cada figura conserva su nombre y el contenido verifica igual.
- [Galería](galeria/) con antes/después (niveles, jerarquía, lípidos y columna) y la hoja con las 9 figuras.

## v2.0.0 — 2026-10-04

Los 4 primeros temas de Bioquímica, perfectos y conforme a todas las especificaciones de la versión. **Criterio de vida superado:** revisión del usuario aprobada.

### Independiente del agente
- La skill sigue el formato abierto [Agent Skills](https://agentskills.io): Claude Code, Gemini CLI, Codex…
- El `SKILL.md` no nombra herramientas de ningún agente.
- `AGENTS.md` es la fuente de verdad para quien trabaje en el repo; `CLAUDE.md` y `GEMINI.md` lo importan.
- `instalar.ps1` enlaza la skill en `~/.claude`, `~/.gemini`, `~/.codex` o `~/.agents`.

### Una nota por tema
- `<Asignatura> - Tema <N>.md`, nombre único en el vault, con alias `Tema <N>`.
- Frontmatter con `tema`, `titulo`, `fechas`, `fuente` y `aliases`.
- Índice plegable, marcas de página invisibles y callout de sesión solo cuando hay fecha escrita.
- Los temas que crecen se amplían al final, sin reconvertir.

### Estética didáctica, sin tocar el contenido
- Lista blanca de 10 mejoras: definiciones, puntos importantes, fórmulas destacadas (solo ecuaciones sueltas de una línea), términos en negrita, tablas, fichas plegables, anchos de figura y figuras lado a lado. Más la lista negra y las etiquetas fijas.
- **Dos pasadas** (transcripción fiel y luego estética) y **`verificar_contenido.py`**, que compara palabra por palabra. Una nota que no da OK no se entrega.
- `obsidian/apuntes-estetica.css`: callouts propios y paleta.

### Figuras
- Estilo común Apuntes.md (principios de figures4papers, sin copiar código):
  - Helvetica + `sansmath`;
  - paleta semántica compartida con el CSS y con RDKit;
  - estilos con nombre (`curva`, `anotacion`, `marca`…), sin colores sueltos.
- `tikz2svg.sh`:
  - falla si el texto se fuera a perder (fuentes Type 3);
  - el preview es del SVG final;
  - compila dos veces cuando hay `\chemmove`.
- `smiles2svg.py`: grupos R como R/R′ y `*` en los carbonos quirales sin configuración.

### Entregable
- Bioquímica, Temas 1–4 (págs. 2–11): 21 figuras, 9 moléculas y 2 751 palabras verificadas. Publicado en la [galería](galeria/), con las páginas originales, comparativas antes/después y capturas en Obsidian.

### Pendiente → v2.1
- Los dibujos figurativos (columna de cromatografía, α-hélice…) son la parte más floja. Se sustituyen por iconos con licencia libre o por recortes vectoriales del propio dibujo.

## v1.0.0 — 2026-10-04

Primera versión: conversión fiel de apuntes escritos a mano y escaneados a notas Markdown para Obsidian.

**Criterio de vida superado.** Con apuntes reales de Bioquímica (págs. 6–7 del Tema 2), la nota se retoca en bastante menos de 5 minutos y no se inventa estereoquímica que no esté en la hoja.

### Skill `apuntes-a-md`
- Flujo: localizar sobre cuadrícula → leer por franjas → inventario → nota → verificar cada asset → resumen.
- Lectura de letra a mano apoyada en el contexto, en tres niveles de confianza. Nunca se corrige, se reescribe ni se predicen números.
- Marcas de duda (`(?)`, `[!warning]` con el recorte del original, `[!todo]`) y posibles erratas transcritas tal cual.
- Estereoquímica:
  - del dibujo si se lee;
  - del nombre escrito en la hoja;
  - plano con `*` en el C quiral si no está dibujada;
  - aviso si está dibujada pero no se lee.
- Fecha: la de la hoja o, si no tiene, la anterior del cuaderno.
- Figuras redibujadas por defecto (TikZ/chemfig/pgfplots), con todas las etiquetas del original y a tamaño legible.

### Scripts
- `smiles2svg.py`: RDKit; JSON con estereocentros; R/R′ para los grupos genéricos y `*` en los quirales sin asignar.
- `tikz2svg.sh`: `pdflatex` → `dvisvgm`. Detecta fuentes Type 3 (el texto se perdería) y hace el preview del SVG final con Edge/Chrome.
- `crop.py`: cuadrícula de coordenadas y recortes por fracciones de página.
- `ordenar_vault.py` (experimental): coloca las notas en `<Asignatura>/` sin editarlas.

### Obsidian
- Sin plugins. Snippet CSS para ver los SVG en modo oscuro.
