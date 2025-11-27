/**
 * Philosophy RAG Import Worker
 *
 * Parses response files and uploads to D1 + Vectorize
 * Handles incremental uploads for any number of responses
 */

interface Env {
  DB: D1Database;
  VECTORIZE: VectorizeIndex;
  OPENAI_API_KEY: string;
}

interface ParsedResponse {
  id: string;
  questionNumber: string;
  questionTitle: string;
  traditionName: string;
  sections: {
    opening: string;
    historicalDevelopment?: string;
    keyConcepts?: string;
    coreArguments?: string;
    counterArguments?: string;
    textualFoundation?: string;
    internalVariations?: string;
    contemporaryApplications?: string;
  };
}

interface Chunk {
  id: string;
  text: string;
  sectionType: string;
  index: number;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405 });
    }

    try {
      const body = await request.json() as { responses: string[] };
      const responseTexts = body.responses;

      if (!responseTexts || responseTexts.length === 0) {
        return new Response('No responses provided', { status: 400 });
      }

      const results = {
        processed: 0,
        errors: [] as string[],
        responses: [] as string[]
      };

      for (const responseText of responseTexts) {
        try {
          const parsed = parseResponse(responseText);
          await uploadResponse(parsed, env);
          results.processed++;
          results.responses.push(parsed.id);
        } catch (error) {
          results.errors.push(`Failed to process response: ${error}`);
        }
      }

      return new Response(JSON.stringify(results), {
        headers: { 'Content-Type': 'application/json' }
      });

    } catch (error) {
      return new Response(`Error: ${error}`, { status: 500 });
    }
  }
};

/**
 * Parse a response text into structured format
 */
function parseResponse(text: string): ParsedResponse {
  const lines = text.trim().split('\n');

  // Parse header: "*** X.XX.NNN Tradition Name Response"
  const headerMatch = lines[0].match(/\*\*\*\s+(\d+\.\d+)\.(\d+)\s+(.+?)\s+Response/);
  if (!headerMatch) {
    throw new Error('Invalid response header format');
  }

  const questionNumber = headerMatch[1];
  const traditionNumber = headerMatch[2];
  const traditionName = headerMatch[3];
  const id = `${questionNumber}.${traditionNumber}`;

  // Extract sections
  const sections: ParsedResponse['sections'] = {
    opening: ''
  };

  let currentSection: keyof typeof sections | null = null;
  let currentText: string[] = [];

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();

    if (!line) continue;

    // Check for section headers
    if (line.startsWith('**Historical Development**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'historicalDevelopment';
      currentText = [line.replace('**Historical Development**:', '').trim()];
    } else if (line.startsWith('**Key Concepts**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'keyConcepts';
      currentText = [line.replace('**Key Concepts**:', '').trim()];
    } else if (line.startsWith('**Core Arguments**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'coreArguments';
      currentText = [line.replace('**Core Arguments**:', '').trim()];
    } else if (line.startsWith('**Counter-Arguments**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'counterArguments';
      currentText = [line.replace('**Counter-Arguments**:', '').trim()];
    } else if (line.startsWith('**Textual Foundation**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'textualFoundation';
      currentText = [line.replace('**Textual Foundation**:', '').trim()];
    } else if (line.startsWith('**Internal Variations**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'internalVariations';
      currentText = [line.replace('**Internal Variations**:', '').trim()];
    } else if (line.startsWith('**Contemporary Applications**:')) {
      if (currentSection) {
        sections[currentSection] = currentText.join(' ').trim();
      }
      currentSection = 'contemporaryApplications';
      currentText = [line.replace('**Contemporary Applications**:', '').trim()];
    } else {
      // Add to current section (or opening if no section yet)
      if (currentSection === null) {
        if (sections.opening) {
          sections.opening += ' ' + line;
        } else {
          sections.opening = line;
        }
      } else {
        currentText.push(line);
      }
    }
  }

  // Save last section
  if (currentSection) {
    sections[currentSection] = currentText.join(' ').trim();
  }

  // Extract question title from opening (if present)
  const questionTitle = `Question ${questionNumber}`;

  return {
    id,
    questionNumber,
    questionTitle,
    traditionName,
    sections
  };
}

/**
 * Create semantic chunks from response
 */
function createChunks(response: ParsedResponse): Chunk[] {
  const chunks: Chunk[] = [];
  let index = 0;

  // Chunk 0: Opening
  chunks.push({
    id: `${response.id}-chunk-${index}`,
    text: response.sections.opening,
    sectionType: 'opening',
    index: index++
  });

  // Chunk 1: Historical Development
  if (response.sections.historicalDevelopment) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.historicalDevelopment,
      sectionType: 'historical_development',
      index: index++
    });
  }

  // Chunk 2: Key Concepts
  if (response.sections.keyConcepts) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.keyConcepts,
      sectionType: 'key_concepts',
      index: index++
    });
  }

  // Chunk 3: Core Arguments
  if (response.sections.coreArguments) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.coreArguments,
      sectionType: 'core_arguments',
      index: index++
    });
  }

  // Chunk 4: Counter-Arguments
  if (response.sections.counterArguments) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.counterArguments,
      sectionType: 'counter_arguments',
      index: index++
    });
  }

  // Chunk 5: Textual Foundation
  if (response.sections.textualFoundation) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.textualFoundation,
      sectionType: 'textual_foundation',
      index: index++
    });
  }

  // Chunk 6: Internal Variations
  if (response.sections.internalVariations) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.internalVariations,
      sectionType: 'internal_variations',
      index: index++
    });
  }

  // Chunk 7: Contemporary Applications
  if (response.sections.contemporaryApplications) {
    chunks.push({
      id: `${response.id}-chunk-${index}`,
      text: response.sections.contemporaryApplications,
      sectionType: 'contemporary_applications',
      index: index++
    });
  }

  return chunks;
}

/**
 * Generate embeddings using OpenAI
 */
async function generateEmbeddings(texts: string[], apiKey: string): Promise<number[][]> {
  const response = await fetch('https://api.openai.com/v1/embeddings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: 'text-embedding-3-small',
      input: texts
    })
  });

  if (!response.ok) {
    throw new Error(`OpenAI API error: ${response.statusText}`);
  }

  const data = await response.json() as any;
  return data.data.map((item: any) => item.embedding);
}

/**
 * Upload response with embeddings to D1 + Vectorize
 */
async function uploadResponse(response: ParsedResponse, env: Env): Promise<void> {
  // 1. Insert question if not exists
  await env.DB.prepare(
    'INSERT OR IGNORE INTO questions (number, title) VALUES (?, ?)'
  ).bind(response.questionNumber, response.questionTitle).run();

  const questionResult = await env.DB.prepare(
    'SELECT id FROM questions WHERE number = ?'
  ).bind(response.questionNumber).first();

  const questionId = questionResult!.id as number;

  // 2. Insert tradition if not exists
  await env.DB.prepare(
    'INSERT OR IGNORE INTO traditions (name) VALUES (?)'
  ).bind(response.traditionName).run();

  const traditionResult = await env.DB.prepare(
    'SELECT id FROM traditions WHERE name = ?'
  ).bind(response.traditionName).first();

  const traditionId = traditionResult!.id as number;

  // 3. Insert response
  await env.DB.prepare(`
    INSERT OR REPLACE INTO responses (
      id, question_id, tradition_id, opening, historical_development,
      key_concepts, core_arguments, counter_arguments, textual_foundation,
      internal_variations, contemporary_applications
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  `).bind(
    response.id,
    questionId,
    traditionId,
    response.sections.opening,
    response.sections.historicalDevelopment || null,
    response.sections.keyConcepts || null,
    response.sections.coreArguments || null,
    response.sections.counterArguments || null,
    response.sections.textualFoundation || null,
    response.sections.internalVariations || null,
    response.sections.contemporaryApplications || null
  ).run();

  // 4. Create chunks and generate embeddings
  const chunks = createChunks(response);
  const chunkTexts = chunks.map(c => c.text);
  const embeddings = await generateEmbeddings(chunkTexts, env.OPENAI_API_KEY);

  // 5. Insert embeddings into D1
  for (let i = 0; i < chunks.length; i++) {
    const chunk = chunks[i];
    await env.DB.prepare(`
      INSERT OR REPLACE INTO embeddings (id, response_id, section_type, chunk_index, chunk_text)
      VALUES (?, ?, ?, ?, ?)
    `).bind(
      chunk.id,
      response.id,
      chunk.sectionType,
      chunk.index,
      chunk.text
    ).run();
  }

  // 6. Insert vectors into Vectorize
  const vectors = chunks.map((chunk, i) => ({
    id: chunk.id,
    values: embeddings[i],
    metadata: {
      responseId: response.id,
      sectionType: chunk.sectionType,
      chunkIndex: chunk.index,
      questionNumber: response.questionNumber,
      traditionName: response.traditionName
    }
  }));

  await env.VECTORIZE.upsert(vectors);
}
