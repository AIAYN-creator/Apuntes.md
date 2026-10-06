# Guía de uso, paso a paso

Esta guía es para ti si nunca has usado una terminal, GitHub ni nada parecido. No hace falta saber programar: solo **copiar y pegar** unos comandos y seguir los pasos en orden. Calcula unos **30–45 minutos** la primera vez, la mayoría esperando descargas. Después, convertir apuntes es pedirlo con una frase.

> **Qué vas a conseguir:** de un PDF de tus apuntes a mano (por ejemplo, exportado de GoodNotes, Notability o un escáner) a notas de [Obsidian](https://obsidian.md/) limpias, con fórmulas, moléculas y dibujos, ordenadas por asignatura y enlazadas entre sí. **Sin inventar nada**: lo que no se lee bien queda marcado para que lo revises.

**Índice**
1. [Lo que necesitas](#1-lo-que-necesitas)
2. [Instalar los programas](#2-instalar-los-programas)
3. [Descargar Apuntes.md](#3-descargar-apuntesmd)
4. [Instalar la skill](#4-instalar-la-skill)
5. [Preparar Obsidian](#5-preparar-obsidian)
6. [Convertir tus apuntes](#6-convertir-tus-apuntes)
7. [Ejercicios](#7-ejercicios)
8. [Enlazar los temas de una asignatura](#8-enlazar-los-temas-de-una-asignatura)
9. [Si algo falla](#9-si-algo-falla)
10. [Actualizar](#10-actualizar)

---

## 1. Lo que necesitas

| Qué | Para qué | ¿Gratis? |
|---|---|---|
| Un PC con **Windows 10 u 11** | Todo funciona en Windows | — |
| **[Claude](https://claude.ai/download)** (app de escritorio, pestaña **Code**) o Claude Code en la terminal | Es quien lee tus apuntes y escribe las notas | Necesita una suscripción de Claude con acceso a Claude Code |
| **[Obsidian](https://obsidian.md/)** | Para leer las notas | Sí |
| Tus apuntes en **PDF** (o fotos/escaneos) | — | — |

> También funciona con otros agentes compatibles con *Agent Skills* (Gemini CLI, Codex…), pero esta guía usa Claude, que es con el que está probado.

## 2. Instalar los programas

Necesitas tres programas "de fondo". No los vas a abrir nunca: los usa Claude por debajo.

**Abre PowerShell:** pulsa la tecla **Windows**, escribe `PowerShell` y pulsa **Intro**. Se abre una ventana con texto. Ahí **pegas** cada comando (clic derecho pega) y pulsas **Intro**.

**1. uv**, que ejecuta las herramientas de Python (y descarga Python solo):
```powershell
winget install astral-sh.uv
```

**2. MiKTeX**, que dibuja las figuras y las fórmulas:
```powershell
winget install MiKTeX.MiKTeX
```

**3. Git**, que trae "Git Bash", necesario para una de las herramientas:
```powershell
winget install Git.Git
```

> Si te pregunta *"¿Está de acuerdo con todos los términos de los acuerdos de origen?"*, escribe `Y` y pulsa Intro. Si Windows pide permiso para instalar, acepta.

**Un ajuste en MiKTeX (importante):** abre **MiKTeX Console** desde el menú Inicio → **Settings** → en *"Install missing packages on-the-fly"* elige **Always**. Así, cuando haga falta un paquete, se instala solo en vez de preguntar.

**Comprueba que todo está:** **cierra PowerShell y ábrelo otra vez** (si no, no "ve" lo recién instalado) y pega:
```powershell
uv --version; pdflatex --version; git --version
```
Si salen tres versiones (números), perfecto. Si alguno dice *"no se reconoce"*, mira [Si algo falla](#9-si-algo-falla).

> **Edge** (viene con Windows) también se usa, para comprobar que las figuras se ven bien. No tienes que hacer nada.

## 3. Descargar Apuntes.md

1. Entra en **https://github.com/AIAYN-creator/Apuntes.md**.
2. Pulsa el botón verde **`<> Code`** → **Download ZIP**.
3. Descomprime el ZIP (clic derecho → *Extraer todo…*) en **Documentos**. Sale una carpeta `Apuntes.md-main`: **renómbrala a `Apuntes.md`** para que coincida con los comandos de esta guía. Debe quedar `Documentos\Apuntes.md\instalar.ps1`.

> ⚠️ **No muevas ni borres esa carpeta después de instalar.** La skill queda "enlazada" a ella: si la mueves, hay que volver a instalar (paso 4).

*Si sabes usar git:* `git clone https://github.com/AIAYN-creator/Apuntes.md.git` en lugar del ZIP. Así actualizar es más fácil (paso 10).

## 4. Instalar la skill

En PowerShell, pega estas dos líneas (la primera entra en la carpeta; cámbiala si descomprimiste en otro sitio):
```powershell
cd "$HOME\Documents\Apuntes.md"
powershell -ExecutionPolicy Bypass -File .\instalar.ps1
```
Debe decir algo como:
```
[claude] apuntes-a-md instalada: ...
[claude] enlazar-apuntes instalada: ...
```

> `-ExecutionPolicy Bypass` deja ejecutar **solo este** script esta vez; no cambia la seguridad de tu PC. Si al descomprimir la carpeta quedó dentro de otra (`Apuntes.md-main\Apuntes.md-main`), entra en la de dentro: es la que contiene `instalar.ps1`.

Con eso Claude ya conoce dos *skills* nuevas: **`apuntes-a-md`** (convertir) y **`enlazar-apuntes`** (conectar temas).

## 5. Preparar Obsidian

1. **Crea tu vault:** abre Obsidian → *Crear nuevo vault* → ponle nombre (p. ej. `Apuntes`) y elige dónde guardarlo (p. ej. `Documentos\Apuntes`). Un *vault* es simplemente una carpeta con tus notas.
2. **Activa el estilo de las notas:**
   - En Obsidian: *Ajustes* (⚙️ abajo a la izquierda) → *Apariencia* → baja hasta *Fragmentos CSS* → pulsa el icono de **carpeta** 📁. Se abre la carpeta `snippets` de tu vault.
   - Copia ahí los dos ficheros de `Apuntes.md\skills\apuntes-a-md\obsidian\`: **`apuntes-estetica.css`** y **`svg-modo-oscuro.css`**.
   - Vuelve a Obsidian, pulsa el icono de **recargar** 🔄 y **activa los dos** interruptores.
3. **Ajustes → Archivos y enlaces:** activa *Actualizar enlaces internos automáticamente* y pon *Formato de los nuevos enlaces* en **Ruta relativa al archivo**.

No hace falta ningún plugin.

## 6. Convertir tus apuntes

1. **Exporta tus apuntes a PDF** (desde la app de la tableta, o escanea las hojas). Guárdalo donde quieras, por ejemplo `Documentos\Escaneos\bioquimica.pdf`.
2. **Abre Claude** → pestaña **Code** → elige como carpeta de trabajo **tu vault** (`Documentos\Apuntes`).
3. **Pídeselo con una frase**, diciendo qué páginas son de qué tema. Por ejemplo:

   > Pasa a Markdown los apuntes de Bioquímica de `C:\Users\TuNombre\Documents\Escaneos\bioquimica.pdf`: las páginas 2–5 son el Tema 1 y las 6–9 el Tema 2.

   También puedes escribir `/apuntes-a-md` delante.
4. **Acepta los permisos** que te pida (leer el PDF, ejecutar las herramientas, escribir las notas). Tarda unos minutos por tema.
5. **Al terminar te da un resumen:**
   - dónde está cada nota: `Universidad/Química/2026-2027/Bioquímica/Bioquímica - Tema 1.md`;
   - si el texto se ha verificado palabra por palabra (tiene que decir **OK**);
   - cuántas **dudas** ha marcado: búscalas en la nota como `(?)` o en los avisos amarillos. Ahí lleva un recorte de tu hoja original para que lo arregles en segundos;
   - si hay moléculas, de dónde ha sacado la estereoquímica.

> **La carrera y el curso:** por defecto pone `Química` y el curso `2026-2027`. Si estudias otra cosa o es otro curso, díselo en la frase ("…de Física, curso 2025-2026").

**Si no le das algún dato**, te lo pregunta antes de escribir nada.

## 7. Ejercicios

Las hojas de ejercicios van en su propia nota, junto a los apuntes del tema: `Bioquímica - Ejercicios T1.md`.

> Pasa a Markdown los ejercicios del Tema 1 de Bioquímica: `C:\...\ejercicios-t1.pdf`.

- Cada ejercicio, con su número tal como está en la hoja.
- Tu resolución (si la escribiste) queda **plegada**: puedes intentarlo antes de desplegarla.
- **Nunca resuelve nada por su cuenta**: si en la hoja no hay solución, la nota tampoco la tiene. Así sabes que todo lo que pone salió de ti (o del profe).

## 8. Enlazar los temas de una asignatura

Cuando tengas varios temas de una asignatura:

> Enlaza los temas de Bioquímica.

- Busca los conceptos que aparecen en varios temas (por ejemplo *plegamiento* o *efecto hidrofóbico*) y enlaza su primera mención en cada sección con el tema donde se explican.
- Crea un **índice de la asignatura** (`Bioquímica.md`) con todos los temas, sus ejercicios y los conceptos que se repiten.
- **Antes de escribir te enseña la lista** de lo que va a enlazar; tú dices sí, quitas lo que sobre, o no.
- No cambia ni una palabra de tus notas (lo comprueba solo).

Puedes repetirlo cuando añadas temas nuevos: solo añade lo que falte.

## 9. Si algo falla

| Problema | Solución |
|---|---|
| *"uv / pdflatex / git no se reconoce como nombre de un cmdlet"* | Cierra PowerShell (y Claude) y vuelve a abrirlos. Si sigue, reinicia el PC: la instalación aún no ha llegado a la ruta del sistema |
| `winget` no se reconoce | Actualiza el *Instalador de aplicación* desde Microsoft Store, o descarga cada programa de su web: [uv](https://docs.astral.sh/uv/getting-started/installation/), [MiKTeX](https://miktex.org/download), [Git](https://git-scm.com/download/win) |
| Una ventana de MiKTeX pregunta si instalar un paquete | Dile que sí y pon *Always* (paso 2) para que no vuelva a preguntar |
| *"La ejecución de scripts está deshabilitada"* al instalar | Usa exactamente el comando del paso 4, con `-ExecutionPolicy Bypass` |
| *"No se encuentra la ruta"* al hacer `cd` | La carpeta tiene otro nombre (el ZIP la llama `Apuntes.md-main`). Abre la carpeta en el Explorador, haz clic en la barra de direcciones, copia la ruta y úsala: `cd "C:\…\Apuntes.md-main"` |
| Claude no parece conocer la skill | Comprueba que el paso 4 dijo "instalada" y **abre una conversación nueva** en Claude |
| Las figuras se ven negras en el modo oscuro de Obsidian | Activa el fragmento `svg-modo-oscuro.css` (paso 5) |
| Los cuadros de definición / importante salen grises | Activa el fragmento `apuntes-estetica.css` (paso 5) |
| He movido la carpeta de Apuntes.md | Vuelve a ejecutar `instalar.ps1` desde el sitio nuevo |
| Una palabra está mal leída | Corrígela a mano en Obsidian: es tu nota. Las dudosas ya vienen marcadas con `(?)` |

¿Otra cosa? Abre un *issue* en [GitHub](https://github.com/AIAYN-creator/Apuntes.md/issues) contando qué pediste y qué pasó.

## 10. Actualizar

- **Si descargaste el ZIP:** descarga el nuevo, **borra el contenido** de tu carpeta `Apuntes.md` y pon dentro el nuevo, **en la misma ruta**. No hace falta reinstalar.
- **Si usaste git:** en esa carpeta, `git pull`.

Tus notas viven en tu vault, no en esta carpeta: actualizar no las toca.
