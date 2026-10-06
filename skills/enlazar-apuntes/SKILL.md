---
name: enlazar-apuntes
description: Enlaza entre sí los temas de una asignatura en un vault de Obsidian ya convertido con apuntes-a-md. Añade enlaces internos a la sección donde se define cada concepto, tags mínimos y un índice (MOC) por asignatura con los conceptos transversales, sin cambiar ni una palabra de las notas. Usa esta skill cuando el usuario pida enlazar, conectar o relacionar sus apuntes o temas, ponerles tags o crear el índice de una asignatura.
---

# Enlazar apuntes

Conectas los temas de **una asignatura**:
- enlaces internos a la sección donde se define cada concepto;
- tags;
- un índice (MOC) por asignatura.

Lo que importa, por este orden:

1. **No cambiar ni una palabra.** Un enlace solo envuelve palabras que ya están: `plegamiento` → `[[Bioquímica - Tema 3#Plegamiento (folding)|plegamiento]]`. El script lo comprueba antes de escribir.
2. **Poco azul.** Solo la **primera mención de cada sección** y solo los conceptos que de verdad atraviesan temas.
3. **Nada sin el OK del usuario.** Primero un resumen; se escribe solo cuando lo apruebe.

El script está en `scripts/enlazar.py` de esta skill. Lánzalo con `uv run`, que instala solo sus dependencias.

## 1. Antes de empezar

Necesitas saber la **carpeta de la asignatura**, p. ej. `<vault>/Universidad/Química/2026-2027/Bioquímica/`. Si no te la dan, pregunta.

**Los enlaces son solo dentro de una asignatura.** Entre asignaturas los pone el usuario a mano. Si te pide enlazar dos asignaturas, díselo.

## 2. Flujo

### Paso 1: inventario
```bash
uv run <skill>/scripts/enlazar.py inventario <carpeta-asignatura>
```
Lista los temas y sus encabezados, que son los destinos posibles. **Lee las notas enteras**: tienes que entender de qué trata cada sección.

### Paso 2: elegir conceptos
**Candidatos:** conceptos que se **definen** en una sección de un tema y **aparecen** en otros temas. Comprueba dónde aparecen:
```bash
uv run <skill>/scripts/enlazar.py inventario <carpeta> --buscar "efecto hidrofóbico" "plegamiento" "pI"
```
Solo cuenta las menciones donde se podría enlazar.

**Reglas para elegir:**
- **El destino es la sección donde se define el concepto** (su `##`/`###`, o la sección que contiene su `[!definicion]`). Nunca una mención cualquiera.
- **Solo conceptos con sección propia.** Una palabra que aparece de pasada en dos temas no se enlaza: no hay dónde llevarla.
- **Si es ambiguo, no se enlaza.** Si una forma puede significar otra cosa en esta asignatura, déjala fuera o usa `"mayusculas": true` (p. ej. `pI`, `Cys`).
- **Merece la pena si aparece en al menos otro tema.** Un concepto que solo vive en su tema no aporta.
- **Las `formas` son tal como aparecen en el texto:** plurales, variantes (`enlaces de H`, `enlaces de hidrógeno`). No inventes formas que no estén en las notas.

### Paso 3: plan
Escribe el plan en un fichero temporal (no en el vault):
```json
{"conceptos": [
  {"concepto": "efecto hidrofóbico",
   "formas": ["efecto hidrofóbico", "efectos hidrofóbicos"],
   "destino": "Bioquímica - Tema 1#Interacciones por efecto hidrofóbico"},
  {"concepto": "pI", "formas": ["pI"], "destino": "Bioquímica - Tema 2#Punto isoelectrónico", "mayusculas": true}
]}
```
`destino` es `<nombre de la nota>#<encabezado exacto>`. El script falla si la nota o el encabezado no existen.

### Paso 4: simular y enseñar el resumen
```bash
uv run <skill>/scripts/enlazar.py aplicar <carpeta> --plan <plan.json>
```

**Qué muestra:**
- cada enlace, con su línea y sección;
- los tags que añade;
- el MOC completo;
- la comprobación de que el texto no cambia.

**Qué le enseñas al usuario:**
- cuántos enlaces hay por nota;
- la lista "concepto → destino";
- lo que te parezca dudoso.

**Espera su OK.**

### Paso 5: escribir
```bash
uv run <skill>/scripts/enlazar.py aplicar <carpeta> --plan <plan.json> --escribir
```

**Qué hace:**
- pone los enlaces y los tags;
- genera el MOC `<Asignatura>.md`.

Si la comprobación del texto falla, no escribe nada.

**Después,** si tienes las transcripciones fieles, pasa `verificar_contenido.py` de la skill `apuntes-a-md` sobre cada nota: lee `[[destino|texto]]` como `texto`, así que tiene que seguir dando OK.

## 3. Qué hace el script (para que lo expliques)

| Regla | Detalle |
|---|---|
| **Primera mención por sección** | Cada `##`/`###` es una sección. Si ya hay un enlace a ese destino en la sección, no añade otro |
| **Nunca enlaza en** | Títulos, avisos (`[!warning]`, `[!todo]`), índice, `[!sesion]`, `[!formula]`, fórmulas `$…$`, código, comentarios `%% %%`, imágenes, pies de figura, resaltados `==…==` (dudas) ni dentro de otro enlace |
| **Ni en la sección que define el concepto** | Sería un enlace a sí misma |
| **Tablas** | Dentro de una tabla escribe `[[destino\|texto]]`, para no romper la tabla |
| **Tags** | `apuntes`, `<asignatura>` y `<asignatura>/tema-N`, por ejemplo `[apuntes, bioquimica, bioquimica/tema-1]`. En las notas de ejercicios, `ejercicios` en lugar de `apuntes`. Respeta los que ya hubiera |
| **Ejercicios** | Las notas `<Asignatura> - Ejercicios T<N>.md` (`tipo: ejercicios`) se enlazan igual: sus conceptos llevan a la sección de los apuntes donde se definen. **Los destinos son siempre secciones de los apuntes**, nunca un ejercicio |
| **MOC** | `<Asignatura>.md` en la carpeta de la asignatura, con `tipo: moc`. Lleva la tabla de temas (título, fechas, páginas y sus **ejercicios**) y la de **conceptos transversales** (dónde se define y dónde aparece: `T2` son los apuntes del Tema 2 y `E2` sus ejercicios). Se regenera entero en cada pasada; si existe un `<Asignatura>.md` que no generó el script, no toca nada |
| **Repetible** | Una segunda pasada con el mismo plan no añade nada. Un plan con conceptos nuevos solo añade esos |

## 4. Cierre

**Dale al usuario:**
- el número de enlaces por nota;
- los conceptos que no se han podido enlazar en ningún sitio;
- la ruta del MOC;
- el resultado de `verificar_contenido.py`, si lo has pasado.

**Recuérdale** que el MOC se regenera: si quiere notas propias sobre la asignatura, que las ponga en otra nota.
