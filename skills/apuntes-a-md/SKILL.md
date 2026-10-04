---
name: apuntes-a-md
description: Convierte apuntes y ejercicios escritos a mano y escaneados (PDF o imagen) en notas Markdown para Obsidian, con fórmulas en LaTeX, estructuras químicas como SMILES + SVG (RDKit), diagramas redibujados en TikZ/chemfig y compilados a SVG, y recortes del original para lo que no se puede redibujar. Usa esta skill cuando el usuario pase un escaneo de apuntes (química, bioquímica, biología, física...) y pida pasarlo a Markdown, a Obsidian, a su vault o "a limpio". Nunca inventa: lo dudoso se marca de forma visible.
---

# Apuntes a Markdown

Conviertes un escaneo de apuntes a mano en **una nota `.md` + su carpeta de assets**, lista para Obsidian. Lo que importa, por este orden:

1. **No inventar.** Un dato inventado (sobre todo estereoquímica) es peor que un hueco marcado. Ante la duda, se marca (sección 5).
2. **Fidelidad al original.** Transcribes, no redactas: no resumes, no reordenas, no "mejoras" el texto, no corriges al autor. Para *leer* la letra a mano sí te ayudas del contexto (sección 5a).
3. **Poco retoque.** La nota debe quedar lista con menos de 5 minutos de revisión humana.

Los scripts están en `scripts/` de esta skill. Lánzalos con la ruta de la skill delante (Python con `uv run`, que instala solo sus dependencias; el `.sh` con `bash`).

**Lo que necesitas de tu entorno**, seas el agente que seas (Claude Code, Gemini CLI, Codex…):
- **Ver imágenes y PDF**: toda la skill se apoya en mirar el escaneo, las cuadrículas y los previews.
- **Ejecutar comandos de shell**: para los scripts.
- **Escribir ficheros**: para la nota, los `.tex` y los assets.

Si te falta alguna de las tres, díselo al usuario antes de empezar en vez de improvisar.

## 1. Antes de empezar

Necesitas saber, y si no lo sabes **pregunta antes de escribir nada**:

- La ruta del **escaneo** y, si es un PDF, qué páginas.
- La ruta del **vault** (o de la carpeta de salida).
- **Asignatura** y **tema**, si no se leen en la hoja. Si el escaneo es un cuaderno y el título del tema está en una página anterior del mismo PDF, puedes tomarlo de ahí, pero dilo en el `[!warning]` inicial.

## 2. Dónde va cada cosa

```
<vault>/<Asignatura>/<tema-slug>.md
<vault>/<Asignatura>/assets/<tema-slug>/<asset>
```

- `tema-slug`: el tema en kebab-case y sin tildes (`ciclo-de-krebs`), **como mucho 5 palabras**. Si el título es largo ("Tema 2: Aminoácidos, enlace peptídico, estructuras…"), quédate con el número y el núcleo del contenido de esas páginas (`tema-2-aminoacidos`); el título completo va en `tema`. Si la nota ya existe, añade `-2`, `-3`… **Nunca sobrescribas una nota existente.**
- Assets: `<tipo>-<NN>[-<desc>].<ext>`.
  - `tipo`: `mol` (`.svg` de RDKit), `fig` (`.tex` + `.svg`, mismo nombre base) o `crop` (`.png`).
  - `NN`: dos dígitos, numeración propia por tipo, en orden de aparición.
  - `desc`: opcional, kebab-case, como mucho 3 palabras.
- Los enlaces son **Markdown relativo**: `![alt](assets/<tema-slug>/mol-01-glucosa.svg)`. Nunca `![[...]]`.

## 3. Frontmatter (exactamente estos 4 campos)

```yaml
---
asignatura: Bioquímica
tema: Ciclo de Krebs
fecha: 2026-09-28
fuente: "bq-krebs.pdf#p3"
---
```

- `fecha`: la fecha **escrita en la hoja**. Si la hoja no lleva fecha, usa la **fecha inmediatamente anterior** del mismo cuaderno o PDF: retrocede página a página hasta encontrar una (los apuntes se fechan al empezar la clase y las páginas siguientes son de la misma sesión). Esto no lleva aviso. Solo si no hay ninguna fecha antes, pon `null` y añade un `[!warning]` al principio de la nota. No uses nunca la fecha de hoy.
- `fuente`: nombre del archivo, más `#p<N>` o `#p<N>-<M>` si es un PDF.
- No añadas `tags` ni otros campos: los tags son cosa de la skill `enlazar-vault`.

## 4. Flujo de trabajo

### Paso 1: leer y localizar
1. Abre el escaneo (PDF o imagen) con la herramienta de tu entorno que te deja **ver** archivos.
2. Para cada página, saca la vista con cuadrícula. Te servirá para dar coordenadas a los recortes:
   ```bash
   uv run <skill>/scripts/crop.py <escaneo> --page N --render <tmp>/pN-grid.png --grid
   ```
   Las coordenadas de `--box` se leen **siempre en esta imagen con cuadrícula**: no las estimes a partir de otra vista de la página, porque cada vista tiene márgenes y escalas distintos.
3. **Para leer la letra**, recorta la página en 4–5 franjas horizontales a ~160 ppp (`--box 0 Y0 1 Y1 --pad 0 --dpi 160`) y amplía a 300 ppp las líneas dudosas, sobre todo números y subíndices.
4. **Inventario antes de escribir.** Recorre la página de arriba abajo y lista cada elemento con su tipo (texto, fórmula, estructura, diagrama, gráfica) y su caja aproximada. No redactes nada todavía.

### Paso 2: escribir la nota, elemento a elemento, en el orden del original

| Elemento | Cómo |
|---|---|
| **Texto** | Markdown limpio. Los títulos y subtítulos de la hoja pasan a `#`/`##`/`###`, las listas a listas, y lo subrayado, recuadrado, resaltado con fluorescente o escrito en otro color para destacar pasa a **negrita**. No uses `==resaltado==` para lo que el autor resaltó: está reservado para las dudas. Las abreviaturas y las comillas de "ídem" (`"`) se dejan tal como están escritas. |
| **Fórmulas** | LaTeX: `$...$` en línea y `$$...$$` en bloque (en líneas propias). En la nota **no uses `\ce{}`**, porque Obsidian no carga mhchem: usa `\rightarrow`, `\rightleftharpoons`, `\xrightarrow{\text{enzima}}`… |
| **Estructura química** | SMILES → `smiles2svg.py` (sección 6). |
| **Diagrama o dibujo esquemático** (flechas, ciclos, rutas, perfil de energía, gráfica, montaje, cargas parciales δ⁺/δ⁻ sobre moléculas, micelas, bicapas, hélices, formas de lípidos…) | Redibújalo en TikZ/chemfig → `tikz2svg.sh` (sección 7). |
| **Diagrama ambiguo**, o dibujo realista (célula, orgánulo, aparato con detalle) | Recórtalo con `crop.py` y pon un callout `[!todo]` (sección 5c). |

**Cuándo redibujar y cuándo recortar:** por defecto, **redibuja**. El usuario prefiere el dibujo limpio al pantallazo, y un dibujo esquemático hecho a mano (aunque sea figurativo: micelas, vesículas, cabezas y colas de lípidos) se puede reproducir con TikZ. Recorta solo si el original es **ambiguo** (no sabes qué representa una flecha o una forma, o falta alguna etiqueta) o si es un dibujo realista que no se puede esquematizar sin perder información. Lo que se lee pero no se entiende va como recorte dentro del `[!warning]`, porque así el arreglo es inmediato.

### Paso 3: verificar cada asset
Usa `--preview` en ambos scripts y **compara el PNG de preview con el recorte del original**. Comprueba que los átomos, los enlaces, las flechas y las etiquetas coinciden. Si no coinciden y no sabes corregirlo, cambia ese elemento por recorte + `[!todo]`.

### Paso 4: cierre
Relee la nota entera contra el escaneo. Después, dale al usuario un resumen corto:
- la ruta de la nota;
- cuántos `[!warning]`, `[!todo]` y `(?)` hay;
- **la lista de decisiones de estereoquímica**: qué SMILES llevan estereo y de dónde salió (del dibujo o del nombre).

## 5. Marcas de duda

Todo lo dudoso tiene que poder encontrarse buscando `[!warning]`, `[!todo]` o `(?)`.

**a) Palabras difíciles de leer (letra a mano).** La caligrafía del autor es difícil. **Léela como lo haría un compañero de clase**: las letras que se entienden mal se reconstruyen con el contexto, igual que el texto predictivo completa una palabra a medio escribir. Lo que se reconstruye es la **lectura** (qué palabra escribió el autor), nunca el **contenido** (qué debería haber escrito).

Pistas de contexto, de más a menos fiables:
1. La **misma palabra escrita más clara** en otra parte de la hoja.
2. **Lo que hay dibujado o escrito al lado**: la estructura, la enzima sobre la flecha, la fórmula.
3. El **vocabulario de la asignatura y el tema** (en bioquímica: metabolitos, enzimas, cofactores…).
4. La **frase**: qué palabra encaja en esa posición gramatical y con ese número de letras.

Según lo seguro que estés, haces una de tres cosas:

| Confianza | Ejemplo | Qué escribes |
|---|---|---|
| **Alta**: solo una palabra encaja con las letras visibles y con el contexto | `glu_ól_s_s` en una hoja de rutas metabólicas | La palabra, **sin marca**: `glucólisis` |
| **Media**: hay una lectura claramente más probable, pero otra es posible | `pir_v_to` junto a una flecha de la glucólisis | La más probable marcada: `==piruvato (?)==` |
| **Baja**: varias lecturas plausibles, o no se ve forma de palabra | | Las candidatas, `==piruvato / pirimidina (?)==`, o si no hay ninguna, `==ilegible (?)==` |

Límites, que no cambian aunque la confianza sea alta:
- **Solo se lee, no se edita.** Nada de corregir la ortografía, cambiar palabras por sinónimos, completar frases a medias, añadir palabras que faltan ni reordenar. Si el autor escribió mal una palabra **y se lee claramente**, se transcribe tal cual. El contexto solo decide entre lecturas de letras que realmente son ambiguas.
- **Abreviaturas tal cual** (`rx`, `enz.`, `cte`): no se expanden.
- **Números, cargas, subíndices, coeficientes y unidades no se predicen.** El contexto no puede saber si es un 2 o un 3. Si no se lee, va marcado con `(?)`.
- **Si una lectura reconstruida cambia el significado químico** (un nombre de compuesto que cambiaría el SMILES, un nombre de enzima), no basta la confianza alta: márcalo con `(?)`.

```markdown
…en la glucólisis, la ==piruvato carboxilasa (?)== se activa por acetil-CoA y el NADH se reoxida en la ==ilegible (?)==…
```

**b) Bloque dudoso** (fórmula, estructura, estereoquímica o una posible errata del original): callout con lo que leíste, la alternativa si la hay y el recorte del original.
```markdown
> [!warning] Dudoso: estereoquímica en C2
> No se distingue si el OH de C2 está a la izquierda o a la derecha en la proyección de Fischer.
> SMILES sin estereo: `OCC(O)C(O)C(O)C(O)C=O`
> ![original](assets/glucolisis/crop-02.png)
```
Si el original parece tener un error (un signo, un subíndice…), **transcribe lo que pone** y añade `> [!warning] Posible errata en el original`. No lo corrijas.

**Pon siempre el recorte del original dentro del `[!warning]`.** Así el usuario resuelve la duda de un vistazo, sin abrir el escaneo.

**c) Diagrama no redibujado:**
```markdown
> [!todo] TODO: redibujar esquema de la cadena de transporte electrónico
> ![original](assets/fosforilacion-oxidativa/crop-03-cadena.png)
```

## 6. Estructuras químicas

```bash
uv run <skill>/scripts/smiles2svg.py "<SMILES>" -o <vault>/<Asig>/assets/<slug>/mol-NN-desc.svg --preview
```

Devuelve un JSON por stdout (`canonical`, `stereocenters`, `unassigned_stereocenters`, `stereo_double_bonds`, `preview`). Si el exit es 1, el SMILES no es válido: corrígelo o recorta.

En la nota se escribe así:
```markdown
![α-D-glucopiranosa](assets/glucolisis/mol-01-glucosa.svg)
`smiles: OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@@H]1O`
`estereo: por nombre (α-D-glucopiranosa)`
```
- El nombre completo, con letras griegas, va en el **alt** de la imagen. `--legend` solo admite ASCII, así que por defecto no lo uses.
- Escribe el SMILES `canonical` que devuelve el script.
- Los `*` del SMILES (grupos R) se dibujan como **R, R′, R″…**, y los carbonos quirales sin configuración llevan un **`*`** al lado.
- Si lo escrito en la hoja **no es un SMILES válido** (p. ej. R–CO–NH₃ sin carga: el N tendría 4 enlaces), no lo "arregles" para que RDKit lo acepte. Dibújalo **tal cual con chemfig** (`fig-NN`, colores O rojo y N azul como RDKit) y sin línea `smiles:`.

### Regla crítica: estereoquímica

El script avisa de todos los estereocentros y dobles enlaces E/Z. Para cada uno:

| Situación en el original | Qué haces |
|---|---|
| Cuñas o guiones, posiciones en Fischer/Haworth, R/S o E/Z **legibles sin duda** | SMILES isomérico + `` `estereo: del dibujo` `` |
| Sin dibujo claro, pero el **nombre escrito en la hoja** fija la configuración (D-glucosa, L-alanina, α/β, *cis*/*trans*, *(R)*-…) | SMILES isomérico + `` `estereo: por nombre (<nombre tal cual>)` `` |
| Carbono quiral **sin configuración dibujada** (dibujo plano, sin cuñas ni Fischer/Haworth). Es lo habitual cuando se representan ambos enantiómeros o la configuración da igual | SMILES **sin** estereo; el dibujo sale plano con **`*` en el carbono quiral** (lo pone `smiles2svg.py`) + `` `estereo: sin indicar (C* quiral)` ``. **Sin aviso**: no es una duda, es una convención |
| El nombre y el dibujo **se contradicen** | SMILES **sin** estereo + `[!warning]` explicando la contradicción |
| La configuración **está dibujada pero no se lee** (cuña o guion indistinguible, un OH borroso en Fischer) | SMILES **sin** estereo (sin `@` ni `/\`) + `[!warning]` + recorte |

**Nunca** completes la estereoquímica por tu cuenta ("es la natural", "la habitual"). Solo cuenta lo que pone la hoja, sea en el dibujo o en el nombre.

### Casos de bioquímica
- **Fischer/Haworth:** RDKit dibuja la fórmula esquelética y la proyección se pierde. Si la proyección es lo que enseña la hoja (anómeros, ciclación, D/L), añade también el recorte del original debajo, sin `[!todo]`.
- **Grupos R genéricos** (aminoácido genérico, ácido graso "R-COOH"): usa `*` en el SMILES (`*C(N)C(=O)O`).
- **Esquemas abreviados** (ATP como "Adenina–Ribosa–P–P–P", péptidos con cajas, polímeros con `n`): no los conviertas en SMILES. Son diagramas: redibuja con TikZ o recorta.

## 7. Diagramas redibujados

1. Copia `templates/figura.tex` a `assets/<slug>/fig-NN-desc.tex` y sustituye **solo** el cuerpo. No añadas la opción `tikz` a `standalone`. Escribe el `.tex` con la herramienta de tu entorno para escribir ficheros, no con un heredoc de shell: las capas de escape se comen los saltos de línea `\\` de TikZ.
2. Compila:
   ```bash
   bash <skill>/scripts/tikz2svg.sh <vault>/<Asig>/assets/<slug>/fig-NN-desc.tex --preview
   ```
   Si falla, el script imprime los errores de LaTeX. Corrige y repite; tras dos intentos fallidos, recorta y pon un `[!todo]`.
3. En la nota solo enlazas el `.svg`. El `.tex` se queda al lado como fuente.
4. **Comprueba las anotaciones en el preview.** El `--preview` es del **SVG final** (el que verá Obsidian), no del PDF. Haz una lista de cada palabra o etiqueta escrita a mano dentro o alrededor del dibujo original (ejes, flechas, nombres, "Máxima atracción…") y comprueba que **todas** se leen en el preview. Si falta alguna, la figura no está terminada.

La plantilla trae `chemfig` (estructuras y esquemas de reacción), `mhchem` (`\ce{}` sí funciona **dentro** del `.tex`), TikZ y `pgfplots`, además del **estilo Apuntes.md**: letra sans-serif (Helvetica + `sansmath`, como Obsidian), la paleta y estilos con nombre. **Usa siempre los estilos y colores con nombre, nunca colores sueltos** (`red`, `blue!70!black`…): así todas las figuras se ven iguales y el estilo se cambia en un solo sitio.

| Para… | Usa |
|---|---|
| La curva o el dato principal | `curva` (rojo, 1,6 pt); `curva secundaria` (azul claro) |
| Texto escrito a mano alrededor del dibujo | `anotacion` (azul, tamaño normal) |
| Flechas de anotación / "implica" (⟹) | `flecha` / `implica` |
| Puntos destacados (pK, máximos…) | `node[marca, label={[anotacion]above:…}]` |
| Óvalos o círculos que rodean algo | `resalte` |
| Líneas guía (y = 0, asíntotas) | `referencia` (gris punteado) |
| Ejes de pgfplots | `\begin{axis}[apuntes, …]` |
| Colores sueltos | `apAzul`, `apRojo`, `apVerde`, `apGris`, `apNegro` y sus variantes `…Claro` |

Los colores siguen la semántica de los apuntes: **rojo** para lo que el autor dibuja en rojo (curvas, estructuras) y **azul** para sus anotaciones. Es la misma paleta del CSS de Obsidian y de las moléculas de RDKit.

- **Rutas y ciclos metabólicos:** nodos con los metabolitos y la enzima sobre la flecha, **solo con las etiquetas que aparecen en la hoja**. No completes intermedios que no estén escritos.
- **Gráficas** (Michaelis-Menten, Lineweaver-Burk, curvas de valoración): si la hoja da la ecuación o los valores, dibújala con pgfplots usando esos datos. Si es una curva hecha a mano sin datos, dibuja solo la **forma cualitativa**, con los ejes y las marcas que ponga la hoja (`Vmax`, `Km`…) y sin números inventados en los ejes.
- **Todas las etiquetas a tamaño normal** (`font=\normalsize`, nunca `\scriptsize` ni `\small`): tienen que leerse igual que los números de los ejes. Si no caben, agranda la escala de la figura (`x=2cm, y=2cm`) en vez de encoger la letra.
- **Cargas parciales sobre moléculas:** `\chemabove{C}{\delta^+}` en chemfig. Para δ en un extremo de enlace sin átomo, usa `\chemabove{}{\delta^-}`.
- **Colores:** respeta los del original con la paleta (`\color{apRojo}` para estructuras en rojo, `anotacion`/`apAzul` para lo azul). No pongas `color=` en `every picture`: pisaría los `\color` de chemfig. El CSS de modo oscuro los mantiene reconocibles.
- **Dibujos repetitivos** (micelas, bicapas, vesículas): define una macro para la unidad (cabeza + colas) y colócala con `\foreach` en círculo o en fila. Ojo con la orientación: en micelas y en la capa externa de las vesículas, las cabezas van **fuera** y las colas **dentro**.

## 8. Checklist final

- [ ] Frontmatter con los 4 campos; `fecha` sacada de la hoja, o la anterior del cuaderno, o `null` con su aviso.
- [ ] Todo el contenido de la hoja está, en el mismo orden.
- [ ] Cada estructura tiene su `smiles:`, y cada SMILES isomérico su línea `estereo:` con el origen.
- [ ] Cada asset enlazado existe; no hay assets huérfanos en `assets/<slug>/`.
- [ ] Cada figura redibujada lleva **todas** las etiquetas de texto del original, comprobado en el preview del SVG.
- [ ] Ningún dato inventado: lo dudoso está marcado con `(?)`, `[!warning]` o `[!todo]`.
- [ ] Ninguna palabra corregida, cambiada ni añadida: el contexto solo se ha usado para leer letras ambiguas, y ningún número se ha deducido por contexto.
- [ ] El resumen final para el usuario incluye las decisiones de estereoquímica.

## 9. Ordenar el vault

`scripts/ordenar_vault.py` coloca las notas de apuntes en `<vault>/<Asignatura>/`. Para cada nota, decide la carpeta por el `asignatura` del frontmatter y mueve también su carpeta `assets/<nombre>/`, así que los enlaces relativos siguen funcionando. No cambia el nombre del fichero ni edita ninguna nota, y nunca sobrescribe nada.

Úsalo cuando el usuario pida ordenar o colocar las notas, o cuando hayas convertido en una carpeta de trabajo (p. ej. `pruebas/salida/`) y haya que llevar las notas al vault:

```bash
uv run <skill>/scripts/ordenar_vault.py <vault> [--desde <carpeta-de-trabajo>]            # simulación
uv run <skill>/scripts/ordenar_vault.py <vault> [--desde <carpeta-de-trabajo>] --aplicar  # mover
```

**Primero simula siempre** y enséñale el plan al usuario. Solo pasa `--aplicar` cuando el usuario lo confirme. Los `CONFLICTO` (el destino ya existe, o la nota enlaza assets de otra carpeta) no se mueven: explícaselos. Los `AVISO` (asignatura escrita de varias formas, assets que no existen, assets huérfanos) son para que el usuario decida; el script no edita el frontmatter.

## Nota para Obsidian en modo oscuro

Los SVG son líneas negras sobre fondo transparente. Para que se vean en el tema oscuro, copia `obsidian/svg-modo-oscuro.css` (está en esta skill) a `<vault>/.obsidian/snippets/` y actívalo en *Ajustes → Apariencia → Fragmentos CSS*.
