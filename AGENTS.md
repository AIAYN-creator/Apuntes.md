# Instrucciones para agentes en este repo

Este fichero es la fuente de verdad para cualquier agente (Claude Code, Gemini CLI, Codex, Cursor…). `CLAUDE.md` y `GEMINI.md` solo lo importan.

## Qué hay aquí

- **`skills/apuntes-a-md/`**: la skill, en formato [Agent Skills](https://agentskills.io) (`SKILL.md` con `name` y `description`, más `scripts/`, `templates/` y `obsidian/`).
- **Para convertir apuntes**, sigue [`skills/apuntes-a-md/SKILL.md`](skills/apuntes-a-md/SKILL.md) al pie de la letra. No hace falta tenerla instalada como skill: leer ese fichero basta.

## Si modificas el repo

- **La skill tiene que seguir siendo independiente del agente.** Nada de nombres de herramientas de un agente concreto en el `SKILL.md`; describe la acción ("abre la imagen", "escribe el fichero").
- **Los scripts son de línea de comandos.** Python con dependencias inline (PEP 723) y lanzado con `uv run`; Bash para `tikz2svg.sh`. Mensajes para humanos por stderr, resultado por stdout, y códigos de salida 0/1/2 documentados en la cabecera.
- **Fin de línea LF** (lo fuerza `.gitattributes`). Escribe los ficheros con la herramienta de ficheros y no con heredocs: en Git Bash las capas de escape se comen las `\`.
- **`pruebas/escaneos/` y `pruebas/salida/` no se suben**: son apuntes personales.
- **Commits**: un commit por cambio coherente, en español, terminado con el trailer `Supervised-by: <agente> <correo>`. El agente figura como supervisor, no como coautor.
- **Antes de dar una figura por buena**, mira el preview del **SVG final** (`tikz2svg.sh --preview`), no el PDF.
