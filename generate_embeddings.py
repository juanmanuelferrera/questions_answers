#!/usr/bin/env python3
"""
Generate vector embeddings for all responses in the database.

Uses OpenAI's text-embedding-3-small model (1536 dimensions).
Chunks responses by section for optimal retrieval.

Cost: ~$0.02 per 1000 chunks (~$0.38 for Questions 1.24-1.25)
"""

import os
import sqlite3
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
import time

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Embedding model configuration
MODEL = "text-embedding-3-small"
EMBEDDING_DIM = 1536
BATCH_SIZE = 100  # Process in batches to avoid rate limits

def get_embedding(text: str) -> np.ndarray:
    """Generate embedding for a text chunk"""
    try:
        response = client.embeddings.create(
            model=MODEL,
            input=text
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"   ❌ Error generating embedding: {e}")
        return None

def chunk_response_by_sections(response_data: dict) -> list[dict]:
    """
    Chunk a response into smaller pieces for embedding.

    Strategy: One chunk per section for new format responses.
    This preserves semantic coherence while keeping chunks manageable.
    """
    chunks = []

    # Section order and names
    sections = [
        ('opening', 'Opening'),
        ('historical_development', 'Historical Development'),
        ('key_concepts', 'Key Concepts'),
        ('core_arguments', 'Core Arguments'),
        ('counter_arguments', 'Counter-Arguments'),
        ('textual_foundation', 'Textual Foundation'),
        ('internal_variations', 'Internal Variations'),
        ('contemporary_applications', 'Contemporary Applications')
    ]

    for i, (section_key, section_name) in enumerate(sections):
        section_text = response_data.get(section_key)

        if section_text and section_text.strip():
            # Create chunk with metadata
            chunk = {
                'text': section_text.strip(),
                'section_type': section_key,
                'chunk_index': i,
                'metadata': f"[{response_data['tradition_name']} - {section_name}]\n"
            }
            chunks.append(chunk)

    return chunks

def generate_all_embeddings(db_path='philosophical_traditions_sample.db', clear_existing=False):
    """Generate embeddings for all responses in the database"""

    print("="*80)
    print("EMBEDDING GENERATION")
    print("="*80)
    print(f"Model: {MODEL}")
    print(f"Embedding dimension: {EMBEDDING_DIM}")
    print(f"Database: {db_path}\n")

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Clear existing embeddings if requested
    if clear_existing:
        cursor.execute("DELETE FROM embeddings")
        conn.commit()
        print("🗑️  Cleared existing embeddings\n")

    # Get all responses
    cursor.execute("""
        SELECT
            r.id, r.question_id, r.tradition_id, r.full_text,
            r.opening, r.historical_development, r.key_concepts,
            r.core_arguments, r.counter_arguments, r.textual_foundation,
            r.internal_variations, r.contemporary_applications,
            q.number as question_number, t.name as tradition_name
        FROM responses r
        JOIN questions q ON r.question_id = q.id
        JOIN traditions t ON r.tradition_id = t.id
    """)

    responses = cursor.fetchall()
    print(f"Found {len(responses)} responses to process\n")

    if not responses:
        print("❌ No responses found in database!")
        print("Run parse_and_import_new_format.py first.")
        return

    # Statistics
    total_chunks = 0
    total_cost = 0.0
    failed_chunks = 0

    # Process each response
    for idx, row in enumerate(responses, 1):
        response_id = row[0]
        response_data = {
            'response_id': response_id,
            'question_number': row[12],
            'tradition_name': row[13],
            'opening': row[4],
            'historical_development': row[5],
            'key_concepts': row[6],
            'core_arguments': row[7],
            'counter_arguments': row[8],
            'textual_foundation': row[9],
            'internal_variations': row[10],
            'contemporary_applications': row[11]
        }

        print(f"[{idx}/{len(responses)}] {response_data['tradition_name']} (Q{response_data['question_number']})...", end=' ')

        # Chunk the response
        chunks = chunk_response_by_sections(response_data)

        if not chunks:
            print("⚠️  No chunks generated")
            continue

        # Generate embeddings for each chunk
        chunk_count = 0
        for chunk in chunks:
            # Generate embedding
            embedding = get_embedding(chunk['text'])

            if embedding is not None:
                # Store in database
                cursor.execute("""
                    INSERT INTO embeddings
                    (response_id, chunk_text, chunk_index, section_type, embedding)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    response_id,
                    chunk['text'],
                    chunk['chunk_index'],
                    chunk['section_type'],
                    embedding.tobytes()  # Store as binary blob
                ))
                chunk_count += 1
                total_chunks += 1
            else:
                failed_chunks += 1

        conn.commit()

        # Estimate cost ($0.02 per 1000 tokens, ~750 tokens per chunk)
        chunk_cost = chunk_count * 0.00002
        total_cost += chunk_cost

        print(f"✅ {chunk_count} chunks (${chunk_cost:.5f})")

        # Rate limiting: small pause between responses
        time.sleep(0.1)

    conn.close()

    # Print summary
    print("\n" + "="*80)
    print("EMBEDDING GENERATION COMPLETE")
    print("="*80)
    print(f"Total responses processed: {len(responses)}")
    print(f"Total chunks embedded: {total_chunks}")
    print(f"Failed chunks: {failed_chunks}")
    print(f"Estimated cost: ${total_cost:.2f}")
    print(f"Database: {db_path}")
    print("="*80)

    # Verify embeddings
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n📊 Database verification:")
    print(f"   Embeddings stored: {embedding_count}")
    print(f"   Average chunks per response: {embedding_count / len(responses):.1f}")

if __name__ == '__main__':
    import sys

    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Create a .env file with your OpenAI API key:")
        print("OPENAI_API_KEY=your_key_here")
        sys.exit(1)

    # Optional: clear existing embeddings
    clear_existing = '--clear' in sys.argv

    if clear_existing:
        print("⚠️  WARNING: This will delete all existing embeddings!")
        response = input("Continue? (yes/no): ").strip().lower()
        if response != 'yes':
            print("❌ Cancelled")
            sys.exit(0)

    generate_all_embeddings(clear_existing=clear_existing)
