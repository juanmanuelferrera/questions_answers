#!/usr/bin/env node

/**
 * Upload Response Files to Cloudflare D1 + Vectorize
 *
 * Usage:
 *   node upload-responses.js <worker-url> <file-pattern>
 *
 * Examples:
 *   node upload-responses.js https://philosophy-rag-import.xxx.workers.dev question_1.19_*.txt
 *   node upload-responses.js https://philosophy-rag-import.xxx.workers.dev "question_1.*.txt"
 */

const fs = require('fs');
const path = require('path');

// Parse command line arguments
const [,, workerUrl, filePattern] = process.argv;

if (!workerUrl || !filePattern) {
  console.error('Usage: node upload-responses.js <worker-url> <file-pattern>');
  console.error('Example: node upload-responses.js https://your-worker.workers.dev "question_1.19_*.txt"');
  process.exit(1);
}

// Simple glob implementation
function findFiles(pattern) {
  const dir = process.cwd();
  const files = fs.readdirSync(dir);

  const regex = new RegExp(
    '^' + pattern
      .replace(/\./g, '\\.')
      .replace(/\*/g, '.*')
      .replace(/\?/g, '.') + '$'
  );

  return files.filter(file => regex.test(file)).map(file => path.join(dir, file));
}

// Parse a response file into individual responses
function parseFile(filePath) {
  const content = fs.readFileSync(filePath, 'utf-8');
  const responses = [];

  // Split by response headers: "*** X.XX.NNN"
  const parts = content.split(/^(?=\*\*\* \d+\.\d+\.\d+)/m);

  for (const part of parts) {
    const trimmed = part.trim();
    if (trimmed && trimmed.startsWith('***')) {
      responses.push(trimmed);
    }
  }

  return responses;
}

// Upload responses to worker
async function uploadResponses(responses, workerUrl) {
  const response = await fetch(workerUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ responses })
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  return await response.json();
}

// Main execution
async function main() {
  console.log(`🔍 Finding files matching: ${filePattern}`);
  const files = findFiles(filePattern);

  if (files.length === 0) {
    console.error(`❌ No files found matching pattern: ${filePattern}`);
    process.exit(1);
  }

  console.log(`📁 Found ${files.length} file(s):\n${files.map(f => `   - ${path.basename(f)}`).join('\n')}`);
  console.log();

  let totalProcessed = 0;
  let totalErrors = 0;

  for (const file of files) {
    const fileName = path.basename(file);
    console.log(`📤 Processing: ${fileName}`);

    try {
      const responses = parseFile(file);
      console.log(`   Found ${responses.length} responses`);

      if (responses.length === 0) {
        console.log(`   ⚠️  Skipping (no responses found)`);
        continue;
      }

      // Upload in batches of 10 to avoid timeout
      const batchSize = 10;
      for (let i = 0; i < responses.length; i += batchSize) {
        const batch = responses.slice(i, i + batchSize);
        console.log(`   Uploading batch ${Math.floor(i / batchSize) + 1}/${Math.ceil(responses.length / batchSize)}...`);

        const result = await uploadResponses(batch, workerUrl);
        totalProcessed += result.processed;

        if (result.errors && result.errors.length > 0) {
          console.log(`   ⚠️  ${result.errors.length} error(s):`);
          result.errors.forEach(err => console.log(`      - ${err}`));
          totalErrors += result.errors.length;
        }
      }

      console.log(`   ✅ Completed: ${responses.length} responses uploaded`);
      console.log();

    } catch (error) {
      console.error(`   ❌ Failed: ${error.message}`);
      console.log();
      totalErrors++;
    }
  }

  console.log('━'.repeat(60));
  console.log(`✨ Upload complete!`);
  console.log(`   Total processed: ${totalProcessed}`);
  console.log(`   Total errors: ${totalErrors}`);
  console.log('━'.repeat(60));
}

main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
