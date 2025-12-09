/**
 * Synthesis Worker - Gemini 2.5 Flash via OpenRouter
 * High quality synthesis with 1M token context and strict accuracy controls
 */

interface Env {
  DEEPSEEK_API_KEY: string;
  OPENROUTER_API_KEY: string;
  OPENAI_API_KEY: string;
  GEMINI_API_KEY: string;
}

interface SynthesisRequest {
  query: string;
  sources: Array<{
    response?: {
      tradition_name: string;
      question_number: string;
    };
    sectionType?: string;
    verse?: {
      book?: string;
      book_name?: string;
      chapter?: string;
      verse_number?: string;
    };
    chunkType?: string;
    chunkText: string;
    score: number;
  }>;
  wordLimit: number;
  bookContext?: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // CORS
    if (request.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type'
        }
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const body = await request.json() as SynthesisRequest;
      const { query, sources, wordLimit, bookContext } = body;

      if (!query || !sources || !wordLimit) {
        return new Response('Missing required fields', { status: 400 });
      }

      // Build context from ALL sources - Gemini 2.5 Flash can handle 1M tokens
      // No source numbers - just the text
      const context = sources.map((src) => {
        return src.chunkText;
      }).join('\n\n' + '='.repeat(80) + '\n\n');

      const bookContextNote = bookContext
        ? `\n\nIMPORTANT: The user specifically filtered to search only in "${bookContext}". Your answer should ONLY reference information from this book. If you mention anything, clearly state it comes from ${bookContext}.`
        : '';

      const prompt = `You are a Vedic scripture reference system. Your ONLY job is to synthesize the provided sources.

CRITICAL RULES:
1. Use ONLY information from the sources below - NO external knowledge
2. If the sources don't answer the question, say "The provided sources do not contain information about this topic"
3. NEVER make up, infer, or add information not explicitly in the sources
4. NEVER combine information about different people/topics (e.g., don't mix facts about different munis)
5. Copy Sanskrit/IAST characters EXACTLY as they appear
6. When referencing scriptures, only cite what's explicitly stated in the sources${bookContextNote}

Question: ${query}

Sources from authentic Vedabase texts:
${context}

Synthesize an answer in ${wordLimit} words using ONLY the information above. If the sources are insufficient, state that clearly.`;

      let synthesis = '';
      let modelUsed = '';
      let provider = '';

      // Using Gemini 2.5 Flash via OpenRouter
      // 1M token context, excellent quality, best price-performance
      // Most popular model on OpenRouter (11.1% usage)

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://vedabase-rag.com',
          'X-Title': 'Vedabase RAG'
        },
        body: JSON.stringify({
          model: 'google/gemini-2.5-flash',
          messages: [
            {
              role: 'user',
              content: prompt
            }
          ],
          max_tokens: Math.max(300, Math.floor(wordLimit * 6)),
          temperature: 0.1,
          stream: true
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Gemini 2.5 Flash error: ${error}`);
      }

      console.log('Using Gemini 2.5 Flash via OpenRouter - 1M token context, ALL sources included');

      // Return streaming response
      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*'
        }
      });

      /*
      // GPT-4o via OpenRouter (fallback)
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://vedabase-rag.com',
          'X-Title': 'Vedabase RAG'
        },
        body: JSON.stringify({
          model: 'openai/gpt-4o',
          messages: [
            {
              role: 'system',
              content: systemPrompt
            },
            {
              role: 'user',
              content: prompt
            }
          ],
          max_tokens: Math.max(300, Math.floor(wordLimit * 6)), // Generous buffer to prevent truncation
          temperature: 0.1, // Ultra-low temperature for maximum accuracy
          stream: true  // Enable streaming
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`GPT-4o fallback error: ${error}`);
      }

      // Return streaming response
      modelUsed = 'openai/gpt-4o';
      provider = 'OpenRouter (GPT-4o)';
      console.log('Using GPT-4o for synthesis with streaming');

      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
          'Access-Control-Allow-Origin': '*'
        }
      });
      */

    } catch (error) {
      return new Response(JSON.stringify({
        error: String(error),
        message: 'Synthesis failed'
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });
    }
  }
};
