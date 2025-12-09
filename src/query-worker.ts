/**
 * Philosophy RAG Query Worker
 *
 * Handles semantic search queries across the philosophy corpus
 * Returns relevant chunks with full response context
 */

interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
  EMBEDDING_CACHE: KVNamespace;
}

interface QueryRequest {
  query: string;
  topK?: number;
  questionFilter?: string;
  traditionFilter?: string;
  source?: 'philosophy' | 'vedabase' | 'all'; // Which corpus to search
  bookFilter?: string; // For Vedabase: 'bg', 'sb1', etc.
}

interface SearchResult {
  score: number;
  source: 'philosophy' | 'vedabase';
  sectionType: string;
  chunkText: string;
  response?: {
    id: string;
    tradition_name: string;
    question_number: string;
    question_title: string;
    opening: string;
    historical_development?: string;
    key_concepts?: string;
    core_arguments?: string;
    counter_arguments?: string;
    textual_foundation?: string;
    internal_variations?: string;
    contemporary_applications?: string;
  };
  vedabaseVerse?: {
    id: string;
    book_code: string;
    book_name: string;
    chapter: string;
    verse_number: string;
    sanskrit?: string;
    synonyms?: string;
    translation?: string;
  };
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type'
        }
      });
    }

    // GET /traditions - Return list of all traditions
    if (request.method === 'GET' && new URL(request.url).pathname === '/traditions') {
      try {
        const traditions = await env.DB.prepare(`
          SELECT DISTINCT t.name
          FROM traditions t
          INNER JOIN responses r ON t.id = r.tradition_id
          ORDER BY t.name
        `).all();

        return new Response(JSON.stringify({
          traditions: traditions.results?.map((t: any) => t.name) || []
        }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: String(error) }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }
    }

    // GET /questions - Return list of all questions
    if (request.method === 'GET' && new URL(request.url).pathname === '/questions') {
      try {
        const questions = await env.DB.prepare(`
          SELECT DISTINCT q.number, q.title
          FROM questions q
          INNER JOIN responses r ON q.id = r.question_id
          ORDER BY q.number
        `).all();

        return new Response(JSON.stringify({
          questions: questions.results?.map((q: any) => ({
            number: q.number,
            title: q.title
          })) || []
        }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: String(error) }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }
    }

    // GET /vedabase-books - Return list of Vedabase books with content
    if (request.method === 'GET' && new URL(request.url).pathname === '/vedabase-books') {
      try {
        const books = await env.DB.prepare(`
          SELECT DISTINCT b.code, b.name
          FROM vedabase_books b
          INNER JOIN vedabase_verses v ON b.id = v.book_id
          INNER JOIN vedabase_chunks c ON v.id = c.verse_id
          ORDER BY b.id
        `).all();

        return new Response(JSON.stringify({
          books: books.results?.map((b: any) => ({
            code: b.code,
            name: b.name
          })) || []
        }), {
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      } catch (error) {
        return new Response(JSON.stringify({ error: String(error) }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          }
        });
      }
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const body = await request.json() as QueryRequest;
      const {
        query,
        topK = 20,
        questionFilter,
        traditionFilter,
        source = 'all',
        bookFilter
      } = body;

      if (!query) {
        return new Response('Query required', { status: 400 });
      }

      // 1. Generate query embedding (with caching)
      const queryEmbedding = await generateQueryEmbedding(query, env.OPENAI_API_KEY, env.EMBEDDING_CACHE);

      // 2. Search Vectorize for similar vectors
      // Cloudflare Vectorize limit: max 50 results with returnMetadata: true
      // When book filter is specified, use Vectorize metadata filtering for better performance
      const vectorK = Math.min(topK * 2, 50);

      const queryOptions: any = {
        topK: vectorK,
        returnMetadata: true
      };

      // Apply metadata filter at Vectorize level if book filter specified
      if (bookFilter) {
        queryOptions.filter = { book_code: bookFilter };
      }

      const vectorResults = await env.VECTORIZE.query(queryEmbedding, queryOptions);

      // DEBUG: Log Vectorize results
      console.log(`Vectorize returned ${vectorResults.matches.length} matches for query: "${query}"`);
      console.log(`Book filter: ${bookFilter || 'none'}, Source: ${source}`);

      // Log first 5 matches with metadata
      vectorResults.matches.slice(0, 5).forEach((match, i) => {
        const meta = match.metadata as any;
        console.log(`  Match ${i+1}: score=${match.score.toFixed(4)}, source=${meta.source}, book_code=${meta.book_code}, id=${match.id}`);
      });

      // 3. Get full data from D1 based on source
      const results: SearchResult[] = [];
      const SCORE_THRESHOLD = 0.3; // Minimum similarity score

      for (const match of vectorResults.matches) {
        // Skip low-quality matches
        if (match.score < SCORE_THRESHOLD) {
          console.log(`Skipping low-score match: ${match.score.toFixed(4)} < ${SCORE_THRESHOLD}`);
          continue;
        }

        const metadata = match.metadata as any;

        // Determine source from metadata
        // NOTE: Vectorize sometimes doesn't return 'source' field, so we infer from book_code
        let chunkSource = metadata.source;
        if (!chunkSource) {
          // If book_code exists, it's vedabase; otherwise philosophy
          chunkSource = metadata.book_code ? 'vedabase' : 'philosophy';
        }

        // Filter by source
        if (source !== 'all' && chunkSource !== source) {
          continue;
        }

        if (chunkSource === 'vedabase') {
          // Handle Vedabase results
          const chunkId = metadata.chunk_id;

          if (!chunkId) {
            console.error(`Missing chunk_id in metadata for match ${match.id}`);
            continue;
          }

          // Get chunk and verse data
          const chunkData = await env.DB.prepare(`
            SELECT
              c.content as chunk_text,
              c.chunk_type,
              v.id as verse_id,
              v.chapter,
              v.verse_number,
              v.sanskrit,
              v.synonyms,
              v.translation,
              b.code as book_code,
              b.name as book_name
            FROM vedabase_chunks c
            JOIN vedabase_verses v ON c.verse_id = v.id
            JOIN vedabase_books b ON v.book_id = b.id
            WHERE c.id = ?
          `).bind(chunkId).first();

          if (!chunkData) {
            continue;
          }

          // Book filter is already applied at Vectorize level (lines 194-196)
          // No need for additional filtering here

          // Calculate hybrid score (vector 70% + keyword 30%)
          const keywordScore = calculateKeywordScore(query, chunkData.chunk_text as string);
          const finalScore = hybridScore(match.score, keywordScore);

          results.push({
            score: finalScore,
            source: 'vedabase',
            sectionType: chunkData.chunk_type as string,
            chunkText: chunkData.chunk_text as string,
            vedabaseVerse: {
              id: String(chunkData.verse_id),
              book_code: chunkData.book_code as string,
              book_name: chunkData.book_name as string,
              chapter: chunkData.chapter as string,
              verse_number: chunkData.verse_number as string,
              sanskrit: chunkData.sanskrit as string | undefined,
              synonyms: chunkData.synonyms as string | undefined,
              translation: chunkData.translation as string | undefined
            }
          });
        } else {
          // Handle Philosophy results (existing logic)
          const responseId = metadata.responseId;

          if (!responseId) {
            console.error(`Missing responseId in metadata for match ${match.id}`);
            continue;
          }

          // Apply filters
          if (questionFilter && !metadata.questionNumber.includes(questionFilter)) {
            continue;
          }
          if (traditionFilter && !metadata.traditionName.toLowerCase().includes(traditionFilter.toLowerCase())) {
            continue;
          }

          // Get chunk text via embeddings -> chunks join
          const embeddingData = await env.DB.prepare(`
            SELECT c.content as chunk_text
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            WHERE e.id = ?
          `).bind(match.id).first();

          if (!embeddingData) {
            console.error(`No embedding data found for match.id: ${match.id}`);
            continue;
          }

          // Get full response
          const responseData = await env.DB.prepare(`
            SELECT
              r.id,
              r.opening,
              r.historical_development,
              r.key_concepts,
              r.core_arguments,
              r.counter_arguments,
              r.textual_foundation,
              r.internal_variations,
              r.contemporary_applications,
              q.number as question_number,
              q.title as question_title,
              t.name as tradition_name
            FROM responses r
            JOIN questions q ON r.question_id = q.id
            JOIN traditions t ON r.tradition_id = t.id
            WHERE r.id = ?
          `).bind(responseId).first();

          if (responseData && embeddingData) {
            // Calculate hybrid score (vector 70% + keyword 30%)
            const keywordScore = calculateKeywordScore(query, embeddingData.chunk_text as string);
            const finalScore = hybridScore(match.score, keywordScore);

            results.push({
              score: finalScore,
              source: 'philosophy',
              sectionType: metadata.sectionType,
              chunkText: embeddingData.chunk_text as string,
              response: {
                id: responseData.id as string,
                tradition_name: responseData.tradition_name as string,
                question_number: responseData.question_number as string,
                question_title: responseData.question_title as string,
                opening: responseData.opening as string,
                historical_development: responseData.historical_development as string | undefined,
                key_concepts: responseData.key_concepts as string | undefined,
                core_arguments: responseData.core_arguments as string | undefined,
                counter_arguments: responseData.counter_arguments as string | undefined,
                textual_foundation: responseData.textual_foundation as string | undefined,
                internal_variations: responseData.internal_variations as string | undefined,
                contemporary_applications: responseData.contemporary_applications as string | undefined
              }
            });
          }
        }

        if (results.length >= topK) {
          break;
        }
      }

      // Sort results by hybrid score (descending) and limit to topK
      results.sort((a, b) => b.score - a.score);
      const finalResults = results.slice(0, topK);

      return new Response(JSON.stringify({
        query,
        count: finalResults.length,
        results: finalResults
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({ error: String(error) }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
  }
};

/**
 * Normalize Sanskrit/IAST text for consistent matching
 * Converts various forms of diacritics to standard forms
 */
function normalizeSanskrit(text: string): string {
  // Common Sanskrit name variations
  const replacements: Record<string, string> = {
    // Krishna variations
    'kṛṣṇa': 'krishna',
    'krsna': 'krishna',
    'कृष्ण': 'krishna',

    // Arjuna variations
    'arjuna': 'arjuna',
    'अर्जुन': 'arjuna',

    // Bhagavad Gita variations
    'bhagavad gītā': 'bhagavad gita',
    'bhagavad geeta': 'bhagavad gita',
    'भगवद्गीता': 'bhagavad gita',

    // Yoga variations
    'yoga': 'yoga',
    'योग': 'yoga',

    // Dharma variations
    'dharma': 'dharma',
    'धर्म': 'dharma',

    // Karma variations
    'karma': 'karma',
    'कर्म': 'karma',

    // Atma/Soul variations
    'ātmā': 'atma',
    'atman': 'atma',
    'आत्मा': 'atma',

    // Brahman variations
    'brahman': 'brahman',
    'ब्रह्मन्': 'brahman',

    // Bhakti variations
    'bhakti': 'bhakti',
    'भक्ति': 'bhakti',

    // Remove common diacritics
    'ā': 'a', 'ī': 'i', 'ū': 'u',
    'ṛ': 'r', 'ṝ': 'r',
    'ḷ': 'l', 'ḹ': 'l',
    'ṃ': 'm', 'ṁ': 'm', 'ḥ': 'h',
    'ś': 's', 'ṣ': 's',
    'ṭ': 't', 'ḍ': 'd',
    'ṇ': 'n', 'ñ': 'n'
  };

  let normalized = text.toLowerCase();

  // Apply replacements
  for (const [pattern, replacement] of Object.entries(replacements)) {
    normalized = normalized.replace(new RegExp(pattern, 'g'), replacement);
  }

  return normalized;
}

/**
 * Expand query with relevant Vedic terminology synonyms and related concepts
 * Improves recall by adding contextually relevant terms
 */
function expandQuery(query: string): string {
  const lowerQuery = query.toLowerCase();
  const expansions: string[] = [query]; // Start with original query

  // Vedic concept synonyms and related terms
  const synonymDictionary: Record<string, string[]> = {
    // Core deities
    'krishna': ['supreme personality of godhead', 'bhagavan', 'govinda', 'vasudeva'],
    'god': ['supreme', 'absolute truth', 'bhagavan', 'paramatma', 'supersoul'],
    'lord': ['supreme lord', 'krishna', 'vishnu', 'narayana'],

    // Spiritual practices
    'chanting': ['kirtan', 'japa', 'holy name', 'hare krishna mantra', 'maha mantra'],
    'meditation': ['dhyana', 'contemplation', 'concentration'],
    'prayer': ['supplication', 'devotional service', 'bhajan'],
    'worship': ['puja', 'arcana', 'deity worship', 'devotional service'],

    // Philosophical concepts
    'soul': ['atma', 'self', 'spirit soul', 'jivatma', 'living entity'],
    'supersoul': ['paramatma', 'antaryami', 'inner witness'],
    'liberation': ['moksha', 'mukti', 'freedom', 'self-realization'],
    'consciousness': ['awareness', 'knowledge', 'jnana', 'realization'],

    // Types of yoga
    'bhakti': ['devotion', 'devotional service', 'love of god', 'pure devotion'],
    'yoga': ['union', 'connection', 'spiritual practice'],
    'karma yoga': ['action in devotion', 'work in krishna consciousness'],
    'jnana': ['knowledge', 'wisdom', 'understanding'],

    // Spiritual principles
    'dharma': ['duty', 'righteousness', 'religion', 'eternal occupation'],
    'karma': ['action', 'work', 'fruitive activities', 'reaction'],
    'maya': ['illusion', 'material energy', 'external energy'],
    'reincarnation': ['transmigration', 'rebirth', 'samsara', 'cycle of birth and death'],

    // Spiritual relationships
    'guru': ['spiritual master', 'teacher', 'acharya', 'preceptor'],
    'disciple': ['student', 'devotee', 'follower', 'initiate'],
    'association': ['satsanga', 'company', 'sangha', 'fellowship'],

    // Spiritual qualities
    'renunciation': ['detachment', 'vairagya', 'sannyasa'],
    'surrender': ['sharanagati', 'submission', 'giving up'],
    'humility': ['meekness', 'modesty', 'absence of pride'],
    'tolerance': ['forbearance', 'patience', 'titiksha'],

    // Material vs spiritual
    'material': ['temporary', 'mundane', 'worldly', 'maya'],
    'spiritual': ['transcendental', 'eternal', 'absolute', 'divine'],
    'illusion': ['maya', 'false ego', 'ahamkara', 'misidentification'],

    // Devotional concepts
    'service': ['seva', 'devotional service', 'bhakti', 'surrender'],
    'love': ['prema', 'pure love', 'devotion', 'affection for krishna'],
    'grace': ['mercy', 'kripa', 'blessing', 'causeless mercy'],

    // Mind and senses
    'mind': ['manas', 'mental', 'thoughts', 'consciousness'],
    'senses': ['indriyas', 'sense organs', 'sense gratification'],
    'desire': ['kama', 'lust', 'craving', 'material desire'],

    // Life and death
    'life': ['existence', 'living', 'embodiment'],
    'death': ['passing', 'leaving body', 'transmigration'],
    'body': ['material body', 'form', 'physical vessel'],

    // Sacred texts
    'bhagavad gita': ['gita', 'song of god', 'krishnas teaching'],
    'srimad bhagavatam': ['bhagavatam', 'bhagavata purana'],
    'vedas': ['vedic literature', 'shruti', 'revealed scriptures'],

    // Time and creation
    'creation': ['manifestation', 'cosmic creation', 'material world'],
    'time': ['kala', 'eternal time', 'factor of time'],
    'universe': ['material world', 'cosmic manifestation', 'brahmanda']
  };

  // Find matching concepts and add synonyms
  for (const [concept, synonyms] of Object.entries(synonymDictionary)) {
    // Check if the concept appears in the query
    const conceptRegex = new RegExp(`\\b${concept}\\b`, 'i');
    if (conceptRegex.test(lowerQuery)) {
      // Add up to 2 most relevant synonyms
      expansions.push(...synonyms.slice(0, 2));
    }
  }

  // Combine original query with expansions (weighted toward original)
  if (expansions.length > 1) {
    // Original query appears 3x for higher weight
    const weightedQuery = `${query} ${query} ${query} ${expansions.slice(1).join(' ')}`;
    console.log(`Query expanded: "${query}" -> added ${expansions.length - 1} related terms`);
    return weightedQuery;
  }

  return query;
}

/**
 * Calculate BM25-style keyword relevance score
 * Simplified implementation for worker environment
 */
function calculateKeywordScore(query: string, text: string): number {
  const queryTerms = query.toLowerCase()
    .split(/\s+/)
    .filter(term => term.length > 2); // Ignore very short words

  if (queryTerms.length === 0) return 0;

  const textLower = text.toLowerCase();
  let matchCount = 0;
  let totalTerms = queryTerms.length;

  // Count how many query terms appear in text
  for (const term of queryTerms) {
    if (textLower.includes(term)) {
      matchCount++;
    }
  }

  // Simple term frequency score (0-1)
  return matchCount / totalTerms;
}

/**
 * Combine vector similarity and keyword matching scores
 * @param vectorScore - Cosine similarity from vector search (0-1)
 * @param keywordScore - Keyword match score (0-1)
 * @param vectorWeight - Weight for vector score (default 0.7 = 70%)
 */
function hybridScore(vectorScore: number, keywordScore: number, vectorWeight: number = 0.7): number {
  const keywordWeight = 1 - vectorWeight;
  return (vectorScore * vectorWeight) + (keywordScore * keywordWeight);
}

/**
 * Generate query embedding using OpenAI with caching, normalization, and expansion
 */
async function generateQueryEmbedding(query: string, apiKey: string, cache?: KVNamespace): Promise<number[]> {
  // 1. Expand query with related Vedic terms
  const expandedQuery = expandQuery(query);

  // 2. Normalize Sanskrit in query for better matching
  const normalizedQuery = normalizeSanskrit(expandedQuery.trim());
  const cacheKey = `embedding:${normalizedQuery}`;

  // Try to get from cache first
  if (cache) {
    try {
      const cached = await cache.get(cacheKey, 'json');
      if (cached && Array.isArray(cached)) {
        console.log('Cache HIT for query:', query);
        return cached as number[];
      }
    } catch (error) {
      console.warn('Cache read error:', error);
    }
  }

  // Cache miss - generate embedding
  console.log('Cache MISS for query:', query, '-> normalized:', normalizedQuery);
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: normalizedQuery // Use normalized query
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.statusText}`);
  }

  const data = await response.json() as any;
  const embedding = data.data[0].embedding;

  // Store in cache (TTL: 7 days)
  if (cache) {
    try {
      await cache.put(cacheKey, JSON.stringify(embedding), {
        expirationTtl: 60 * 60 * 24 * 7 // 7 days
      });
    } catch (error) {
      console.warn('Cache write error:', error);
    }
  }

  return embedding;
}
