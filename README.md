# Preguntas correctas — grandes preguntas, diversas respuestas

Corpus de filosofía comparada: preguntas filosóficas, cada una respondida desde un gran número de tradiciones (católica, sufí, budista, vedānta, etc.; la app web habla de 185 tradiciones). Sobre ese corpus hay un libro en curso en español («Las preguntas correctas»), una app web de consulta en Cloudflare y un sistema RAG sobre el corpus y la Vedabase.

Es un clon del repositorio `questions_answers`, más avanzado que la carpeta `~/git_projects/questions_answers` (tiene `consolidado/` y los últimos commits).

## Estructura

- `tradiciones/` — respuestas por tradición en `.org` y `.txt` (338 ficheros).
- `consolidado/` — una pregunta por fichero (`1.1.org` … `1.25.org`); `_cobertura.json` cuenta las respuestas de cada una.
- `question_*.txt`, `responses_*.org` — tandas de preguntas y respuestas en la raíz.
- `data.json` + `database.html` — base de datos navegable en HTML; `parse_data.py` genera el JSON desde org e `inject_data.py` lo inyecta en el HTML.
- `merge_long_answers.py`, `scan_long_answers.py`, `check_len.py` — utilidades para respuestas largas.
- `libro/` — el libro: `LIBRO_COMPLETO.org`, `LIBRO_MAESTRO.org/.tex/.pdf`, `BOOK_STRUCTURE.org`, personajes y notas.
- `proyectos/` — siete ideas de producto (`01_serie_libros_tematicos` … `07_rag_filosofico`), cada una con su `README.org`; `02_app_web_consulta` es la única con código.
- `vedabase/` — Workers de Cloudflare para el RAG (`src/*.ts`, `wrangler*.toml`, `public/`) y exportaciones de libros, cartas y conferencias.
- `scripts/` — 144 scripts de parseo, embeddings y subida a D1/Vectorize.
- `docs/` — notas de estado y guías del RAG (`PROJECT_DIRECTIVES.md`, `README_RAG.md`, `SETUP.md`…).
- `logs/` — registros de las subidas de embeddings.
- `project_possibilities.org` — lista de usos posibles del corpus.
- `.env.template` — variables que piden los scripts (OpenAI, Anthropic, Cloudflare).

## Uso

App web de consulta (`proyectos/02_app_web_consulta`, Worker `preguntas-correctas`, D1 `preguntas-db`, ruta `academia.vedicvault.org/*`):

```bash
cd proyectos/02_app_web_consulta
wrangler dev        # local en http://localhost:8787
wrangler deploy
```

RAG (`vedabase/`, Worker `philosophy-rag`):

```bash
cd vedabase
npm run dev
npm run deploy
npm run deploy-import   # Worker de importación aparte
```

Base de datos HTML: `python3 parse_data.py` y `python3 inject_data.py` (orden y argumentos por confirmar).

## Estado

- Feb-2026: correcciones de estilo en el libro (leísmo, diálogos, prefijos «Escena:»/«Diálogo:»).
- 28-mar-2026: limpieza del proyecto.
- 10-oct-2026: commits WIP; se deja de versionar la salida de máquina.
- 11-oct-2026: último commit, «Trabajo sin comitear (23 ficheros)», que añade `consolidado/`.

## Repositorio

`https://github.com/juanmanuelferrera/questions_answers.git` (remoto `origin`, compartido con `questions_answers/`).
