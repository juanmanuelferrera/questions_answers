# Preguntas Correctas - App Web de Consulta Filosofica

Aplicacion que toma una pregunta filosofica y genera respuestas desde 185 tradiciones del mundo usando Cloudflare Workers AI, con una sintesis final.

## Arquitectura

- **Backend**: Cloudflare Worker (`worker.js`) con Workers AI (modelo `@cf/meta/llama-3.1-8b-instruct`, gratuito)
- **Frontend**: HTML/CSS/JS vanilla (`public/index.html`)
- **Cache**: Cloudflare D1 (SQLite)
- **Estrategia de batching**: 19 grupos de ~10 tradiciones, procesados en 4 oleadas de 5 llamadas concurrentes

## Requisitos previos

1. Cuenta de Cloudflare (gratuita)
2. [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) instalado:
   ```bash
   npm install -g wrangler
   ```
3. Autenticacion:
   ```bash
   wrangler login
   ```

## Despliegue paso a paso

### 1. Crear la base de datos D1

```bash
wrangler d1 create preguntas-db
```

Copia el `database_id` que te devuelve y reemplaza `YOUR_D1_DATABASE_ID` en `wrangler.toml`.

### 2. Crear las tablas

```bash
wrangler d1 execute preguntas-db --file=schema.sql
```

### 3. Desarrollo local

```bash
wrangler dev
```

Esto abre la app en `http://localhost:8787`.

### 4. Desplegar a produccion

```bash
wrangler deploy
```

Esto despliega el Worker con el frontend integrado (servido desde `public/`).

## Endpoints de la API

| Endpoint | Metodo | Descripcion |
|---|---|---|
| `/api/traditions` | GET | Lista las 185 tradiciones agrupadas por familia |
| `/api/ask` | POST | Genera respuestas (respuesta completa al final) |
| `/api/ask-stream` | POST | Genera respuestas con progreso via SSE |

### Ejemplo de uso de la API

```bash
curl -X POST https://tu-worker.workers.dev/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Cual es el sentido del sufrimiento?"}'
```

## Estructura de archivos

```
02_app_web_consulta/
  worker.js        # Backend (Cloudflare Worker)
  wrangler.toml    # Configuracion de Wrangler
  schema.sql       # Schema de D1
  public/
    index.html     # Frontend (SPA)
  README.md        # Este archivo
```

## Limites del tier gratuito

- Workers AI: ~10,000 tokens/dia en tier gratuito
- D1: 5M filas leidas/dia, 100K escritas/dia
- Workers: 100K requests/dia

Con 185 tradiciones (19 llamadas de batch + 1 de sintesis = 20 llamadas por pregunta), cada pregunta consume ~20 invocaciones de AI. El cache en D1 evita repetir preguntas ya respondidas.

## Notas tecnicas

- Las respuestas se cachean en D1 usando un hash SHA-256 de la pregunta normalizada
- El endpoint streaming usa Server-Sent Events (SSE) para reportar progreso
- Si una llamada de AI falla o devuelve JSON invalido, se genera un placeholder para esas tradiciones
- La UI agrupa las tradiciones en 10 familias con acordeones expandibles
