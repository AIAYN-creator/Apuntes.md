# Changelog

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
