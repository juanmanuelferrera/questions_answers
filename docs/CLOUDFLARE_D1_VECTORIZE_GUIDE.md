# Cloudflare D1 + Vectorize RAG Implementation

## Architecture Overview

```
Text Files → Workers Import Script → D1 (text) + Vectorize (vectors) → Query Worker → API
```

**Key Components:**
1. **D1 Database** - SQLite-compatible cloud database for storing full text responses
2. **Vectorize Index** - Vector search for embeddings
3. **Workers** - Serverless functions for import and query
4. **OpenAI API** - Generate embeddings (text-embedding-3-small)

---

## Prerequisites

### 1. Cloudflare Account Setup
```bash
# Install Wrangler CLI
npm install -g wrangler

# Login to Cloudflare
wrangler login
```

### 2. Create D1 Database
```bash
# Create database
wrangler d1 create philosophy-rag

# Copy the database ID from output, add to wrangler.toml
```

### 3. Create Vectorize Index
```bash
# Create vector index (1536 dimensions for text-embedding-3-small)
wrangler vectorize create philosophy-embeddings \
  --dimensions=1536 \
  --metric=cosine

# Copy the index name to wrangler.toml
```

### 4. Set OpenAI API Key
```bash
# Add OpenAI key as Worker secret
wrangler secret put OPENAI_API_KEY
# Paste your key when prompted
```

---

## Project Structure

```
philosophy-rag/
├── wrangler.toml              # Cloudflare configuration
├── schema.sql                 # D1 database schema
├── src/
│   ├── import-worker.ts       # Import script (run once per question)
│   ├── query-worker.ts        # Query API (public endpoint)
│   └── lib/
│       ├── parser.ts          # Parse .txt files
│       ├── chunker.ts         # Split into semantic chunks
│       └── embedder.ts        # Generate embeddings
└── data/
    └── question_*.txt         # Your existing files
```

---

## Configuration Files

### `wrangler.toml`

```toml
name = "philosophy-rag"
main = "src/query-worker.ts"
compatibility_date = "2024-11-01"

# D1 Database Binding
[[d1_databases]]
binding = "DB"
database_name = "philosophy-rag"
database_id = "YOUR_DATABASE_ID_HERE"  # From: wrangler d1 create

# Vectorize Index Binding
[[vectorize]]
binding = "VECTORIZE"
index_name = "philosophy-embeddings"

# OpenAI API Key (set via: wrangler secret put OPENAI_API_KEY)
[vars]
ENVIRONMENT = "production"

# Import Worker (separate)
[env.import]
name = "philosophy-rag-import"
main = "src/import-worker.ts"
```

### `schema.sql`

```sql
-- Questions table
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT UNIQUE NOT NULL,           -- "1.24"
    title TEXT NOT NULL,                   -- "Do abstract objects exist?"
    category TEXT                          -- "Metaphysics"
);

-- Traditions table
CREATE TABLE IF NOT EXISTS traditions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number INTEGER UNIQUE NOT NULL,        -- 1-185
    name TEXT NOT NULL,                    -- "Catholic (Thomistic)"
    category TEXT                          -- "Christianity"
);

-- Responses table (full text)
CREATE TABLE IF NOT EXISTS responses (
    id TEXT PRIMARY KEY,                   -- "1.24.001"
    question_id INTEGER NOT NULL,
    tradition_id INTEGER NOT NULL,
    tradition_name TEXT NOT NULL,
    question_number TEXT NOT NULL,
    question_title TEXT NOT NULL,

    -- Full text sections
    opening TEXT NOT NULL,
    historical_development TEXT,
    key_concepts TEXT,
    core_arguments TEXT,
    counter_arguments TEXT,
    textual_foundation TEXT,
    internal_variations TEXT,
    contemporary_applications TEXT,

    -- Metadata
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (question_id) REFERENCES questions(id),
    FOREIGN KEY (tradition_id) REFERENCES traditions(id),
    UNIQUE(question_id, tradition_id)
);

-- Index for fast lookups
CREATE INDEX idx_responses_question ON responses(question_id);
CREATE INDEX idx_responses_tradition ON responses(tradition_id);
CREATE INDEX idx_responses_composite ON responses(question_number, tradition_id);

-- Full-text search (optional, for keyword search)
CREATE VIRTUAL TABLE responses_fts USING fts5(
    id,
    opening,
    historical_development,
    key_concepts,
    core_arguments,
    content=responses
);
```

Apply schema:
```bash
wrangler d1 execute philosophy-rag --file=schema.sql
```

---

## Import Worker

### `src/import-worker.ts`

```typescript
export interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
}

interface ParsedResponse {
  id: string;
  questionNumber: string;
  questionTitle: string;
  traditionNumber: number;
  traditionName: string;
  sections: {
    opening: string;
    historicalDevelopment: string;
    keyConcepts: string;
    coreArguments: string;
    counterArguments: string;
    textualFoundation: string;
    internalVariations: string;
    contemporaryApplications: string;
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const { questionNumber, fileContent } = await request.json();

      // Parse file
      const responses = parseFile(fileContent);

      // Import to D1 and Vectorize
      const results = await Promise.all(
        responses.map(r => importResponse(r, env))
      );

      return new Response(JSON.stringify({
        success: true,
        imported: results.length,
        questionNumber
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};

function parseFile(content: string): ParsedResponse[] {
  const responses: ParsedResponse[] = [];

  // Split by response delimiter
  const responseBlocks = content.split(/\n\*\*\* (\d+\.\d+)\.(\d+) (.+?) Response\n/);

  for (let i = 1; i < responseBlocks.length; i += 4) {
    const questionNumber = responseBlocks[i];     // "1.24"
    const traditionNumber = parseInt(responseBlocks[i + 1]); // "001"
    const traditionName = responseBlocks[i + 2];  // "Catholic"
    const body = responseBlocks[i + 3];           // Full response text

    const sections = extractSections(body);

    responses.push({
      id: `${questionNumber}.${traditionNumber.toString().padStart(3, '0')}`,
      questionNumber,
      questionTitle: '', // Would come from questions mapping
      traditionNumber,
      traditionName,
      sections
    });
  }

  return responses;
}

function extractSections(body: string) {
  const sections = {
    opening: '',
    historicalDevelopment: '',
    keyConcepts: '',
    coreArguments: '',
    counterArguments: '',
    textualFoundation: '',
    internalVariations: '',
    contemporaryApplications: ''
  };

  // Extract opening (before first **)
  const openingMatch = body.match(/^(.*?)\n\n\*\*/s);
  sections.opening = openingMatch ? openingMatch[1].trim() : '';

  // Extract each section
  const hdMatch = body.match(/\*\*Historical Development\*\*:?\s*([^\*]+)/);
  sections.historicalDevelopment = hdMatch ? hdMatch[1].trim() : '';

  const kcMatch = body.match(/\*\*Key Concepts\*\*:?\s*([^\*]+)/);
  sections.keyConcepts = kcMatch ? kcMatch[1].trim() : '';

  const caMatch = body.match(/\*\*Core Arguments\*\*:?\s*([^\*]+)/);
  sections.coreArguments = caMatch ? caMatch[1].trim() : '';

  const coaMatch = body.match(/\*\*Counter-Arguments\*\*:?\s*([^\*]+)/);
  sections.counterArguments = coaMatch ? coaMatch[1].trim() : '';

  const tfMatch = body.match(/\*\*Textual Foundation\*\*:?\s*([^\*]+)/);
  sections.textualFoundation = tfMatch ? tfMatch[1].trim() : '';

  const ivMatch = body.match(/\*\*Internal Variations\*\*:?\s*([^\*]+)/);
  sections.internalVariations = ivMatch ? ivMatch[1].trim() : '';

  const caAppMatch = body.match(/\*\*Contemporary Applications\*\*:?\s*(.+)$/s);
  sections.contemporaryApplications = caAppMatch ? caAppMatch[1].trim() : '';

  return sections;
}

async function importResponse(response: ParsedResponse, env: Env) {
  // 1. Insert into D1
  await env.DB.prepare(`
    INSERT INTO responses (
      id, question_number, tradition_id, tradition_name, question_title,
      opening, historical_development, key_concepts, core_arguments,
      counter_arguments, textual_foundation, internal_variations,
      contemporary_applications, word_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    response.id,
    response.questionNumber,
    response.traditionNumber,
    response.traditionName,
    response.questionTitle,
    response.sections.opening,
    response.sections.historicalDevelopment,
    response.sections.keyConcepts,
    response.sections.coreArguments,
    response.sections.counterArguments,
    response.sections.textualFoundation,
    response.sections.internalVariations,
    response.sections.contemporaryApplications,
    calculateWordCount(response.sections)
  ).run();

  // 2. Create chunks
  const chunks = createChunks(response);

  // 3. Generate embeddings and insert into Vectorize
  for (const chunk of chunks) {
    const embedding = await generateEmbedding(chunk.text, env.OPENAI_API_KEY);

    await env.VECTORIZE.insert([{
      id: chunk.id,
      values: embedding,
      metadata: {
        responseId: response.id,
        questionNumber: response.questionNumber,
        traditionNumber: response.traditionNumber,
        traditionName: response.traditionName,
        sectionType: chunk.sectionType,
        chunkIndex: chunk.index
      }
    }]);
  }

  return response.id;
}

function createChunks(response: ParsedResponse) {
  const chunks = [];
  let index = 0;

  // Chunk 0: Full response overview
  chunks.push({
    id: `${response.id}-chunk-${index}`,
    text: response.sections.opening,
    sectionType: 'opening',
    index: index++
  });

  // Chunk 1: Historical Development
  if (response.sections.historicalDevelopment) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.historicalDevelopment,
      sectionType: 'historical_development',
      index: index++
    });
  }

  // Chunk 2: Key Concepts
  if (response.sections.keyConcepts) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.keyConcepts,
      sectionType: 'key_concepts',
      index: index++
    });
  }

  // Chunk 3: Core Arguments
  if (response.sections.coreArguments) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.coreArguments,
      sectionType: 'core_arguments',
      index: index++
    });
  }

  // Chunk 4: Counter Arguments
  if (response.sections.counterArguments) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.counterArguments,
      sectionType: 'counter_arguments',
      index: index++
    });
  }

  // Chunk 5: Textual Foundation
  if (response.sections.textualFoundation) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.textualFoundation,
      sectionType: 'textual_foundation',
      index: index++
    });
  }

  // Chunk 6: Internal Variations
  if (response.sections.internalVariations) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.internalVariations,
      sectionType: 'internal_variations',
      index: index++
    });
  }

  // Chunk 7: Contemporary Applications
  if (response.sections.contemporaryApplications) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.contemporaryApplications,
      sectionType: 'contemporary_applications',
      index: index++
    });
  }

  return chunks;
}

async function generateEmbedding(text: string, apiKey: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      input: text,
      model: 'text-embedding-3-small'
    })
  });

  const data = await response.json();
  return data.data[0].embedding;
}

function calculateWordCount(sections: any): number {
  const allText = Object.values(sections).join(' ');
  return allText.split(/\s+/).length;
}
```

---

## Query Worker

### `src/query-worker.ts`

```typescript
export interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const { query, topK = 20, questionFilter, traditionFilter } = await request.json();

      // 1. Generate query embedding
      const queryEmbedding = await generateEmbedding(query, env.OPENAI_API_KEY);

      // 2. Vector search in Vectorize
      const vectorResults = await env.VECTORIZE.query(queryEmbedding, {
        topK: topK * 2, // Get more results to allow filtering
        returnMetadata: true
      });

      // 3. Filter results if needed
      let filteredResults = vectorResults.matches;
      if (questionFilter) {
        filteredResults = filteredResults.filter(
          m => m.metadata.questionNumber === questionFilter
        );
      }
      if (traditionFilter) {
        filteredResults = filteredResults.filter(
          m => m.metadata.traditionNumber === traditionFilter
        );
      }

      // Take top K after filtering
      filteredResults = filteredResults.slice(0, topK);

      // 4. Get unique response IDs
      const responseIds = [...new Set(
        filteredResults.map(m => m.metadata.responseId)
      )];

      // 5. Fetch full text from D1
      const placeholders = responseIds.map(() => '?').join(',');
      const responses = await env.DB.prepare(`
        SELECT * FROM responses WHERE id IN (${placeholders})
      `).bind(...responseIds).all();

      // 6. Combine and format results
      const results = filteredResults.map(match => {
        const response = responses.results.find(
          r => r.id === match.metadata.responseId
        );

        return {
          score: match.score,
          responseId: match.metadata.responseId,
          questionNumber: match.metadata.questionNumber,
          traditionName: match.metadata.traditionName,
          sectionType: match.metadata.sectionType,
          response: response || null
        };
      });

      return new Response(JSON.stringify({
        query,
        results,
        count: results.length
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: error.message
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};

async function generateEmbedding(text: string, apiKey: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      input: text,
      model: 'text-embedding-3-small'
    })
  });

  const data = await response.json();
  return data.data[0].embedding;
}
```

---

## Deployment Steps

### 1. Initialize Project
```bash
mkdir philosophy-rag && cd philosophy-rag
npm init -y
npm install -D wrangler typescript @cloudflare/workers-types
npm install
```

### 2. Create Cloudflare Resources
```bash
# Create D1 database
wrangler d1 create philosophy-rag

# Create Vectorize index
wrangler vectorize create philosophy-embeddings --dimensions=1536 --metric=cosine

# Set OpenAI API key
wrangler secret put OPENAI_API_KEY
```

### 3. Apply Database Schema
```bash
wrangler d1 execute philosophy-rag --file=schema.sql
```

### 4. Deploy Workers
```bash
# Deploy query worker (main)
wrangler deploy

# Deploy import worker
wrangler deploy --env import
```

---

## Usage

### Import Data

```bash
# Read file content
FILE_CONTENT=$(cat question_1.24_traditions_1-15.txt)

# Import via Worker
curl -X POST https://philosophy-rag-import.YOUR-SUBDOMAIN.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "questionNumber": "1.24",
    "fileContent": "'"$FILE_CONTENT"'"
  }'
```

Or use a script:
```bash
#!/bin/bash
for file in question_1.*.txt; do
  echo "Importing $file..."
  curl -X POST https://philosophy-rag-import.YOUR-SUBDOMAIN.workers.dev \
    -H "Content-Type: application/json" \
    -d @- <<EOF
{
  "questionNumber": "$(echo $file | grep -oP '\d+\.\d+')",
  "fileContent": "$(cat $file | jq -Rs .)"
}
EOF
  sleep 2
done
```

### Query

```bash
curl -X POST https://philosophy-rag.YOUR-SUBDOMAIN.workers.dev \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do Buddhist traditions view abstract objects?",
    "topK": 20
  }'
```

Response:
```json
{
  "query": "How do Buddhist traditions view abstract objects?",
  "results": [
    {
      "score": 0.89,
      "responseId": "1.24.076",
      "questionNumber": "1.24",
      "traditionName": "Theravada Buddhism",
      "sectionType": "core_arguments",
      "response": {
        "id": "1.24.076",
        "opening": "Theravada Buddhism approaches abstract objects...",
        "historical_development": "...",
        "key_concepts": "...",
        ...
      }
    },
    ...
  ],
  "count": 20
}
```

---

## Cost Estimates

### D1
- **Free Tier:** 5GB storage, 5M reads/day, 100K writes/day
- **Your project:** ~150MB for 16 questions (well within free tier)
- **Full project:** ~1.6GB (still free)

### Vectorize
- **Beta:** Currently free during beta
- **Expected pricing:** TBD (likely usage-based)

### Workers
- **Free Tier:** 100K requests/day
- **Your usage:** Likely within free tier

### OpenAI Embeddings
- **16 questions:** ~$0.09 one-time
- **Full project:** ~$0.38 one-time

**Total Cost:** ~$0.09 now, ~$0.38 at completion (+ minimal Cloudflare costs)

---

## Next Steps

1. ✅ Create Cloudflare account
2. ✅ Install Wrangler CLI
3. ✅ Create D1 database and Vectorize index
4. ✅ Copy code above into project files
5. ✅ Deploy workers
6. ✅ Import first question (1.24)
7. ✅ Test queries
8. ✅ Iterate and improve
9. ✅ Import remaining questions incrementally

**Ready to build?** 🚀
