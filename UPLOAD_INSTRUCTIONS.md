# Upload Remaining 52K Vectors

## Current Status
- ✅ Book filtering implemented and working
- ✅ 122,842 vectors uploaded (NOI, SSR, CC, and 19 other books tested)
- ⏳ 52,419 vectors remaining across 12 files

## Authentication Issue
Wrangler OAuth requires interactive browser session. Since I'm running in a non-interactive environment, you need to run the upload commands directly in your terminal.

## Option 1: Automated Batch Upload (Recommended)

Open a **new terminal** and run:

```bash
cd /Users/jaganat/.emacs.d/git_projects/questions_answers
./batch_upsert.sh
```

This will:
- Upload all 12 files sequentially
- Show progress for each file
- Stop on errors with clear messages
- Take approximately 15-25 minutes

## Option 2: Manual Upload Commands

If the batch script has issues, run each command manually:

```bash
cd /Users/jaganat/.emacs.d/git_projects/questions_answers

# File 1/12: KB (560 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=kb_for_upsert_part000.ndjson --batch-size=500

# File 2/12: SB 1-3 Part 1 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=sb_cantos_1_3_for_upsert_part000.ndjson --batch-size=500

# File 3/12: SB 1-3 Part 2 (4,724 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=sb_cantos_1_3_for_upsert_part001.ndjson --batch-size=500

# File 4/12: SB 4-10 Part 1 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=sb_cantos_4_10_for_upsert_part000.ndjson --batch-size=500

# File 5/12: SB 4-10 Part 2 (3,904 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=sb_cantos_4_10_for_upsert_part001.ndjson --batch-size=500

# File 6/12: Rechunked Part 1 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part000.ndjson --batch-size=500

# File 7/12: Rechunked Part 2 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part001.ndjson --batch-size=500

# File 8/12: Rechunked Part 3 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part002.ndjson --batch-size=500

# File 9/12: Rechunked Part 4 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part003.ndjson --batch-size=500

# File 10/12: Rechunked Part 5 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part004.ndjson --batch-size=500

# File 11/12: Rechunked Part 6 (5,000 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part005.ndjson --batch-size=500

# File 12/12: Rechunked Part 7 (3,231 vectors)
npx wrangler vectorize upsert philosophy-vectors --file=rechunked_for_upsert_part006.ndjson --batch-size=500
```

## After Upload Complete

1. **Wait for indexing**: 15-45 minutes for Vectorize to index all vectors
2. **Test book filters**: Query with different book codes (BG, SB1-10, KB)
3. **Verify counts**: Run `npx wrangler vectorize info philosophy-vectors`

Expected final vector count: **~175,261 vectors**

## Troubleshooting

If you get authentication errors:
```bash
npx wrangler login
```
Then re-run the upload commands.

If you get rate limiting errors, increase the delay between batches in `batch_upsert.sh` (change `sleep 2` to `sleep 5`).
