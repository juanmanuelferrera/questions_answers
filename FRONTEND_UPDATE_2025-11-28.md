# Frontend Update - November 28, 2025

## Issues Fixed

### 1. **Book Dropdown Not Loading All Books**
**Problem:** The dropdown only showed a subset of books because the frontend was calling the wrong endpoint.

**Fix:** Changed the API endpoint from `/books` to `/vedabase-books`:
```javascript
// Before
const response = await fetch(`${QUERY_WORKER}/books`);

// After
const response = await fetch(`${QUERY_WORKER}/vedabase-books`);
```

### 2. **Incorrect Book Count in Header**
**Problem:** The header showed outdated stats: "8,481 verses • Bhagavad Gita & Srimad Bhagavatam (Cantos 1-3)"

**Fix:** Updated to reflect all 36 books:
```html
<!-- Before -->
<div class="stats">8,481 verses • Bhagavad Gita & Srimad Bhagavatam (Cantos 1-3)</div>

<!-- After -->
<div class="stats">36 Books • ~35,811 Searchable Chunks • Bhagavad Gita, Srimad Bhagavatam, Caitanya Caritamrita & More</div>
```

### 3. **Wrong API Endpoint**
**Problem:** Frontend was pointing to old `vedabase-rag` worker instead of unified `philosophy-rag` worker.

**Fix:** Updated the worker URL:
```javascript
// Before
const QUERY_WORKER = 'https://vedabase-rag.joanmanelferrera-400.workers.dev';

// After
const QUERY_WORKER = 'https://philosophy-rag.joanmanelferrera-400.workers.dev';
```

### 4. **Missing Source Parameter**
**Problem:** Search wasn't explicitly filtering to Vedabase content.

**Fix:** Added `source: 'vedabase'` parameter:
```javascript
const searchBody = { query, topK, source: 'vedabase' };
```

### 5. **Response Format Handling**
**Problem:** Frontend wasn't correctly handling the Vedabase response format from the unified worker.

**Fix:** Updated to handle both old and new response formats:
```javascript
// Map results to handle both formats
const sources = searchData.results.map(r => ({
    verse: r.vedabaseVerse || r.verse,
    chunkType: r.sectionType || r.chunkType,
    chunkText: r.chunkText,
    score: r.score
}));

// Updated display function to extract correct fields
const verse = result.vedabaseVerse || result.verse || {};
const chunkType = result.sectionType || result.chunkType || 'text';
const bookName = verse.book_name || verse.book || 'Unknown Book';
```

---

## Deployment

**Site:** https://universalphilosophy.info/
**Deployment Date:** November 28, 2025
**Deployment ID:** https://0b6ee2b4.philosophy-rag.pages.dev

---

## Verification

### Books Now Available in Dropdown (36 total):

**Major Texts (8):**
1. Bhagavad Gita
2. Srimad Bhagavatam Canto 1
3. Srimad Bhagavatam Canto 2
4. Srimad Bhagavatam Canto 3
5. Krishna Book
6. Caitanya Caritamrita Adi-lila
7. Caitanya Caritamrita Madhya-lila
8. Caitanya Caritamrita Antya-lila

**Lectures (6):**
9-14. Lectures Part 1A, 1B, 1C, 2A, 2B, 2C

**Other Collection (1):**
15. Other Vedic Texts

**Individual Books (21):**
16. A Second Chance
17. Beyond Birth and Death
18. Easy Journey to Other Planets
19. Elevation to Krsna Consciousness
20. Krsna Consciousness The Topmost Yoga System
21. Krsna, the Reservoir of Pleasure
22. Life Comes from Life
23. Light of the Bhagavata
24. On the Way to Krsna
25. Perfect Questions, Perfect Answers
26. Raja-Vidya: The King of Knowledge
27. Sri Isopanisad
28. Teachings of Lord Caitanya
29. Teachings of Lord Kapila
30. Teachings of Queen Kunti
31. The Nectar of Devotion
32. The Nectar of Instruction
33. The Path of Perfection
34. The Perfection of Yoga
35. The Science of Self Realization
36. Transcendental Teachings of Prahlada Maharaja

---

## Testing

You can verify the fixes by:

1. **Visit:** https://universalphilosophy.info/
2. **Check header:** Should show "36 Books • ~35,811 Searchable Chunks"
3. **Open book dropdown:** Should show all 36 books
4. **Search test:** Try searching for "devotion" and filter by "The Nectar of Devotion"

---

## Related Files

- **Frontend:** `/public/index.html`
- **Backend Worker:** `src/query-worker.ts`
- **Deployment Project:** `philosophy-rag` (Cloudflare Pages)

---

**Status:** ✅ **COMPLETE** - All 36 books now visible and searchable
