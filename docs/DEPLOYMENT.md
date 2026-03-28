# Philosophy RAG Deployment Guide

Quick start guide for deploying your RAG system to Cloudflare D1 + Vectorize.

## Prerequisites

- Cloudflare account (free tier is sufficient)
- Node.js and npm installed
- OpenAI API key

## 1. Install Dependencies

```bash
npm install
```

This installs Wrangler CLI and TypeScript dependencies.

## 2. Login to Cloudflare

```bash
npx wrangler login
```

This opens a browser to authenticate with your Cloudflare account.

## 3. Create D1 Database

```bash
npx wrangler d1 create philosophy-db
```

Copy the `database_id` from the output and paste it into `wrangler.toml` at line 11.

## 4. Create Database Schema

```bash
npx wrangler d1 execute philosophy-db --file=./schema.sql
```

This creates the tables for questions, traditions, responses, and embeddings.

## 5. Create Vectorize Index

```bash
npx wrangler vectorize create philosophy-vectors \
  --dimensions=1536 \
  --metric=cosine
```

This creates the vector index for embeddings (1536 dimensions for OpenAI's text-embedding-3-small).

## 6. Add OpenAI API Key

Edit `wrangler.toml` and add your OpenAI API key:

```toml
[vars]
OPENAI_API_KEY = "sk-..."
```

## 7. Deploy Query Worker

```bash
npm run deploy
```

This deploys the main query worker. Copy the URL from the output (e.g., `https://philosophy-rag.your-subdomain.workers.dev`).

## 8. Deploy Import Worker

```bash
npm run deploy-import
```

This deploys the import worker for uploading responses. Copy this URL as well.

## 9. Import Your First Responses

Create a simple script to test importing (save as `test-import.js`):

```javascript
const fs = require('fs');

// Read a response file
const responseText = fs.readFileSync('question_1.19_traditions_181-185.txt', 'utf-8');

// Split into individual responses
const responses = responseText.split(/\*\*\* \d+\.\d+\.\d+/).slice(1).map((text, i) => {
  const match = responseText.match(new RegExp(`\\*\\*\\* (\\d+\\.\\d+\\.${i + 181})`, 'g'));
  return match ? match[0] + text : null;
}).filter(Boolean);

// Upload to Cloudflare
fetch('https://philosophy-rag-import.your-subdomain.workers.dev', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ responses })
})
.then(r => r.json())
.then(console.log)
.catch(console.error);
```

Replace the Worker URL with your actual import worker URL, then run:

```bash
node test-import.js
```

## 10. Test Query Worker

```bash
curl -X POST https://philosophy-rag.your-subdomain.workers.dev \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the nature of space and time?", "topK": 5}'
```

You should get back JSON with relevant responses!

## 11. Update Frontend

Update the `WORKER_URL` in `rag-frontend.html` (line 324):

```javascript
const WORKER_URL = 'https://philosophy-rag.your-subdomain.workers.dev';
```

Open `rag-frontend.html` in your browser and test queries.

## Incremental Uploads

The import worker supports incremental uploads. You can:

1. Upload one file at a time
2. Upload multiple files in batches
3. Re-upload files (uses `INSERT OR REPLACE`)
4. Continue writing new questions and upload them as you finish

Example batch upload script:

```javascript
const fs = require('fs');
const glob = require('glob');

// Find all response files
const files = glob.sync('question_*.txt');

for (const file of files) {
  const text = fs.readFileSync(file, 'utf-8');
  const responses = parseResponsesFromFile(text);

  await fetch(IMPORT_WORKER_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ responses })
  });

  console.log(`Uploaded ${file}`);
}
```

## Cost Estimates

- **Embeddings**: ~$0.38 for all 36,075 responses (296,600 chunks × $0.0013/1k tokens)
- **D1**: Free tier covers 5M reads/day, 100k writes/day (more than enough)
- **Vectorize**: Free tier covers 30M queries/month
- **Workers**: Free tier covers 100k requests/day

**Total**: ~$0.38 one-time cost for embeddings, everything else free!

## Monitoring

View your deployment stats:

```bash
npx wrangler tail philosophy-rag
```

This shows real-time logs from your Workers.

## Next Steps

1. Test with a few files first
2. Verify queries work correctly
3. Upload remaining responses incrementally
4. Continue writing new questions and upload as you finish
5. Use the RAG system to help generate future responses!
