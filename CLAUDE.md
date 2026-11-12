# Web IMEDEA Sea Level — guía para Claude Code

Este repositorio es el código de la web pública <https://imedea-sealevel.github.io>.
Repo en GitHub: `IMEDEA-SeaLevel/IMEDEA-SeaLevel.github.io` (público, rama `main`).

## Qué puedes hacer y qué no

**Tu único cometido aquí es modificar esta web.** En concreto:

- SÍ: editar los ficheros de este repositorio, probar en local, hacer commit y `git push` a `main`
  de **este** repositorio.
- NO crear, borrar, renombrar, archivar ni cambiar la visibilidad o la configuración de ningún
  repositorio (ni de este, ni de ningún otro de la organización o del usuario).
- NO tocar el repositorio `IMEDEA-SeaLevel/MAROR` ni ningún otro repositorio de código. MAROR es
  privado y debe seguir así. Si la pestaña Repositories sale vacía es lo esperado.
- NO cambiar ajustes de la organización, de GitHub Pages, secretos, miembros ni permisos.
- NO reescribir el historial (`push --force`, `rebase` de commits ya subidos, `reset --hard` sobre
  `main`).
- NO crear tokens ni cambiar credenciales. Si falta un permiso, para y díselo al usuario.
- NO escribir claves ni contraseñas en ningún fichero (el repo es público). La clave de OpenAlex
  está guardada como secreto `OPENALEX_API_KEY` del repo y no hay que tocarla.

Si el usuario pide algo de la lista de «NO», explícale que esta carpeta está pensada solo para
mantener la web y que eso debe hacerlo Ángel Amores (propietario de la organización).

## Cómo está hecha

Web estática generada con Python a partir de ficheros YAML. No usa Jekyll ni Node.

```
data/projects.yml                 proyectos (SE EDITA A MANO)
data/collaborators.yml            personas cuyos artículos se rastrean: nombre + ORCID (A MANO)
data/publications_overrides.yml   añadir / ocultar artículos por DOI (A MANO)
data/site.yml                     título, descripción, organización de GitHub (A MANO)
data/publications.yml             GENERADO — no editar
data/repositories.yml             GENERADO — no editar
scripts/update_publications.py    busca los artículos (OpenAlex + Crossref + texto completo)
scripts/update_repositories.py    lista los repos PÚBLICOS de la organización
scripts/build.py                  genera la web en _site/
templates/                        plantillas HTML (Jinja2)
static/                           CSS, fuentes (autoalojadas), imágenes
.github/workflows/site.yml        Action: actualiza datos, construye y despliega
```

Páginas: **Projects** (portada, `index.html`, con un bloque *Impact* por proyecto: artículos,
citas, revistas), **Publications** y **Repositories**.

La Action se ejecuta en cada push a `main`, cada lunes y a demanda. Actualiza los datos, hace
commit de `data/` si cambian, construye y despliega. Por eso **antes de empezar a trabajar haz
siempre `git pull`**: puede haber commits automáticos nuevos.

## Tareas habituales

### Añadir un proyecto
1. Pide al usuario lo que falte; **no inventes datos**: acrónimo, título, referencia(s) de la ayuda
   tal como aparece en los agradecimientos de los artículos, financiador, inicio y fin, IP(s) y,
   si los hay, web, logo y descripción.
2. Añade un bloque en `data/projects.yml` (las instrucciones de cada campo están al principio del
   fichero). El estado (Upcoming / Ongoing / Completed) se calcula solo con las fechas.
3. El logo, si lo hay, va en `static/img/` (cuadrado, unos 330 px, que pese poco).
4. Ejecuta las herramientas y construye (ver «Probar en local»). Revisa con `--verbose` qué
   artículos se han asignado al proyecto y enséñaselos al usuario.

Cuidado con las referencias:
- Una referencia «paraguas» compartida por muchos proyectos arrastra artículos ajenos. Ejemplo:
  el código 690462 es de todo ERA4CS, por eso INSeaPTION **no** lo usa.
- `search_terms` (búsqueda en el texto completo) solo con palabras exclusivas del proyecto
  (p. ej. «INSeaPTION» sí; «MOCCA» no, es demasiado genérica).
- En proyectos coordinados se usa la referencia del subproyecto propio (MOCCA: solo `…-C31`).

### Añadir una persona
Nombre + ORCID en `data/collaborators.yml`. No es una página de miembros: solo sirve para rastrear
sus artículos y resaltar su nombre en negrita.

### Corregir la lista de artículos
`data/publications_overrides.yml`: `include` (DOI + id de proyecto) para los que falten, `exclude`
(DOI) para los que sobren. Nunca edites `data/publications.yml` a mano: se sobrescribe.

### Cambios de diseño
`templates/` y `static/style.css`. Comprueba siempre escritorio, móvil estrecho (360 px) y modo
oscuro.

## Probar en local y publicar

```bash
git pull
pip install -r requirements.txt            # solo la primera vez
python scripts/update_repositories.py
python scripts/update_publications.py --verbose
python scripts/build.py
python -m http.server -d _site 8791         # http://localhost:8791 (si el puerto está ocupado, usa otro)
```

1. Enseña al usuario el resultado en local (o un resumen claro de lo que cambia) **antes** de subir.
2. Con su visto bueno: commit con un mensaje claro en inglés y `git push` a `main`.
3. Comprueba que la Action termina bien (`gh run list --limit 1`, `gh run watch <id>`) y que el
   cambio se ve en <https://imedea-sealevel.github.io>.

`_site/` no se sube (está en `.gitignore`).

## Normas de contenido y estilo (decididas por Ángel Amores)

- La web está en **inglés**.
- **No es la web de un grupo de investigación** (es una parte de un grupo). No usar «group»,
  «team», «lab» ni textos de presentación. No añadir páginas About, People, Gallery ni News.
- La portada es Projects, con título «Projects» y nada más encima.
- No mostrar indicadores de acceso abierto (*open access*).
- Diseño propio. No copiar estilos ni código de la web de IMEDEA-POP-LAB ni de otras webs.
- Las fuentes están autoalojadas a propósito (privacidad): no cargar fuentes ni scripts de
  terceros (Google Fonts, CDNs, analíticas).
- Mantener la accesibilidad: contraste suficiente, foco visible, jerarquía de títulos.
- El icono (`static/img/logo.svg`) y los recuadros con iniciales de los proyectos sin logo son
  provisionales.

## Estado actual (noviembre de 2026)

| Proyecto   | Referencia(s)                      | Periodo             | IP                         |
|------------|------------------------------------|---------------------|----------------------------|
| SeaLine    | PID2025-171905OB-I00               | sep 2026 – ago 2029 | Ángel Amores, Marta Marcos |
| DRICOEX    | CNS2022-135532                     | 2022 – 2025         | Ángel Amores               |
| DETECT     | PID2021-124085OB-I00               | 2022 – 2025         | Marta Marcos               |
| MOCCA      | RTI2018-093941-B-C31               | 2019 – 2021         | Marta Marcos               |
| INSeaPTION | PCIN-2017-038, ANR-17-ERA4-0002    | 2017 – 2021         | Marta Marcos               |

Colaboradores rastreados: Ángel Amores, Marta Marcos, Francisco M. Calafat.

Pendiente (solo si el usuario lo pide y aporta el material): logos y descripciones de DRICOEX,
DETECT, MOCCA e INSeaPTION; logos oficiales de los financiadores (MICIU/AEI y «Cofinanciado por la
Unión Europea») en el pie; logo definitivo.

## Limitaciones conocidas

- La búsqueda de artículos depende de los metadatos de financiación y del texto completo que
  indexa OpenAlex. Puede faltar algún artículo: se añade con `publications_overrides.yml`.
- Las citas son las de OpenAlex (suelen ser algo menores que las de Google Scholar).
- GitHub desactiva las Actions programadas tras 60 días sin actividad en el repo; se reactivan
  desde la pestaña Actions.
