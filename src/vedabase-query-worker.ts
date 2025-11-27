/**
 * Vedabase Query Worker
 * Semantic search across Vedic texts with RAG
 */

interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
}

interface QueryRequest {
  query: string;
  topK?: number;
  bookFilter?: string;
}

interface SearchResult {
  score: number;
  chunkType: string;
  chunkText: string;
  verse: {
    book: string;
    chapter: string;
    verse_number: string;
    sanskrit: string;
    translation: string;
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

    // GET /books - Return list of all books
    if (request.method === 'GET' && new URL(request.url).pathname === '/books') {
      try {
        const books = await env.DB.prepare(`
          SELECT code, name
          FROM books
          ORDER BY id
        `).all();

        return new Response(JSON.stringify({
          books: books.results || []
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
      const { query, topK = 20, bookFilter } = body;

      if (!query) {
        return new Response('Query required', { status: 400 });
      }

      // 1. Generate query embedding
      const queryEmbedding = await generateQueryEmbedding(query, env.OPENAI_API_KEY);

      // 2. Search Vectorize for similar vectors
      const vectorResults = await env.VECTORIZE.query(queryEmbedding, {
        topK: topK * 2, // Get more candidates to filter
        returnMetadata: true
      });

      // 3. Get full verse data from D1
      const results: SearchResult[] = [];

      for (const match of vectorResults.matches) {
        const metadata = match.metadata as any;

        // Apply book filter
        if (bookFilter && metadata.book_code !== bookFilter) {
          continue;
        }

        // Get chunk content using verse_id, chunk_type, and chunk_index
        // (more reliable than chunk_id which may not be preserved in metadata)
        const chunkData = await env.DB.prepare(`
          SELECT c.content, c.chunk_type, c.chunk_index,
                 v.verse_number, v.chapter, v.sanskrit, v.translation,
                 b.name as book_name
          FROM chunks c
          JOIN verses v ON c.verse_id = v.id
          JOIN books b ON v.book_id = b.id
          WHERE c.verse_id = ? AND c.chunk_type = ? AND c.chunk_index = ?
        `).bind(metadata.verse_id, metadata.chunk_type, metadata.chunk_index).first();

        if (chunkData) {
          results.push({
            score: match.score,
            chunkType: chunkData.chunk_type as string,
            chunkText: chunkData.content as string,
            verse: {
              book: chunkData.book_name as string,
              chapter: chunkData.chapter as string || '',
              verse_number: chunkData.verse_number as string,
              sanskrit: chunkData.sanskrit as string || '',
              translation: chunkData.translation as string || ''
            }
          });

          if (results.length >= topK) {
            break;
          }
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
