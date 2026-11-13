# Cómo contribuir

¡Gracias por querer mejorar Apuntes.md! Puedes ayudar aunque no programes: probar la skill con tus apuntes y contar qué falla es de lo más útil.

**Índice**
1. [Formas de contribuir](#1-formas-de-contribuir)
2. [Reportar un fallo](#2-reportar-un-fallo)
3. [Proponer un cambio (pull request)](#3-proponer-un-cambio-pull-request)
4. [Preparar el entorno](#4-preparar-el-entorno)
5. [Las reglas del proyecto](#5-las-reglas-del-proyecto)
6. [Antes de abrir el pull request](#6-antes-de-abrir-el-pull-request)
7. [Versiones y licencia](#7-versiones-y-licencia)

---

## 1. Formas de contribuir

| Si quieres… | Haz esto |
|---|---|
| Contar que algo no funciona | Abre un [issue](https://github.com/AIAYN-creator/Apuntes.md/issues) (sección 2). No hace falta saber programar |
| Probarla con otra asignatura o carrera (Física, Biología, Medicina…) | Convierte unas páginas y cuéntanos en un issue qué ha salido bien y qué mal. Es la mejor forma de encontrar reglas que faltan |
| Mejorar la guía o el README | Pull request (sección 3); si es pequeño, se puede editar desde la web de GitHub |
| Arreglar un fallo o añadir algo | **Abre antes un issue** para hablarlo, sobre todo si es grande, y luego el pull request |

## 2. Reportar un fallo

Abre un [issue nuevo](https://github.com/AIAYN-creator/Apuntes.md/issues/new) y cuenta:

1. **Qué le pediste** al agente (la frase, más o menos).
2. **Qué esperabas** y **qué salió**.
3. **Qué agente** usaste (Claude Code, Gemini CLI…) y la **versión** de Apuntes.md (está en el README: *Estado: v…*).
4. Si es de una figura o de la lectura de la letra: **un recorte de la hoja** y cómo quedó en la nota.

> 🔒 **Privacidad:** no subas tus apuntes completos si no quieres que sean públicos. Un recorte de la zona que falla basta. Nunca subas apuntes de otra persona sin su permiso.

## 3. Proponer un cambio (pull request)

La rama `main` está **protegida**: todo entra por *pull request* (PR), no se puede reescribir el historial ni borrar la rama.

1. **Haz un fork** del repo (botón *Fork* arriba a la derecha en GitHub) y clónalo:
   ```bash
   git clone https://github.com/<tu-usuario>/Apuntes.md.git
   ```
2. **Crea una rama** con un nombre que diga qué haces:
   ```bash
   git checkout -b arreglo/fechas-sin-año      # o mejora/…, docs/…
   ```
3. **Haz los cambios** siguiendo las reglas (sección 5) y comprueba lo de la sección 6.
4. **Sube la rama** y abre el PR contra `main` del repo original. En la descripción, cuenta **qué cambia y por qué**, y cómo lo has probado.
5. Lo revisamos, y si hace falta algo te lo pedimos en el propio PR.

## 4. Preparar el entorno

1. **Instala los requisitos:** uv, MiKTeX (con *Install missing packages: Always*) y Git. Los comandos están en la [guía de uso](USO.md#2-instalar-los-programas). Los scripts de Python declaran sus dependencias dentro (PEP 723) y `uv run` las instala solo: no hay que crear ningún entorno virtual.
2. **Instala las skills desde tu clon**, para que el agente use tu versión mientras la cambias:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\instalar.ps1
   ```
   El instalador crea *junctions*: cada cambio que hagas en el repo lo ve el agente al instante. Si ya tenías instalada otra copia, el instalador avisa y no la toca; bórrala antes (`~\.claude\skills\apuntes-a-md` y `enlazar-apuntes`).
3. **Usa `pruebas/` para tus pruebas.** Está en `.gitignore`: ahí puedes poner escaneos y salidas (`pruebas/escaneos/`, `pruebas/salida/`) sin que se suban nunca.

**Mapa del repo**

```
skills/apuntes-a-md/     la skill de conversión: SKILL.md (las reglas), scripts/, templates/, obsidian/, iconos/
skills/enlazar-apuntes/  la skill de enlazado: SKILL.md y scripts/enlazar.py
docs/                    USO.md (guía), CHANGELOG.md, galeria/ (ejemplo real)
AGENTS.md                instrucciones para agentes que trabajen en el repo (CLAUDE.md y GEMINI.md lo importan)
instalar.ps1             enlaza las skills en los agentes
```

**¿Trabajas con un agente de IA?** Perfecto: lee [`AGENTS.md`](../AGENTS.md) (tu agente lo carga solo si es Claude Code o Gemini CLI). Revisa tú lo que proponga antes de abrir el PR.

## 5. Las reglas del proyecto

Estas reglas son el corazón de la herramienta. Un PR que las rompa no entra, aunque el resto esté bien.

**Sobre el contenido de las notas**
- **Nunca inventar.** Lo dudoso se marca (`==palabra (?)==`, `[!warning]` con recorte del original). Los números, subíndices y unidades no se deducen nunca por contexto. La estereoquímica sale del dibujo o del nombre escrito en la hoja, o no se pone.
- **La estética no toca el contenido.** Toda mejora visual tiene que pasar `verificar_contenido.py` con **OK**: mismas palabras, mismo orden. Si añades una etiqueta fija nueva (como *Resolución*), añádela también al verificador y al `SKILL.md`.
- **Los ejercicios no se resuelven.** Solo se transcribe lo que hay en la hoja.

**Sobre las skills**
- **Independientes del agente.** Nada de nombres de herramientas de un agente concreto en un `SKILL.md`: se describe la acción ("abre la imagen", "escribe el fichero").
- **Los cambios de comportamiento van en el `SKILL.md`**, que es lo que lee el agente. Un script nuevo sin su regla en el `SKILL.md` no se usará nunca.

**Sobre los scripts**
- De línea de comandos, en Python con dependencias inline (PEP 723) y lanzados con `uv run`; Bash solo para `tikz2svg.sh`.
- Mensajes para humanos por *stderr*, resultado por *stdout*, y códigos de salida **0/1/2** documentados en la cabecera.
- Lo que mueve o escribe ficheros **simula por defecto** y nunca sobrescribe sin que se pida.

**Sobre las figuras**
- Usa la plantilla `templates/figura.tex` y los **estilos y colores con nombre** (`anotacion`, `apAzul`…), nunca colores sueltos.
- Da una figura por buena mirando el **preview del SVG final** (`tikz2svg.sh --preview`), no el PDF.
- Escribe los `.tex` con un editor y no con *heredocs* de Git Bash: las capas de escape se comen las `\`.

**Sobre los iconos**
- Solo **CC0, MIT, BSD o CC-BY** con atribución. **CC-BY-SA nunca.**
- Cada icono, con su fila en `iconos/ICONOS.md`, y `iconos.py comprobar` tiene que dar OK.

**Sobre el repo**
- **Fin de línea LF** (lo fuerza `.gitattributes`).
- **Commits en español**, uno por cambio coherente, con un título que diga qué cambia.
- **Si un agente de IA ha hecho el trabajo**, añade al final del mensaje del commit el trailer `Supervised-by: <agente> <correo>`. El agente figura como supervisor, no como coautor: la responsabilidad del cambio es tuya.
- **La documentación para personas va en `docs/`.** En la raíz solo va lo que tiene que estar ahí.

## 6. Antes de abrir el pull request

- [ ] Si tocas la conversión o la estética: has convertido al menos una página real y `verificar_contenido.py` da **OK** contra su transcripción.
- [ ] Si tocas figuras: has mirado el preview del SVG final, en modo claro y oscuro.
- [ ] Si tocas iconos: `uv run skills/apuntes-a-md/scripts/iconos.py comprobar` da OK.
- [ ] Si tocas `ordenar_vault.py` o `enlazar.py`: lo has probado en simulación sobre **una copia** de un vault (por ejemplo, `docs/galeria/bioquimica/` copiada a `pruebas/`).
- [ ] Si cambia el comportamiento: está explicado en el `SKILL.md` correspondiente y, si afecta al usuario, en `docs/USO.md`.
- [ ] Ningún apunte personal ni dato privado en el PR.

No hace falta tocar el `CHANGELOG.md`: lo actualizamos al sacar la versión, a partir de la descripción de tu PR.

## 7. Versiones y licencia

**Versiones:** `vMAYOR.MENOR.PARCHE`.
- **Parche** (v3.0.**1**): arreglos y documentación.
- **Menor** (v3.**1**.0): algo nuevo que no rompe lo anterior.
- **Mayor** (v**4**.0.0): cambios grandes, como una forma distinta de organizar el vault.

**Licencia:** el proyecto es [MIT](../LICENSE). Al contribuir aceptas que tu aportación se publique con esa misma licencia. Los iconos de terceros mantienen la suya (ver `ICONOS.md`).

**Trato:** respeto y paciencia. Mucha gente que usa esto no viene del mundo de la tecnología, y todas las preguntas son bienvenidas.
