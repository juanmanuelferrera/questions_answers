# Philosophy RAG System

Complete RAG (Retrieval-Augmented Generation) implementation for the comparative philosophy corpus.

## 📁 Project Structure

```
.
├── streamlit_app.py              # Local Streamlit frontend (with copy buttons)
├── rag-frontend.html             # Alternative HTML frontend
├── wrangler.toml                 # Cloudflare Workers configuration
├── schema.sql                    # D1 database schema
├── tsconfig.json                 # TypeScript configuration
├── package.json                  # Node.js dependencies
├── upload-responses.js           # Helper script for uploading files
├── DEPLOYMENT.md                 # Step-by-step deployment guide
├── CLOUDFLARE_D1_VECTORIZE_GUIDE.md  # Complete technical guide
└── src/
    ├── import-worker.ts          # Worker for uploading responses
    └── query-worker.ts           # Worker for RAG queries
```

## 🚀 Quick Start

### Option 1: Test Locally (Streamlit)

Already set up! Just run:

```bash
streamlit run streamlit_app.py
```

Features:
- ✅ Copy buttons for answers and sources
- ✅ Adjustable retrieval parameters
- ✅ GPT-4o synthesis
- ✅ OpenAI embeddings (text-embedding-3-small)

### Option 2: Deploy to Cloudflare (Production)

Follow the detailed guide in `DEPLOYMENT.md`:

1. Install dependencies: `npm install`
2. Login to Cloudflare: `npx wrangler login`
3. Create D1 database and Vectorize index
4. Deploy Workers
5. Upload responses using `upload-responses.js`

## 📊 Current Status

- ✅ **370 responses restructured** (8-section format, semantic chunking ready)
- ✅ **Questions 1.19, 1.24, 1.25** complete
- ✅ **Questions 1.2-1.9** restructured
- ✅ **Local RAG working** (Streamlit with SQLite)
- ⏳ **Cloudflare deployment ready** (needs setup)

## 🎯 Next Steps

### Immediate Actions

1. **Test copy buttons** in Streamlit app
2. **Decide priority**:
   - Continue writing questions (1.26+)
   - Deploy Cloudflare RAG prototype

### If Deploying RAG

```bash
# Install and setup
npm install
npx wrangler login

# Create resources
npx wrangler d1 create philosophy-db
npx wrangler vectorize create philosophy-vectors --dimensions=1536 --metric=cosine

# Apply schema
npx wrangler d1 execute philosophy-db --file=./schema.sql

# Deploy
npm run deploy
npm run deploy-import

# Upload responses
node upload-responses.js <import-worker-url> "question_1.19_*.txt"
```

### If Continuing Writing

Use the 8-section format:

```
*** X.XX.NNN [Tradition Name] Response

[Opening paragraph]

**Historical Development**: [content]

**Key Concepts**: *term1*, *term2*, ...

**Core Arguments**: 1) [argument] 2) [argument] ...

**Counter-Arguments**: Against [position]: [response]

**Textual Foundation**: [sources]

**Internal Variations**: [variations]

**Contemporary Applications**: [applications]
```

## 💰 Cost Estimate

- **Embeddings**: $0.38 total for all 36,075 responses
- **D1 + Vectorize + Workers**: FREE (covers entire project)

## 📚 Additional Resources

- `CLOUDFLARE_D1_VECTORIZE_GUIDE.md` - Complete technical implementation guide
- `DEPLOYMENT.md` - Step-by-step deployment instructions
- `philosophical-traditions-writer.md` - Agent instructions for writing

## 🔧 Helper Scripts

### Upload Responses

```bash
node upload-responses.js <worker-url> <file-pattern>
```

Examples:
```bash
# Upload Question 1.19
node upload-responses.js https://your-import-worker.workers.dev "question_1.19_*.txt"

# Upload all questions
node upload-responses.js https://your-import-worker.workers.dev "question_*.txt"

# Upload specific range
node upload-responses.js https://your-import-worker.workers.dev "question_1.2[0-5]_*.txt"
```

### Query RAG

```bash
curl -X POST <query-worker-url> \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the nature of space and time?", "topK": 10}'
```

## 🎓 Incremental Workflow

The system supports incremental uploads:

1. Write new question responses
2. Upload immediately to test
3. Use RAG to inform future writing
4. Iterate and improve

No need to wait for all 36,075 responses!

## 📝 File Format

All response files should follow the 8-section structure with bold headers. The system automatically:
- Extracts question number and tradition name from headers
- Creates semantic chunks (7-8 per response)
- Generates embeddings for each chunk
- Stores in D1 + Vectorize for fast retrieval

Both `.txt` and `.org` formats work identically. File naming doesn't matter.
