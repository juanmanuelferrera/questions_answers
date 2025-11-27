#!/usr/bin/env python3
"""
RAG Query Interface for Philosophical Traditions

Retrieves relevant philosophical responses using semantic search
and synthesizes answers using Claude Sonnet 4.

Cost: ~$0.03 per query (embedding + Claude synthesis)
"""

import os
import sqlite3
import numpy as np
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
from typing import List, Dict
import argparse

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Configuration
EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_TOP_K = 8  # Number of chunks to retrieve

def get_query_embedding(query: str) -> np.ndarray:
    """Generate embedding for user query"""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"❌ Error generating query embedding: {e}")
        return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_relevant_chunks(
    query_embedding: np.ndarray,
    db_path: str = 'philosophical_traditions.db',
    top_k: int = DEFAULT_TOP_K,
    traditions_filter: List[str] = None
) -> List[Dict]:
    """
    Retrieve most relevant chunks using semantic search.

    Args:
        query_embedding: Query vector embedding
        db_path: Path to SQLite database
        top_k: Number of top chunks to retrieve
        traditions_filter: Optional list of tradition names to filter by

    Returns:
        List of chunk dictionaries with metadata and similarity scores
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build query with optional tradition filter
    query = """
        SELECT
            e.chunk_text, e.section_type, e.chunk_index, e.embedding,
            r.full_text, r.id as response_id,
            q.number as question_number, q.title as question_title,
            t.name as tradition_name, t.id as tradition_id
        FROM embeddings e
        JOIN responses r ON e.response_id = r.id
        JOIN questions q ON r.question_id = q.id
        JOIN traditions t ON r.tradition_id = t.id
    """

    params = []
    if traditions_filter:
        placeholders = ','.join('?' * len(traditions_filter))
        query += f" WHERE t.name IN ({placeholders})"
        params = traditions_filter

    cursor.execute(query, params)
    all_chunks = cursor.fetchall()

    if not all_chunks:
        print("❌ No embeddings found in database!")
        print("Run generate_embeddings.py first.")
        return []

    # Calculate similarities
    chunks_with_scores = []
    for row in all_chunks:
        # Deserialize embedding from binary blob
        stored_embedding = np.frombuffer(row[3], dtype=np.float32)

        # Calculate similarity
        similarity = cosine_similarity(query_embedding, stored_embedding)

        chunks_with_scores.append({
            'chunk_text': row[0],
            'section_type': row[1],
            'chunk_index': row[2],
            'similarity': similarity,
            'response_id': row[5],
            'question_number': row[6],
            'question_title': row[7],
            'tradition_name': row[8],
            'tradition_id': row[9]
        })

    conn.close()

    # Sort by similarity and return top_k
    chunks_with_scores.sort(key=lambda x: x['similarity'], reverse=True)
    return chunks_with_scores[:top_k]

def format_context_for_claude(chunks: List[Dict]) -> str:
    """Format retrieved chunks into context for Claude"""
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"**Source {i}: {chunk['tradition_name']} "
            f"(Q{chunk['question_number']}, {chunk['section_type'].replace('_', ' ').title()}) "
            f"[Relevance: {chunk['similarity']:.2f}]**\n\n"
            f"{chunk['chunk_text']}\n"
        )

    return "\n---\n\n".join(context_parts)

def synthesize_answer(query: str, context: str, chunks: List[Dict]) -> Dict:
    """Use Claude to synthesize answer from retrieved context"""

    # Get unique traditions mentioned
    traditions = sorted(set(c['tradition_name'] for c in chunks))

    prompt = f"""You are a philosophical research assistant. A user has asked the following question:

**QUESTION**: {query}

I have retrieved the most relevant passages from a database of philosophical responses across {len(traditions)} traditions. Please synthesize a comprehensive answer that:

1. Directly addresses the user's question
2. Draws on multiple philosophical perspectives from the sources
3. Highlights key agreements and disagreements between traditions
4. Uses specific concepts and arguments from the sources
5. Maintains scholarly accuracy and nuance

**RETRIEVED SOURCES**:

{context}

**SYNTHESIS GUIDELINES**:
- Begin with a direct answer to the question
- Reference specific traditions by name when presenting their views
- Compare and contrast different approaches
- Use technical terminology from the sources where appropriate
- Keep the answer comprehensive but concise (~400-600 words)
- End with a brief note on why these differences exist (e.g., different metaphysical assumptions)

Please provide your synthesis now."""

    try:
        message = anthropic_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        answer = message.content[0].text

        # Estimate cost
        input_tokens = len(prompt.split()) * 1.3
        output_tokens = len(answer.split()) * 1.3
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)

        return {
            'answer': answer,
            'cost': cost,
            'input_tokens': int(input_tokens),
            'output_tokens': int(output_tokens)
        }

    except Exception as e:
        print(f"❌ Error synthesizing answer: {e}")
        return None

def query_rag_system(
    question: str,
    db_path: str = 'philosophical_traditions.db',
    top_k: int = DEFAULT_TOP_K,
    traditions_filter: List[str] = None,
    verbose: bool = True
) -> Dict:
    """
    Complete RAG query pipeline.

    Args:
        question: User's philosophical question
        db_path: Path to SQLite database
        top_k: Number of relevant chunks to retrieve
        traditions_filter: Optional list of traditions to filter by
        verbose: Print detailed progress information

    Returns:
        Dictionary with answer, sources, and metadata
    """
    if verbose:
        print("="*80)
        print("RAG QUERY SYSTEM")
        print("="*80)
        print(f"Question: {question}")
        print(f"Retrieving top {top_k} relevant chunks...")
        if traditions_filter:
            print(f"Filtered to traditions: {', '.join(traditions_filter)}")
        print()

    # Step 1: Generate query embedding
    if verbose:
        print("🔍 Generating query embedding...", end=' ')

    query_embedding = get_query_embedding(question)
    if query_embedding is None:
        return None

    if verbose:
        print("✅")

    # Step 2: Retrieve relevant chunks
    if verbose:
        print("📚 Retrieving relevant passages...", end=' ')

    chunks = retrieve_relevant_chunks(
        query_embedding,
        db_path=db_path,
        top_k=top_k,
        traditions_filter=traditions_filter
    )

    if not chunks:
        return None

    if verbose:
        print(f"✅ Found {len(chunks)} chunks")
        print(f"\nTop sources:")
        for i, chunk in enumerate(chunks[:5], 1):
            print(f"  {i}. {chunk['tradition_name']} "
                  f"({chunk['section_type'].replace('_', ' ').title()}) "
                  f"- Similarity: {chunk['similarity']:.3f}")

    # Step 3: Format context
    context = format_context_for_claude(chunks)

    # Step 4: Synthesize answer with Claude
    if verbose:
        print("\n🤖 Synthesizing answer with Claude Sonnet 4...", end=' ')

    result = synthesize_answer(question, context, chunks)

    if result is None:
        return None

    if verbose:
        print(f"✅ (${result['cost']:.4f})")
        print("\n" + "="*80)
        print("ANSWER")
        print("="*80)
        print(result['answer'])
        print("\n" + "="*80)

        # Print source summary
        traditions = sorted(set(c['tradition_name'] for c in chunks))
        print(f"\nSources consulted: {len(chunks)} passages from {len(traditions)} traditions")
        print(f"Traditions: {', '.join(traditions)}")
        print(f"Query cost: ${result['cost']:.4f}")

    return {
        'answer': result['answer'],
        'sources': chunks,
        'traditions': sorted(set(c['tradition_name'] for c in chunks)),
        'cost': result['cost'],
        'input_tokens': result['input_tokens'],
        'output_tokens': result['output_tokens']
    }

def main():
    """Command-line interface for RAG queries"""
    parser = argparse.ArgumentParser(
        description='Query the philosophical traditions RAG system'
    )
    parser.add_argument(
        'question',
        type=str,
        help='Philosophical question to ask'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=DEFAULT_TOP_K,
        help=f'Number of chunks to retrieve (default: {DEFAULT_TOP_K})'
    )
    parser.add_argument(
        '--traditions',
        type=str,
        nargs='+',
        help='Filter by specific traditions (e.g., Catholic Buddhist Hindu)'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='philosophical_traditions.db',
        help='Path to database (default: philosophical_traditions.db)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Only print the answer, no metadata'
    )

    args = parser.parse_args()

    # Check for API keys
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found")
        print("Add to .env file: OPENAI_API_KEY=your_key_here")
        return

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ Error: ANTHROPIC_API_KEY not found")
        print("Add to .env file: ANTHROPIC_API_KEY=your_key_here")
        return

    # Run query
    result = query_rag_system(
        question=args.question,
        db_path=args.db,
        top_k=args.top_k,
        traditions_filter=args.traditions,
        verbose=not args.quiet
    )

    if result is None:
        print("❌ Query failed")
        return

    if args.quiet:
        print(result['answer'])

if __name__ == '__main__':
    main()
