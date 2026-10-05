---
name: apuntes-a-md
description: Convierte apuntes y ejercicios escritos a mano y escaneados (PDF o imagen) en notas Markdown para Obsidian, con fórmulas en LaTeX, estructuras químicas como SMILES + SVG (RDKit), diagramas redibujados en TikZ/chemfig y compilados a SVG, y recortes del original para lo que no se puede redibujar. Usa esta skill cuando el usuario pase un escaneo de apuntes (química, bioquímica, biología, física...) y pida pasarlo a Markdown, a Obsidian, a su vault o "a limpio". Nunca inventa: lo dudoso se marca de forma visible.
---

# Apuntes a Markdown

Conviertes un escaneo de apuntes a mano en **una nota `.md` por tema + su carpeta de assets**, lista para Obsidian, con una **estética didáctica acordada** que mejora la forma sin tocar el fondo. Lo que importa, por este orden:

1. **No inventar.** Un dato inventado (sobre todo estereoquímica) es peor que un hueco marcado. Ante la duda, se marca (sección 5).
2. **Fidelidad al original.** Transcribes, no redactas: no resumes, no reordenas, no "mejoras" el texto, no corriges al autor. Para *leer* la letra a mano sí te ayudas del contexto (sección 5a).
3. **La estética nunca toca el contenido.** Se aplica en una segunda pasada y se **comprueba con un script** que las palabras son exactamente las mismas (sección 8).
4. **Poco retoque.** La nota debe quedar lista con menos de 5 minutos de revisión humana por página.

Los scripts están en `scripts/` de esta skill. Lánzalos con la ruta de la skill delante (Python con `uv run`, que instala solo sus dependencias; el `.sh` con `bash`).

**Lo que necesitas de tu entorno**, seas el agente que seas (Claude Code, Gemini CLI, Codex…):
- **Ver imágenes y PDF**: toda la skill se apoya en mirar el escaneo, las cuadrículas y los previews.
- **Ejecutar comandos de shell**: para los scripts.
- **Escribir ficheros**: para la nota, los `.tex` y los assets.

Si te falta alguna de las tres, díselo al usuario antes de empezar en vez de improvisar.

## 1. Antes de empezar

Necesitas saber, y si no lo sabes **pregunta antes de escribir nada**:

- La ruta del **escaneo** y qué páginas son de **qué tema** (un PDF puede traer varios temas).
- La ruta del **vault** (o de la carpeta de salida).
- **Asignatura** y **número y título del tema**, si no se leen en la hoja. Si el escaneo es un cuaderno y el título del tema está en una página anterior del mismo PDF, puedes tomarlo de ahí, pero dilo en el `[!warning]` inicial.
- **Si la nota del tema ya existe** (el tema crece: sección 2.1).

## 2. Una nota por tema: dónde va cada cosa

```
<vault>/Universidad/<carrera>/<curso>/<Asignatura>/<Asignatura> - Tema <N>.md
<vault>/Universidad/<carrera>/<curso>/<Asignatura>/assets/<slug>/<asset>

p. ej. Universidad/Química/2026-2027/Bioquímica/Bioquímica - Tema 1.md
       Universidad/Química/2026-2027/Bioquímica/assets/bioquimica-tema-1/mol-01.svg
```

- **Carrera:** `Química`, salvo que el usuario diga otra.
- **Curso:** `2026-2027`, salvo que el usuario diga otro. El curso empieza en septiembre. Si las fechas de la hoja caen en otro curso, **pregunta** antes de escribir y, si lo confirma, pon `curso: AAAA-AAAA` en el frontmatter.
- **La carpeta de la asignatura** se llama como el campo `asignatura`. Si ya existe con otras tildes o mayúsculas, reutilízala.
- **Si el usuario da una carpeta de salida** que no es el vault (p. ej. `pruebas/salida/`), escribe ahí `<Asignatura>/…` sin más. `ordenar_vault.py` (sección 10) la lleva luego a su sitio.

- **Nombre de la nota:** `<Asignatura> - Tema <N>.md`. Es único en todo el vault, así que los enlaces de Obsidian no se confunden con el Tema 1 de otra asignatura. El alias `Tema <N>` va en el frontmatter.
- **`slug`:** el nombre de la nota en kebab-case, sin tildes ni espacios (`bioquimica-tema-1`). Es la carpeta de assets.
- **Assets:** `<tipo>-<NN>[-<desc>].<ext>`, con **numeración continua en todo el tema** por tipo.
  - `tipo`: `mol` (`.svg` de RDKit), `fig` (`.tex` + `.svg`, mismo nombre base), `rec` (`.svg`, recorte vectorial del dibujo del autor) o `crop` (`.png`).
  - `NN`: dos dígitos, en orden de aparición.
  - `desc`: opcional, kebab-case, como mucho 3 palabras.
- **Enlaces a assets:** Markdown relativo, `![alt|ancho](assets/<slug>/mol-01-glucosa.svg)`. Nunca `![[...]]`.

### 2.1 Temas que crecen
Si la nota del tema **ya existe** y llegan páginas nuevas, **añade al final**. **Nunca reescribas lo ya convertido**: el usuario puede haberlo retocado a mano. Solo actualizas el índice, `fechas` y `fuente`, y la numeración de assets sigue donde se quedó. **Nunca sobrescribas una nota existente** de ninguna otra forma.

## 3. Frontmatter

```yaml
---
asignatura: Bioquímica
tema: 1
titulo: "Moléculas biológicas, el agua, interacciones débiles en medio acuoso"
fechas: [2026-09-16]
fuente: "bq-temas-1-4.pdf#p2-5"
aliases: [Tema 1]
---
```

- **`tema`:** el número. **`titulo`:** tal como está en la hoja, con mayúscula inicial.
- **`fechas`:** las fechas de sesión **escritas** en las páginas del tema, en orden y sin repetir.
  - Una página sin fecha hereda la **fecha inmediatamente anterior** del mismo cuaderno o PDF: retrocede página a página hasta encontrar una. Los apuntes se fechan al empezar la clase. Esto no lleva aviso.
  - Solo si no hay ninguna fecha antes, pon `fechas: []` y un `[!warning]` al principio de la nota.
  - No uses nunca la fecha de hoy.
- **`fuente`:** escaneo + rango de páginas (`#p2-5`). Si el tema viene de varios escaneos, usa una lista.
- **`curso`** *(opcional)*: solo si el usuario ha confirmado un curso distinto del 2026-2027 (sección 2).
- No añadas `tags`: son cosa de la v3 (enlazado del vault).

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

### Paso 2: transcripción fiel (primera pasada)

Escribe primero una **transcripción fiel y sin estética** en `<tmp>/<slug>.transcripcion.md`, **fuera del vault**. Será la referencia contra la que se comprueba la estética (paso 5).
- Con su frontmatter.
- Con una marca `%% pág. N %%` al empezar cada página.
- Elemento a elemento, en el orden del original, como dice la tabla de abajo.

| Elemento | Cómo |
|---|---|
| **Texto** | Markdown limpio. Los títulos y subtítulos de la hoja pasan a `##`/`###` (el `#` es el título del tema), las listas a listas, y lo subrayado, recuadrado, resaltado con fluorescente o escrito en otro color para destacar pasa a **negrita**. No uses `==resaltado==` para lo que el autor resaltó: está reservado para las dudas. Las abreviaturas y las comillas de "ídem" (`"`) se dejan tal como están escritas. **Sin negritas dentro de los títulos**: rompen los enlaces del índice. |
| **Fórmulas** | LaTeX: `$...$` en línea y `$$...$$` en bloque (en líneas propias). En la nota **no uses `\ce{}`**, porque Obsidian no carga mhchem: usa `\rightarrow`, `\rightleftharpoons`, `\xrightarrow{\text{enzima}}`… **Nunca un `_` o `^` fuera de LaTeX**: se ve tal cual ("pK_R"). Usa `p$K_R$`, o los caracteres Unicode si existen (H₂O, pK₁, Na⁺) |
| **Estructura química** | SMILES → `smiles2svg.py` (sección 6). |
| **Diagrama o dibujo esquemático** (flechas, ciclos, rutas, perfil de energía, gráfica, montaje, cargas parciales δ⁺/δ⁻ sobre moléculas, micelas, bicapas, hélices, formas de lípidos…) | Redibújalo en TikZ/chemfig → `tikz2svg.sh` (sección 7). |
| **Dibujo figurativo** (material de laboratorio, hélices, plegamientos, células…), que en TikZ quedaría tosco | Si el escaneo es un **PDF de tableta** (sus trazos son vectores), usa el **recorte vectorial** del dibujo del autor: `recorte_vectorial.py` (sección 7.1). Es su dibujo exacto, nítido, y no inventa nada |
| **Diagrama ambiguo**, o dibujo de un escaneo en papel (imagen) | Recórtalo con `crop.py` y pon un callout `[!todo]` (sección 5c). |

**Cuándo redibujar y cuándo recortar:** por defecto, **redibuja**. El usuario prefiere el dibujo limpio al pantallazo, y un dibujo esquemático hecho a mano (aunque sea figurativo: micelas, vesículas, cabezas y colas de lípidos) se puede reproducir con TikZ. Recorta solo si el original es **ambiguo** (no sabes qué representa una flecha o una forma, o falta alguna etiqueta) o si es un dibujo realista que no se puede esquematizar sin perder información. Lo que se lee pero no se entiende va como recorte dentro del `[!warning]`, porque así el arreglo es inmediato.

### Paso 3: verificar cada asset
Usa `--preview` en ambos scripts y **compara el PNG de preview con el recorte del original**. Comprueba que los átomos, los enlaces, las flechas y las etiquetas coinciden. Si no coinciden y no sabes corregirlo, cambia ese elemento por recorte + `[!todo]`.

### Paso 4: estética (segunda pasada)
Copia la transcripción a la nota final, `<vault>/<Asignatura>/<Asignatura> - Tema <N>.md`, y aplícale **solo** lo de la sección 8. Ninguna palabra cambia.

### Paso 5: verificar que el contenido no ha cambiado
```bash
uv run <skill>/scripts/verificar_contenido.py <tmp>/<slug>.transcripcion.md "<vault>/<Asignatura>/<Asignatura> - Tema <N>.md"
```
Tiene que decir **`OK: mismo contenido`**. Si dice `DIFERENCIAS`, lista cada palabra que no cuadra. **Corrige la nota final**, nunca la transcripción, y vuelve a verificar. Una nota que no da OK **no se entrega**.

Si el tema crece (2.1), verifica solo la parte nueva: transcribe las páginas nuevas a su propio `.transcripcion.md` y compáralo con lo que has añadido.

### Paso 6: cierre
Relee la nota entera contra el escaneo. Después, dale al usuario un resumen corto:
- la ruta de la nota;
- el resultado de `verificar_contenido.py`;
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

### 7.1 Recorte vectorial (dibujos figurativos de tableta)

TikZ sirve para gráficas, química, cargas parciales y esquemas de flujo. **No lo uses para dibujos figurativos**: sale tosco. Si el PDF viene de una tableta, cada trazo del autor es un vector y se puede exportar tal cual:

```bash
uv run <skill>/scripts/recorte_vectorial.py <apuntes.pdf> --page N --box X0 Y0 X1 Y1 -o <vault>/<Asig>/assets/<slug>/rec-NN-desc.svg --paleta --preview
```

- **`--box`** se lee en la cuadrícula de `crop.py`, igual que un recorte normal. Por defecto entran solo los trazos **enteros** dentro de la caja, para no arrastrar texto vecino; con `--tocar` entran también los que la cruzan.
- **`--paleta`** pasa los colores del autor a la paleta (sus azules, rojos y verdes) y respeta los rellenos claros. Úsalo siempre, salvo que el color original importe para el contenido.
- Si la página no tiene trazos (es una imagen escaneada), el script falla y lo dice: entonces, `crop.py`.

**Las etiquetas van en TikZ, en tipografía, nunca con la letra del autor.** El flujo:
1. **Recorta el dibujo sin sus etiquetas.** Pon una caja `--excluir` ajustada a cada etiqueta escrita a mano. Repítela tantas veces como etiquetas haya, y deja fuera las puntas de flecha para que se conserven. Usa `--pdf` para tener también `rec-NN-desc.pdf`. Mira el preview: no debe quedar ni una letra suelta ni faltar una flecha.
2. **El script imprime el `marco`** del dibujo en fracciones de página. Pasa la posición de cada etiqueta (leída en la cuadrícula, en el punto donde empieza el texto o acaba la flecha) a coordenadas del dibujo: `u = (x − mx0)/(mx1 − mx0)`, `v = (my1 − y)/(my1 − my0)`.
3. **Compón la figura** `fig-NN-desc.tex` desde la plantilla:
   ```latex
   \begin{tikzpicture}
     \node[inner sep=0, anchor=south west] (img) at (0,0) {\includegraphics[width=4.2cm]{rec-NN-desc.pdf}};
     \begin{scope}[x={(img.south east)}, y={(img.north west)}]   % (0,0)–(1,1) = el dibujo
       \node[anotacion, anchor=west, font=\large] at (0.76,0.86) {Fase móvil o eluyent};
     \end{scope}
   \end{tikzpicture}
   ```
4. **Compila con `tikz2svg.sh`.** Al detectar `\includegraphics` usa `pdftocairo`, porque `dvisvgm` deja el dibujo incrustado en blanco. En la nota se enlaza el `fig-NN-desc.svg`; el `rec-NN-desc.svg/.pdf` se queda al lado como fuente.

Las etiquetas se copian **tal cual están escritas** (p. ej. "eluyent"), como cualquier texto de la hoja. Tipo de asset del recorte: **`rec-NN-desc`**. La figura final va como cualquier otra, sin `[!todo]`.

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
- **Flechas curvas de mecanismo o de resonancia:** `\chemmove` con átomos y enlaces nombrados (`@{n}`). `tikz2svg.sh` compila dos veces cuando lo detecta, porque con una sola pasada las flechas salen descolocadas. Mantén las flechas dentro del dibujo: lo que sobresale del recuadro se corta.
- **Nombres de variables en `\foreach`:** no uses nombres de comandos de TikZ (`\fill`, `\draw`, `\node`…): se rompen sin dar error.
- **Colores:** respeta los del original con la paleta (`\color{apRojo}` para estructuras en rojo, `anotacion`/`apAzul` para lo azul). No pongas `color=` en `every picture`: pisaría los `\color` de chemfig. El CSS de modo oscuro los mantiene reconocibles.
- **Dibujos repetitivos** (micelas, bicapas, vesículas): define una macro para la unidad (cabeza + colas) y colócala con `\foreach` en círculo o en fila. Ojo con la orientación: en micelas y en la capa externa de las vesículas, las cabezas van **fuera** y las colas **dentro**.

## 8. Estética (segunda pasada)

**Principio: se mejora la forma, nunca el fondo.** Si a la nota final le quitas el formato y las etiquetas fijas, tienen que quedar **exactamente las mismas palabras, en el mismo orden**, que en la transcripción. `verificar_contenido.py` lo comprueba (paso 5).

### 8.1 Estructura de la nota

```markdown
# Tema 1: Moléculas biológicas, el agua, interacciones débiles en medio acuoso

> [!abstract]- Índice
> - [[#Biomoléculas]]
> - [[#Importancia del carbono]]

%% pág. 2 %%
## Biomoléculas
…
%% pág. 4 %%
> [!sesion] 16/IX/2026
## Propiedades térmicas del H₂O
```

- **`#`:** el título del tema, tal como está en la hoja.
- **Índice plegable (`-`)** al principio, con un enlace a cada `##` del tema, en orden. Los textos de los enlaces deben coincidir **exactamente** con los títulos.
- **`%% pág. N %%`** al empezar cada página: es un comentario invisible en modo lectura y sirve para saber de dónde sale cada trozo.
- **`> [!sesion] <fecha>`** solo donde la hoja **trae una fecha escrita**, copiada tal cual (`16/IX/2026`).
- Las secciones que cruzan de página siguen sin corte visible.

### 8.2 ✅ Lo que SÍ se puede hacer

| # | Mejora | Cuándo |
|---|---|---|
| B1 | **Jerarquía de títulos** coherente y MAYÚSCULAS de la hoja → mayúscula inicial | Siempre; las siglas (ATP, DNA) se quedan en mayúsculas |
| B2 | **Índice plegable** | Siempre (8.1) |
| B3 | `> [!definicion] Definición` | La frase **define** el término del título de la sección, o el término antes de ":" |
| B4 | `> [!importante] Importante` | El autor escribe **una frase entera en rojo** o la remata con "!!" |
| B5 | **Término en negrita** | Patrón "Término: explicación" (`**Cisteína**: …`) |
| B6 | `> [!formula] Fórmula` | **Solo una ecuación suelta y destacada, de una línea** (una ley, una definición matemática). **Desarrollos de varias líneas, pasos de un ejercicio o ecuaciones encadenadas → bloque `$$…$$` normal, sin callout**, alineado con `\begin{aligned}` si son varias líneas. Ante la duda, sin callout |
| B7 | **Lista paralela → tabla** | Cada elemento tiene la misma estructura (columna A → columna B). Se conserva el orden de lectura (por filas) |
| B8 | **Figuras** con ancho uniforme y **pie en cursiva** justo debajo. Anchos de referencia, tomados de los retoques del usuario: `\|160` grupos y fragmentos, `\|260`–`\|300` moléculas, `\|400`–`\|450` esquemas pequeños, `\|560`–`\|700` gráficas y diagramas anchos. **Dos figuras pequeñas relacionadas van en la misma línea**, una al lado de la otra (p. ej. dos vistas de la misma molécula) | El pie lleva **solo palabras de la hoja** (las etiquetas escritas junto al dibujo). Sin palabras de la hoja, no hay pie |
| B9 | `> [!ficha]- Ficha` plegable con las líneas `smiles:` y `estereo:` | Debajo de cada molécula |
| B10 | Paleta: azul = estructura, rojo = importante, verde = definición, gris = metadatos | La pone el CSS (`obsidian/apuntes-estetica.css`); la misma que en las figuras |

**Etiquetas fijas.** Son las **únicas palabras que la estética puede añadir**: *Índice, Definición, Importante, Fórmula, Ficha*, y la fecha de *sesión* copiada de la hoja. Escríbelas exactamente así, porque `verificar_contenido.py` solo ignora estas.

### 8.3 ❌ Lo que NUNCA se hace
- Cambiar, añadir o quitar palabras (salvo las etiquetas fijas), ni para "aclarar".
- Corregir ortografía, puntuación de contenido o erratas: se avisa, no se corrige.
- Reordenar contenido entre secciones, fusionar secciones o crear títulos que no están en la hoja.
- Resumir, añadir explicaciones, ejemplos, reglas mnemotécnicas o emojis.
- Expandir abreviaturas (`protes`, `A-B`, `Cys`).
- Quitar marcas de duda (`(?)`, `[!warning]`).
- Usar `==resaltado==` para algo que no sea una duda.
- Poner negritas dentro de los títulos.

## 9. Checklist final

- [ ] `verificar_contenido.py` da **OK** entre la transcripción y la nota final.
- [ ] Nombre `<Asignatura> - Tema <N>.md`; frontmatter con `asignatura`, `tema`, `titulo`, `fechas`, `fuente`, `aliases`.
- [ ] Índice con todos los `##`, marcas `%% pág. N %%` y `[!sesion]` solo donde hay fecha escrita.
- [ ] Ningún `_` ni `^` fuera de `$…$` (subíndices y superíndices siempre en LaTeX o en Unicode).
- [ ] Todo el contenido de la hoja está, en el mismo orden.
- [ ] Cada estructura tiene su `smiles:`, y cada SMILES isomérico su línea `estereo:` con el origen.
- [ ] Cada asset enlazado existe; no hay assets huérfanos en `assets/<slug>/`.
- [ ] Cada figura redibujada lleva **todas** las etiquetas de texto del original, comprobado en el preview del SVG.
- [ ] Ningún dato inventado: lo dudoso está marcado con `(?)`, `[!warning]` o `[!todo]`.
- [ ] Ninguna palabra corregida, cambiada ni añadida: el contexto solo se ha usado para leer letras ambiguas, y ningún número se ha deducido por contexto.
- [ ] El resumen final para el usuario incluye las decisiones de estereoquímica.

## 10. Ordenar el vault

`scripts/ordenar_vault.py` coloca las notas de apuntes en `Universidad/<carrera>/<curso>/<Asignatura>/` (sección 2).
- **Qué mueve:** cada nota junto con su carpeta `assets/<slug>/`, y también los MOC de asignatura (`tipo: moc`). Así los enlaces relativos siguen funcionando.
- **Qué no hace:** no cambia el nombre de ningún fichero, no edita ninguna nota y nunca sobrescribe nada. Las notas que ya están en su sitio no se tocan.

Úsalo cuando el usuario pida ordenar o colocar las notas, o cuando hayas convertido en una carpeta de trabajo y haya que llevar las notas al vault:

```bash
uv run <skill>/scripts/ordenar_vault.py <vault> [--desde <carpeta-de-trabajo>] [--excluir <carpeta>]            # simulación
uv run <skill>/scripts/ordenar_vault.py <vault> [--desde <carpeta-de-trabajo>] [--excluir <carpeta>] --aplicar  # mover
```

`--carrera` (por defecto `Química`) y `--curso` (por defecto `2026-2027`) cambian los valores por defecto. `--excluir` deja fuera carpetas del vault, con rutas relativas al vault.

**Primero simula siempre** y enséñale el plan al usuario. Solo pasa `--aplicar` cuando el usuario lo confirme.

**Los `CONFLICTO` no se mueven:** explícaselos al usuario. Son estos:
- el destino ya existe;
- la nota enlaza assets de otra carpeta;
- sus fechas son de otro curso. En ese caso, pregunta el curso y, con su OK, añade `curso:` al frontmatter (es metadato, no contenido).

**Los `AVISO` son para que el usuario decida:**
- la asignatura está escrita de varias formas;
- hay assets que no existen o assets huérfanos;
- un `![[x.svg]]` tiene un nombre repetido en el vault, y Obsidian podría enseñar el de otro tema.

## Fragmentos CSS para Obsidian

Copia los dos ficheros de `obsidian/` a `<vault>/.obsidian/snippets/` y actívalos en *Ajustes → Apariencia → Fragmentos CSS*:
- **`apuntes-estetica.css`**: los callouts propios (definición, importante, fórmula, ficha, sesión), los colores de títulos y los pies de figura. Sin él, los callouts propios se ven como notas grises genéricas: no se pierde nada, pero queda menos claro.
- **`svg-modo-oscuro.css`**: para que los SVG (líneas oscuras, fondo transparente) se vean en el tema oscuro.
