# Solutions for Large Chunks with Buried Information

## Problem
"Lomasa Muni" appears at the end of a 1,750-character purport paragraph about Arjuna's journey. In semantic search, important names buried in long chunks may not rank highly.

## Solutions (from easiest to most comprehensive)

### Option 1: Wait for Indexing ⏱️
**Effort:** None
**Time:** 5-15 minutes
**Action:** The embeddings were just uploaded. Wait 15-20 minutes for Vectorize to fully index them.

**Why it might work:** Once indexed, the embedding might actually capture "Lomasa" well enough.

---

### Option 2: Increase topK Parameter 🎯
**Effort:** Very Low (1 line change)
**Time:** Immediate

**Current:** Frontend requests top 20 chunks
**Change:** Request top 30-40 chunks when filtering by book

**How:** In `public/index.html` line 595:
```javascript
// OLD:
const searchTopK = bookFilter ? Math.min(topK * 3, 50) : topK;

// NEW:
const searchTopK = bookFilter ? Math.min(topK * 5, 100) : topK;
```

**Pros:** Simple, might catch Lomasa in expanded results
**Cons:** More chunks sent to synthesis (higher cost, slower)

---

### Option 3: Add Hybrid Search (Keyword + Semantic) 🔍
**Effort:** Medium
**Time:** 1-2 hours

**Add keyword search fallback** when semantic search doesn't find exact matches:

1. Try semantic search first
2. If query contains proper names (capitalized words), also do SQL LIKE search
3. Combine results

**Implementation:**
```typescript
// In query-worker.ts
if (query.includes('Muni') || /[A-Z][a-z]+/.test(query)) {
  // Also do keyword search
  const keywordResults = await env.DB.prepare(`
    SELECT * FROM vedabase_chunks
    WHERE content LIKE ?
    LIMIT 5
  `).bind(`%${query}%`).all();

  // Merge with semantic results
}
```

**Pros:** Catches exact name matches
**Cons:** Requires code changes + deployment

---

### Option 4: Re-chunk Large Purports ✂️
**Effort:** Medium-High
**Time:** 2-3 hours (re-chunk + re-embed + re-upload)

**What:** Split purport paragraphs >600 chars into smaller segments

**Process:**
```bash
# 1. Re-chunk locally
python3 rechunk_large_purports.py

# 2. Generate new embeddings
python3 generate_rechunked_embeddings.py

# 3. Upload to production
python3 upload_rechunked_data.py
python3 upload_rechunked_embeddings.py
```

**Result:** Chunk 2985 (1750 chars) → 3 chunks (~600 chars each)
- Chunk A: Arjuna's penances and weapons
- Chunk B: Urvaśī story
- Chunk C: **Meeting Lomasa Muni** ← This would rank high!

**Pros:** Best long-term solution, improves all searches
**Cons:** Need to regenerate ~15K embeddings (~$0.15), re-upload everything

---

### Option 5: Named Entity Enhancement 🏷️
**Effort:** High
**Time:** 3-4 hours

**Extract named entities and create separate mini-chunks:**

For each purport:
1. Extract names (regex: `[A-Z][a-z]+ (?:Muni|Rishi|Maharaja|etc)`)
2. Create micro-chunks: "Lomasa Muni - mentioned in SB 1.12.21"
3. Add as separate searchable entries

**Pros:** Guarantees name findability
**Cons:** Most complex, requires NER

---

## Recommended Approach

### Immediate (Do Now):
1. **Wait 10 more minutes** for Vectorize indexing to complete
2. **Test with a more specific query:** "Arjuna met Lomasa" or "Lomasa ascetic"

### Short-term (If still not working):
**Option 2:** Increase topK to 40-50 (5-minute fix)

### Long-term (If you want perfect results):
**Option 4:** Re-chunk large purports

I've created the re-chunking script if you want to use it. It's already written and ready to run!

---

## Testing After Each Solution

Try these queries to verify:
- ✅ "Who is Lomasa Muni?"
- ✅ "Arjuna met Lomasa"
- ✅ "ascetic Lomasa"
- ✅ "Lomasa protection Yudhiṣṭhira"

If **any** of these work, the system is functioning correctly - it's just a ranking issue.

---

## Current Status

- ✅ Data: All in production D1
- ✅ Embeddings: All uploaded to Vectorize
- ⏳ Indexing: Should be complete in 5-10 minutes
- 💡 Optimization: Can improve with re-chunking if needed

**My recommendation:** Wait 10 minutes, then try "Arjuna met Lomasa" as the query. If that works, the system is fine - just need to tune chunk sizes for better ranking.
