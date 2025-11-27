# Vedabase RAG Upload Guide

Complete guide for uploading Vedabase data to production (Cloudflare D1 + Vectorize).

## Prerequisites

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Copy the template and add your API keys:

```bash
cp .env.template .env
```

Edit `.env` and add:

1. **OPENAI_API_KEY** - Get from https://platform.openai.com/api-keys
2. **CLOUDFLARE_ACCOUNT_ID** - Get from https://dash.cloudflare.com/ (right side of overview)
3. **CLOUDFLARE_API_TOKEN** - Create at https://dash.cloudflare.com/profile/api-tokens
   - Required permissions: **D1:Edit**, **Vectorize:Edit**

Your `.env` should look like:
```env
OPENAI_API_KEY=sk-proj-xxxxx
CLOUDFLARE_ACCOUNT_ID=abc123def456
CLOUDFLARE_API_TOKEN=xyz789token
```

### 3. Verify Setup

Run the test script to ensure everything is configured:

```bash
python3 test_vedabase_setup.py
```

You should see:
```
✓ Local Database ................. PASS
✓ Environment Variables .......... PASS
✓ OpenAI Connection .............. PASS
✓ Wrangler CLI ................... PASS
```

---

## Upload Process

### Step 1: Upload Data to Remote D1

This uploads all 8,481 verses and 19,823 chunks to Cloudflare D1.

```bash
python3 upload_vedabase_to_remote.py
```

**What it does:**
- Reads verses and chunks from local D1
- Generates SQL INSERT statements in batches of 500 verses
- Uploads each batch to remote D1 via `wrangler d1 execute`
- Tracks progress in `vedabase_upload_progress.json`
- Can be resumed if interrupted

**Time:** ~10-15 minutes
**Cost:** $0 (D1 is free tier)

**Output:**
```
Batch 1/17: Processing verse IDs 1 to 500 (500 verses)
  Chunks in batch: 1,150
  Uploading to remote D1...
  ✓ Success
  Progress: 500/8,481 verses (5.9%)
```

### Step 2: Generate and Upload Embeddings

This generates embeddings for all chunks and uploads to Vectorize.

```bash
python3 generate_vedabase_embeddings.py
```

**What it does:**
- Reads all 19,823 chunks from local D1
- Generates embeddings in batches of 100 using OpenAI
- Uploads embeddings to Cloudflare Vectorize
- Tracks progress in `vedabase_embedding_progress.json`
- Can be resumed if interrupted

**Time:** ~1-2 hours (due to OpenAI rate limits)
**Cost:** ~$0.20 (OpenAI embeddings)

**Output:**
```
Batch 1: Processing chunk IDs 1 to 100 (100 chunks)
  Generating embeddings for 100 chunks...
  Uploading to Vectorize...
  ✓ Successfully uploaded 100 vectors
  Progress: 100/19,823 (0.5%)
```

---

## Progress Tracking

Both scripts save progress to JSON files and can be resumed:

- `vedabase_upload_progress.json` - Data upload progress
- `vedabase_embedding_progress.json` - Embedding generation progress

If interrupted (Ctrl+C or error), simply run the script again to resume from where it left off.

---

## Verification

### Check Remote D1

```bash
# Count verses
npx wrangler d1 execute philosophy-db --remote --command "SELECT COUNT(*) FROM vedabase_verses"

# Count chunks
npx wrangler d1 execute philosophy-db --remote --command "SELECT COUNT(*) FROM vedabase_chunks"

# Sample verse
npx wrangler d1 execute philosophy-db --remote --command "SELECT * FROM vedabase_verses LIMIT 1"
```

Expected output:
- Verses: 8,481
- Chunks: 19,823

### Test Vectorize Search

After embeddings are uploaded, test semantic search:

```bash
python3 query_rag.py
```

Try queries like:
- "What is karma according to Bhagavad Gita?"
- "Explain the concept of surrender"
- "Krishna's appearance in Vrindavan"

---

## Troubleshooting

### Error: "OPENAI_API_KEY not set"

**Solution:** Make sure you have a `.env` file with your API key:
```bash
cp .env.template .env
# Edit .env and add your keys
```

### Error: "Database not found"

**Solution:** The local D1 database is missing. Make sure you've run the import script first:
```bash
python3 import_vedabase_to_d1_fixed.py
```

### Error: "wrangler d1 execute failed"

**Solution:**
1. Make sure you're logged in: `npx wrangler login`
2. Check database name: `npx wrangler d1 list`
3. Verify database ID in `wrangler.toml`

### Error: "Rate limit exceeded" (OpenAI)

**Solution:** The script automatically handles rate limits with 1-second delays. If you still hit limits:
1. Reduce `BATCH_SIZE` in `generate_vedabase_embeddings.py` (from 100 to 50)
2. Wait a few minutes and resume

### Upload interrupted

**Solution:** Both scripts support resuming. Just run them again:
```bash
# Resume data upload
python3 upload_vedabase_to_remote.py

# Resume embedding generation
python3 generate_vedabase_embeddings.py
```

The scripts will skip already-processed data and continue from where they left off.

---

## Cost Breakdown

| Component | Quantity | Cost |
|-----------|----------|------|
| D1 Database | 8,481 verses | $0 (free tier) |
| D1 Storage | ~20 MB | $0 (free tier) |
| Vectorize Vectors | 19,823 | $0 (free tier) |
| Vectorize Storage | ~300 MB | $0 (free tier) |
| OpenAI Embeddings | 19,823 chunks | ~$0.20 |
| **Total** | | **~$0.20** |

---

## Timeline

| Step | Time | Progress |
|------|------|----------|
| Setup & Testing | 5 min | ✅ Complete |
| Upload to D1 | 10-15 min | ⏳ Pending |
| Generate Embeddings | 1-2 hours | ⏳ Pending |
| Test Queries | 5 min | ⏳ Pending |
| **Total** | **~2 hours** | |

---

## Next Steps After Upload

Once embeddings are uploaded:

1. **Update Query Worker** - Add Vedabase search to `src/query-worker.ts`
2. **Update Frontend** - Add Vedabase tab to `rag-frontend.html`
3. **Test Queries** - Verify semantic search works across all texts
4. **Document Results** - Update `VEDABASE_RAG_STATUS.md` with completion status

---

## Files Created During Upload

- `vedabase_sql_batches/batch_001.sql` - SQL batch files (auto-created)
- `vedabase_upload_progress.json` - Upload progress tracking
- `vedabase_embedding_progress.json` - Embedding progress tracking

These can be deleted after successful upload.

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review the progress JSON files for details
3. Check Cloudflare dashboard for D1 and Vectorize status
4. Review OpenAI usage dashboard for API limits

---

**Status:** Ready to upload
**Last Updated:** 2025-11-25
