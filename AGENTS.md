# Instrucciones para agentes en este repo

Este fichero es la fuente de verdad para cualquier agente (Claude Code, Gemini CLI, Codex, Cursor…). `CLAUDE.md` y `GEMINI.md` solo lo importan.

## Qué hay aquí

- **`skills/apuntes-a-md/`**: la skill de conversión, en formato [Agent Skills](https://agentskills.io) (`SKILL.md` con `name` y `description`, más `scripts/`, `templates/` y `obsidian/`).
- **`skills/enlazar-apuntes/`**: la skill de enlazado (enlaces entre temas, tags y MOC por asignatura).
- **Para convertir apuntes**, sigue [`skills/apuntes-a-md/SKILL.md`](skills/apuntes-a-md/SKILL.md) al pie de la letra; **para enlazarlos**, [`skills/enlazar-apuntes/SKILL.md`](skills/enlazar-apuntes/SKILL.md). No hace falta tenerlas instaladas como skills: leer esos ficheros basta.

## Si modificas el repo

- **La skill tiene que seguir siendo independiente del agente.** Nada de nombres de herramientas de un agente concreto en el `SKILL.md`; describe la acción ("abre la imagen", "escribe el fichero").
- **Los scripts son de línea de comandos.** Python con dependencias inline (PEP 723) y lanzado con `uv run`; Bash para `tikz2svg.sh`. Mensajes para humanos por stderr, resultado por stdout, y códigos de salida 0/1/2 documentados en la cabecera.
- **Fin de línea LF** (lo fuerza `.gitattributes`). Escribe los ficheros con la herramienta de ficheros y no con heredocs: en Git Bash las capas de escape se comen las `\`.
- **`pruebas/` no se sube** (está en `.gitignore`): ahí van los escaneos y las salidas de prueba, que son apuntes personales. Créala en local si la necesitas.
- **Documentación para personas en `docs/`** (`USO.md`, `CHANGELOG.md`, `galeria/`). En la raíz solo queda lo que tiene que estar ahí.
- **Commits**: un commit por cambio coherente, en español, terminado con el trailer `Supervised-by: <agente> <correo>`. El agente figura como supervisor, no como coautor.
- **Antes de dar una figura por buena**, mira el preview del **SVG final** (`tikz2svg.sh --preview`), no el PDF.
