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
      // Include metadata so the LLM knows the source of each chunk
      const context = sources.map((src, index) => {
        let header = '';

        // Build source header with metadata
        if (src.verse?.book_name) {
          header = `[Source: ${src.verse.book_name}`;
          if (src.verse.chapter) {
            header += ` - ${src.verse.chapter}`;
          }
          if (src.verse.verse_number) {
            header += ` (${src.verse.verse_number})`;
          }
          header += ']\n';
        }

        // DEBUG: Log first source to see structure
        if (index === 0) {
          console.log('First source structure:', JSON.stringify(src, null, 2));
          console.log('chunkText length:', src.chunkText?.length || 'UNDEFINED');
        }

        return header + (src.chunkText || '');
      }).join('\n\n' + '='.repeat(80) + '\n\n');

      const bookContextNote = bookContext
        ? `\n\nIMPORTANT: The user specifically filtered to search only in "${bookContext}". Your answer should ONLY reference information from this book. If you mention anything, clearly state it comes from ${bookContext}.`
        : '';

      const prompt = `You are a Vedic scripture reference system. Synthesize information from the provided sources to answer the question.

Question: ${query}

CRITICAL INSTRUCTIONS:
- The sources below may include conversations, interviews, letters, or scripture commentaries
- If someone's NAME appears in the sources (asking questions, being mentioned, etc.), that IS information about them
- Extract what they said, what they asked, or what was said about them
- Synthesize this into a coherent answer
- Use ONLY information explicitly present in the sources
- If the sources truly contain NO relevant information, say so${bookContextNote}

Sources from authentic Vedabase texts:
${context}

Based on the sources above, provide a ${wordLimit}-word answer using ONLY the information present in the text.`;

      let synthesis = '';
      let modelUsed = '';
      let provider = '';

      // Using Gemini 3 Pro Preview via OpenRouter
      // Google's flagship frontier model for high-precision multimodal reasoning
      // 1M token context, state-of-the-art benchmark results
      // Excels at: research synthesis, complex reasoning, factual QA

      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.OPENROUTER_API_KEY}`,
          'HTTP-Referer': 'https://vedabase-rag.com',
          'X-Title': 'Vedabase RAG'
        },
        body: JSON.stringify({
          model: 'google/gemini-3-pro-preview',
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
        throw new Error(`Gemini 3 Pro error: ${error}`);
      }

      console.log('Using Gemini 3 Pro Preview via OpenRouter - flagship model with 1M token context');

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
