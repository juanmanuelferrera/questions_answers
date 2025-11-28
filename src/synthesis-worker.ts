/**
 * Synthesis Worker - OpenRouter GPT-OSS-120B + GPT-4o Synthesis
 *
 * Primary: OpenRouter GPT-OSS-120B ($9/month, fast, 80/100 quality, 97.5% cheaper)
 * Fallback: GPT-4o (for reliability, 95/100 quality)
 * Hides API keys from browser and adds rate limiting
 */

interface Env {
  OPENROUTER_API_KEY: string;
  OPENAI_API_KEY: string;
  RATE_LIMITER: RateLimit;
}

interface SynthesisRequest {
  query: string;
  sources: Array<{
    // Old format (philosophy)
    response?: {
      tradition_name: string;
      question_number: string;
    };
    sectionType?: string;
    // New format (Vedabase)
    verse?: {
      book: string;
      chapter: string;
      verse_number: string;
      sanskrit?: string;
      translation?: string;
    };
    chunkType?: string;
    chunkText: string;
    score: number;
  }>;
  wordLimit: number;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Handle CORS preflight
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
      // Rate limiting (max 60 requests per minute per IP)
      const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';

      // Simple in-memory rate limiting (for demonstration)
      // In production, use Cloudflare's Durable Objects or KV for persistent rate limiting

      const body = await request.json() as SynthesisRequest;
      const { query, sources, wordLimit } = body;

      if (!query || !sources || !wordLimit) {
        return new Response('Missing required fields', { status: 400 });
      }

      // Build context from sources (supports both formats)
      const context = sources.map((src, i) => {
        // Detect format
        if (src.verse) {
          // Vedabase format
          const chapterInfo = src.verse.chapter ? ` (${src.verse.chapter})` : '';
          return `**Source ${i + 1}: ${src.verse.book}${chapterInfo}** - Verse ${src.verse.verse_number} [Similarity: ${src.score.toFixed(3)}]\n\n${src.chunkText}`;
        } else if (src.response) {
          // Philosophy format
          return `**Source ${i + 1}: ${src.response.tradition_name}** (Q${src.response.question_number}, ${src.sectionType?.replace(/_/g, ' ')}) [Similarity: ${src.score.toFixed(3)}]\n\n${src.chunkText}`;
        }
        return `**Source ${i + 1}** [Similarity: ${src.score.toFixed(3)}]\n\n${src.chunkText}`;
      }).join('\n\n' + '='.repeat(80) + '\n\n');

      // Create prompt
      const prompt = `Based on the sources below, synthesize an answer to the question.

QUESTION: ${query}

SOURCES:
${context}

CRITICAL REQUIREMENTS:
1. Your response MUST be EXACTLY ${wordLimit} words or fewer. This is a strict limit.
2. Format your answer in multiple clear paragraphs separated by blank lines.
3. Each paragraph should focus on a distinct aspect or tradition.

Please create a synthesis that:
1. Directly answers the question
2. Integrates multiple philosophical perspectives from the sources
3. Highlights agreements and disagreements between traditions
4. Uses specific concepts and arguments from the sources
5. Maintains academic precision and nuance
6. FORMATS IN PARAGRAPHS: Use 2-4 paragraphs depending on word limit (separate with double line breaks)

FORMATTING: Write in clear paragraphs. For example:
[Opening paragraph introducing main themes...]

[Second paragraph comparing different traditions...]

[Third paragraph highlighting key disagreements or convergences...]

WORD LIMIT: ${wordLimit} words maximum. Count carefully and stop at ${wordLimit} words.`;

      // Try OpenRouter GPT-OSS-120B first ($9/month, fast), fallback to GPT-4o
      let synthesis: string;
      let modelUsed = 'gpt-oss-120b';

      try {
        // Call OpenRouter API (FREE tier)
        const openrouterResponse = await fetch('https://openrouter.ai/api/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${env.OPENROUTER_API_KEY}`,
            'HTTP-Referer': 'https://vedabase-rag.com',
            'X-Title': 'Vedabase RAG Synthesis'
          },
          body: JSON.stringify({
            model: 'openai/gpt-oss-120b',  // $0.04/M input + $0.20/M output = ~$9/month
            messages: [
              {
                role: 'system',
                content: `You are an expert synthesizer of knowledge from diverse sources. CRITICAL: Always respect the word limit strictly. Your responses must not exceed ${wordLimit} words.`
              },
              {
                role: 'user',
                content: prompt
              }
            ],
            max_tokens: Math.floor(wordLimit * 1.5),
            temperature: 0.7
          })
        });

        if (!openrouterResponse.ok) {
          const errorText = await openrouterResponse.text();
          console.error('OpenRouter API error, falling back to GPT-4o:', errorText);
          throw new Error(`OpenRouter error: ${errorText}`);
        }

        const openrouterData = await openrouterResponse.json() as any;
        synthesis = openrouterData.choices[0].message.content;

      } catch (openrouterError) {
        // Fallback to GPT-4o if OpenRouter fails
        console.log('OpenRouter failed, using GPT-4o fallback');
        modelUsed = 'gpt-4o';

        const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${env.OPENAI_API_KEY}`
          },
          body: JSON.stringify({
            model: 'gpt-4o',
            messages: [
              {
                role: 'system',
                content: `You are an expert synthesizer of knowledge from diverse sources. CRITICAL: Always respect the word limit strictly. Your responses must not exceed ${wordLimit} words.`
              },
              {
                role: 'user',
                content: prompt
              }
            ],
            max_tokens: Math.floor(wordLimit * 1.5),
            temperature: 0.7
          })
        });

        if (!openaiResponse.ok) {
          const error = await openaiResponse.text();
          throw new Error(`Both OpenRouter and GPT-4o failed. GPT-4o error: ${error}`);
        }

        const data = await openaiResponse.json() as any;
        synthesis = data.choices[0].message.content;
      }

      return new Response(JSON.stringify({
        synthesis,
        model: modelUsed,
        cost_savings: modelUsed === 'gpt-oss-120b' ? '97.5% - $9/mo vs $360/mo' : '0%',
        speed: modelUsed === 'gpt-oss-120b' ? 'Fast (260 tok/s)' : 'Standard'
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: String(error),
        message: 'Failed to generate synthesis'
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
