# Philosophy RAG API Documentation

**Base URL:** `https://philosophy-rag.joanmanelferrera-400.workers.dev`

**Last Updated:** 2025-11-25

---

## Overview

The Philosophy RAG API provides semantic search across two major corpora:

1. **Philosophy Traditions** - Responses to philosophical questions across 185 traditions
2. **Vedabase** - Sacred texts including Bhagavad Gita and Srimad Bhagavatam

The API uses vector embeddings and Cloudflare Vectorize for semantic similarity search.

---

## Authentication

No authentication required. API is publicly accessible with CORS enabled.

---

## Endpoints

### 1. Search (POST)

**Endpoint:** `POST /`

Perform semantic search across philosophy traditions and/or Vedabase texts.

**Request Body:**

```json
{
  "query": "What is karma?",
  "topK": 20,
  "source": "all",
  "questionFilter": "1.2",
  "traditionFilter": "Buddhism",
  "bookFilter": "bg"
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The search query text |
| `topK` | number | No | 20 | Maximum number of results to return |
| `source` | string | No | "all" | Which corpus to search: "philosophy", "vedabase", or "all" |
| `questionFilter` | string | No | - | Filter philosophy results by question number (e.g., "1.2") |
| `traditionFilter` | string | No | - | Filter philosophy results by tradition name (partial match) |
| `bookFilter` | string | No | - | Filter Vedabase results by book code (e.g., "bg", "sb1") |

**Response:**

```json
{
  "query": "What is karma?",
  "count": 15,
  "results": [
    {
      "score": 0.87,
      "source": "philosophy",
      "sectionType": "core_arguments",
      "chunkText": "Karma operates through intentional action...",
      "response": {
        "id": "resp_123",
        "tradition_name": "Buddhism - Theravada",
        "question_number": "1.19",
        "question_title": "What is karma?",
        "opening": "...",
        "core_arguments": "..."
      }
    },
    {
      "score": 0.85,
      "source": "vedabase",
      "sectionType": "verse_text",
      "chunkText": "Book: Bhagavad Gita\n\nSanskrit: karmaṇo hy api...",
      "vedabaseVerse": {
        "id": "456",
        "book_code": "bg",
        "book_name": "Bhagavad Gita",
        "chapter": "Chapter 3",
        "verse_number": "3.9",
        "sanskrit": "karmaṇo hy api boddhavyaṁ...",
        "synonyms": "karmaṇaḥ—of work...",
        "translation": "The intricacies of action are very hard to understand..."
      }
    }
  ]
}
```

**Result Types:**

**Philosophy Result:**
- `source`: "philosophy"
- `response`: Contains tradition_name, question info, and response sections
- `sectionType`: One of: "opening", "historical_development", "key_concepts", "core_arguments", "counter_arguments", "textual_foundation", "internal_variations", "contemporary_applications"

**Vedabase Result:**
- `source`: "vedabase"
- `vedabaseVerse`: Contains book, chapter, verse, translation, synonyms
- `sectionType`: Either "verse_text" or "purport_paragraph"

---

### 2. Get Traditions (GET)

**Endpoint:** `GET /traditions`

Returns a list of all available philosophical traditions.

**Response:**

```json
{
  "traditions": [
    "Advaita Vedanta",
    "Buddhism - Mahayana",
    "Buddhism - Theravada",
    "Buddhism - Tibetan",
    "Buddhism - Zen",
    "Catholic Christianity",
    "Confucianism",
    "Daoism",
    "Dvaita Vedanta",
    ...
  ]
}
```

---

### 3. Get Questions (GET)

**Endpoint:** `GET /questions`

Returns a list of all philosophical questions in the corpus.

**Response:**

```json
{
  "questions": [
    {
      "number": "1.2",
      "title": "What is the nature of existence?"
    },
    {
      "number": "1.19",
      "title": "What is karma?"
    },
    {
      "number": "1.24",
      "title": "What is meditation?"
    },
    ...
  ]
}
```

---

### 4. Get Vedabase Books (GET)

**Endpoint:** `GET /vedabase-books`

Returns a list of all Vedabase books available for search.

**Response:**

```json
{
  "books": [
    {
      "code": "bg",
      "name": "Bhagavad Gita"
    },
    {
      "code": "sb1",
      "name": "Srimad Bhagavatam Canto 1"
    },
    {
      "code": "sb2",
      "name": "Srimad Bhagavatam Canto 2"
    },
    {
      "code": "sb3",
      "name": "Srimad Bhagavatam Canto 3"
    },
    {
      "code": "kb",
      "name": "Krishna Book"
    },
    {
      "code": "cc1",
      "name": "Caitanya Caritamrita Adi-lila"
    },
    {
      "code": "cc2",
      "name": "Caitanya Caritamrita Madhya-lila"
    },
    {
      "code": "cc3",
      "name": "Caitanya Caritamrita Antya-lila"
    }
  ]
}
```

---

## Example Queries

### Search Only Philosophy Traditions

```bash
curl -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the nature of consciousness?",
    "source": "philosophy",
    "topK": 10
  }'
```

### Search Only Vedabase

```bash
curl -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is devotional service?",
    "source": "vedabase",
    "topK": 15
  }'
```

### Search Bhagavad Gita Only

```bash
curl -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to control the mind?",
    "source": "vedabase",
    "bookFilter": "bg",
    "topK": 10
  }'
```

### Search Buddhist Traditions Only

```bash
curl -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is meditation?",
    "source": "philosophy",
    "traditionFilter": "Buddhism",
    "topK": 20
  }'
```

### Search All Sources

```bash
curl -X POST https://philosophy-rag.joanmanelferrera-400.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is karma?",
    "source": "all",
    "topK": 30
  }'
```

---

## JavaScript/TypeScript Examples

### Basic Search

```javascript
async function searchPhilosophy(query) {
  const response = await fetch('https://philosophy-rag.joanmanelferrera-400.workers.dev', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, topK: 20 })
  });

  return await response.json();
}

// Usage
const results = await searchPhilosophy("What is enlightenment?");
console.log(`Found ${results.count} results`);
```

### Search with Filters

```javascript
async function searchVedabase(query, bookCode) {
  const response = await fetch('https://philosophy-rag.joanmanelferrera-400.workers.dev', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      source: 'vedabase',
      bookFilter: bookCode,
      topK: 15
    })
  });

  return await response.json();
}

// Usage
const bgResults = await searchVedabase("What is surrender?", "bg");
```

### Get Available Resources

```javascript
async function getResources() {
  const [traditions, questions, books] = await Promise.all([
    fetch('https://philosophy-rag.joanmanelferrera-400.workers.dev/traditions').then(r => r.json()),
    fetch('https://philosophy-rag.joanmanelferrera-400.workers.dev/questions').then(r => r.json()),
    fetch('https://philosophy-rag.joanmanelferrera-400.workers.dev/vedabase-books').then(r => r.json())
  ]);

  return { traditions, questions, books };
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "error": "Query required"
}
```

### 405 Method Not Allowed

```
Method not allowed
```

### 500 Internal Server Error

```json
{
  "error": "OpenAI API error: rate limit exceeded"
}
```

---

## Rate Limits

No explicit rate limits are enforced by the API itself. However, the underlying OpenAI embedding API has rate limits that may affect performance under heavy load.

---

## CORS

CORS is enabled for all origins (`Access-Control-Allow-Origin: *`).

Supported methods: GET, POST, OPTIONS

---

## Performance

- **Average query latency:** 300-800ms
  - 100-200ms for embedding generation
  - 100-300ms for vector search
  - 100-300ms for database queries
- **Concurrent requests:** Supports high concurrency via Cloudflare Workers
- **Caching:** No caching implemented (all queries are fresh)

---

## Data Statistics

### Philosophy Corpus
- **Traditions:** 185
- **Questions:** ~25
- **Total responses:** ~4,625 (185 × 25)
- **Searchable chunks:** ~50,000+

### Vedabase Corpus
- **Books:** 8 (Bhagavad Gita, SB Cantos 1-3, Krishna Book, CC Adi/Madhya/Antya)
- **Verses:** 8,481
- **Searchable chunks:** 19,823 (verses + purport paragraphs)

---

## Versioning

**Current Version:** 1.0.0
**API Stability:** Beta (interfaces may change)

---

## Support

For issues or questions:
- Check `VEDABASE_RAG_STATUS.md` for implementation status
- Review `VEDABASE_UPLOAD_GUIDE.md` for upload instructions
- See `README_RAG.md` for general RAG system documentation

---

**Deployed:** 2025-11-25
**Worker URL:** https://philosophy-rag.joanmanelferrera-400.workers.dev
