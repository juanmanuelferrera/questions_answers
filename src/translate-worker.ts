/**
 * Translation Worker - Translates synthesis to Spanish using Gemini 2.5 Flash via OpenRouter
 */

interface Env {
  OPENAI_API_KEY: string; // Actually OpenRouter API key
}

interface TranslateRequest {
  question: string;
  answer: string;
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
      const body = await request.json() as TranslateRequest;
      const { question, answer } = body;

      if (!question || !answer) {
        return new Response('Missing required fields', { status: 400 });
      }

      // Call Gemini 2.5 Flash via OpenRouter for translation
      const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
          'HTTP-Referer': 'https://vedabase-rag.com',
          'X-Title': 'Vedabase Translation'
        },
        body: JSON.stringify({
          model: 'google/gemini-2.5-flash',
          messages: [
            {
              role: 'user',
              content: 'You are a professional translator specializing in spiritual and philosophical texts. Translate the following question and answer to Spanish, maintaining the same tone, structure, and spiritual terminology. Format the output as:\n\n[Translated Question]\n\n[Translated Answer]\n\nDo NOT include labels like "Pregunta:" or "Respuesta:".\n\n' + `${question}\n\n${answer}`
            }
          ],
          max_tokens: 1500,
          temperature: 0.3
        })
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`OpenRouter error: ${error}`);
      }

      const data = await response.json() as any;
      const translation = data.choices[0].message.content;

      return new Response(JSON.stringify({
        translation
      }), {
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      });

    } catch (error) {
      return new Response(JSON.stringify({
        error: String(error),
        message: 'Translation failed'
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
