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

      // 1. Generate query embedding
      const queryEmbedding = await generateQueryEmbedding(query, env.OPENAI_API_KEY);

      // 2. Search Vectorize for similar vectors
      // Cloudflare Vectorize limit: max 50 results with returnMetadata: true
      const vectorK = Math.min(topK * 2, 50);
      const vectorResults = await env.VECTORIZE.query(queryEmbedding, {
        topK: vectorK,
        returnMetadata: true
      });

      // 3. Get full data from D1 based on source
      const results: SearchResult[] = [];

      for (const match of vectorResults.matches) {
        const metadata = match.metadata as any;
        const chunkSource = metadata.source || 'philosophy'; // Default to philosophy for backwards compatibility

        // Filter by source
        if (source !== 'all' && chunkSource !== source) {
          continue;
        }

        if (chunkSource === 'vedabase') {
          // Handle Vedabase results
          const chunkId = metadata.chunk_id;

          // Apply book filter (handle undefined book_code for old embeddings)
          if (bookFilter && metadata.book_code && metadata.book_code !== bookFilter) {
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

          if (chunkData) {
            results.push({
              score: match.score,
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
          }
        } else {
          // Handle Philosophy results (existing logic)
          const responseId = metadata.responseId;

          // Apply filters
          if (questionFilter && !metadata.questionNumber.includes(questionFilter)) {
            continue;
          }
          if (traditionFilter && !metadata.traditionName.toLowerCase().includes(traditionFilter.toLowerCase())) {
            continue;
          }

          // Get embedding metadata
          const embeddingData = await env.DB.prepare(`
            SELECT chunk_text
            FROM embeddings
            WHERE id = ?
          `).bind(match.id).first();

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
            results.push({
              score: match.score,
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

      return new Response(JSON.stringify({
        query,
        count: results.length,
        results
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
 * Generate query embedding using OpenAI
 */
async function generateQueryEmbedding(query: string, apiKey: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: query
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.statusText}`);
  }

  const data = await response.json() as any;
  return data.data[0].embedding;
}
