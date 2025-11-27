/**
 * Vedabase Import Worker
 * Imports verses with intelligent chunking for RAG
 */

interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
}

interface VerseData {
  book: string;
  chapter?: string;
  part?: string;
  chapter_title?: string;
  verse: string;
  sanskrit: string;
  synonyms: string;
  translation: string;
  purport: string;
}

interface ImportRequest {
  verses: VerseData[];
  book_code: string;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const { verses, book_code } = await request.json() as ImportRequest;

      if (!verses || !Array.isArray(verses)) {
        return new Response('Invalid verses data', { status: 400 });
      }

      // Get book_id
      const book = await env.DB.prepare('SELECT id FROM vedabase_books WHERE code = ?')
        .bind(book_code)
        .first();

      if (!book) {
        return new Response(`Book code '${book_code}' not found`, { status: 400 });
      }

      const book_id = book.id as number;
      let verses_imported = 0;
      let chunks_created = 0;

      for (const verseData of verses) {
        // 1. Insert verse
        const verseResult = await env.DB.prepare(`
          INSERT INTO vedabase_verses (book_id, chapter, verse_number, sanskrit, synonyms, translation)
          VALUES (?, ?, ?, ?, ?, ?)
        `).bind(
          book_id,
          verseData.chapter || verseData.part || null,
          verseData.verse,
          verseData.sanskrit,
          verseData.synonyms,
          verseData.translation
        ).run();

        const verse_id = verseResult.meta.last_row_id;

        // 2. Create chunks
        const chunks_to_insert = [];

        // Chunk 1: Verse text (sanskrit + translation combined)
        const verseText = `${verseData.sanskrit}\n\n${verseData.translation}`.trim();
        if (verseText) {
          chunks_to_insert.push({
            type: 'verse_text',
            index: 0,
            content: verseText,
            word_count: verseText.split(/\s+/).length
          });
        }

        // Chunk 2+: Purport paragraphs
        if (verseData.purport) {
          const paragraphs = verseData.purport
            .split('\n\n')
            .map(p => p.trim())
            .filter(p => p.length > 50); // Skip very short paragraphs

          paragraphs.forEach((para, index) => {
            chunks_to_insert.push({
              type: 'purport_paragraph',
              index: index + 1,
              content: para,
              word_count: para.split(/\s+/).length
            });
          });
        }

        // 3. Insert chunks and generate embeddings
        for (const chunk of chunks_to_insert) {
          // Insert chunk
          const chunkResult = await env.DB.prepare(`
            INSERT INTO vedabase_chunks (verse_id, chunk_type, chunk_index, content, word_count)
            VALUES (?, ?, ?, ?, ?)
          `).bind(
            verse_id,
            chunk.type,
            chunk.index,
            chunk.content,
            chunk.word_count
          ).run();

          const chunk_id = chunkResult.meta.last_row_id;

          // Generate embedding
          const embedding = await generateEmbedding(chunk.content, env.OPENAI_API_KEY);

          // Insert into Vectorize
          const vectorId = `${book_code}_${verse_id}_${chunk.type}_${chunk.index}`;
          await env.VECTORIZE.upsert([{
            id: vectorId,
            values: embedding,
            metadata: {
              chunk_id,
              verse_id,
              book_code,
              verse_number: verseData.verse,
              chapter: verseData.chapter || verseData.part || '',
              chunk_type: chunk.type,
              chunk_index: chunk.index
            }
          }]);

          // Record embedding in DB
          await env.DB.prepare(`
            INSERT INTO embeddings (id, chunk_id)
            VALUES (?, ?)
          `).bind(vectorId, chunk_id).run();

          chunks_created++;
        }

        verses_imported++;

        // Progress log every 50 verses
        if (verses_imported % 50 === 0) {
          console.log(`Imported ${verses_imported}/${verses.length} verses...`);
        }
      }

      return new Response(JSON.stringify({
        success: true,
        verses_imported,
        chunks_created,
        book_code
      }), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      console.error('Import error:', error);
      return new Response(JSON.stringify({
        error: String(error),
        message: 'Failed to import verses'
      }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  }
};

async function generateEmbedding(text: string, apiKey: string): Promise<number[]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: text
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.statusText}`);
  }

  const data = await response.json() as any;
  return data.data[0].embedding;
}
