#!/usr/bin/env python3
"""
RAG Query Interface - Manual Synthesis Version

Retrieves relevant chunks using OpenAI embeddings,
then prints them for manual synthesis with Claude Code.

This version doesn't use the Anthropic API, so it works
with Claude Code Max subscription instead.
"""

import os
import sqlite3
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict
import argparse

load_dotenv()

openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_TOP_K = 8

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
    db_path: str = 'philosophical_traditions_sample.db',
    top_k: int = DEFAULT_TOP_K,
    traditions_filter: List[str] = None
) -> List[Dict]:
    """Retrieve most relevant chunks using semantic search"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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
        return []

    # Calculate similarities
    chunks_with_scores = []
    for row in all_chunks:
        stored_embedding = np.frombuffer(row[3], dtype=np.float32)
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

def format_context_for_display(chunks: List[Dict]) -> str:
    """Format retrieved chunks for display"""
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"**Fuente {i}: {chunk['tradition_name']} "
            f"(Q{chunk['question_number']}, {chunk['section_type'].replace('_', ' ').title()}) "
            f"[Relevancia: {chunk['similarity']:.3f}]**\n\n"
            f"{chunk['chunk_text']}\n"
        )

    return "\n" + "="*80 + "\n\n".join(context_parts)

def query_rag_retrieval(
    question: str,
    db_path: str = 'philosophical_traditions_sample.db',
    top_k: int = DEFAULT_TOP_K,
    traditions_filter: List[str] = None
):
    """
    RAG retrieval without synthesis.
    Prints context for manual synthesis with Claude Code.
    """

    print("="*80)
    print("RAG QUERY SYSTEM (Manual Synthesis)")
    print("="*80)
    print(f"Pregunta: {question}")
    print(f"Recuperando top {top_k} chunks relevantes...")
    if traditions_filter:
        print(f"Filtrado a tradiciones: {', '.join(traditions_filter)}")
    print()

    # Step 1: Generate query embedding
    print("🔍 Generando embedding de la pregunta...", end=' ')
    query_embedding = get_query_embedding(question)
    if query_embedding is None:
        return None
    print("✅")

    # Step 2: Retrieve relevant chunks
    print("📚 Buscando pasajes relevantes...", end=' ')
    chunks = retrieve_relevant_chunks(
        query_embedding,
        db_path=db_path,
        top_k=top_k,
        traditions_filter=traditions_filter
    )

    if not chunks:
        return None

    print(f"✅ Encontrados {len(chunks)} chunks")

    # Step 3: Display results
    print("\n" + "="*80)
    print("TOP FUENTES ENCONTRADAS:")
    print("="*80)

    for i, chunk in enumerate(chunks, 1):
        print(f"\n{i}. {chunk['tradition_name']} "
              f"({chunk['section_type'].replace('_', ' ').title()}) "
              f"- Similitud: {chunk['similarity']:.3f}")

    print("\n" + "="*80)
    print("CONTEXTO COMPLETO PARA SÍNTESIS:")
    print("="*80)

    context = format_context_for_display(chunks)
    print(context)

    print("\n" + "="*80)
    print("PROMPT PARA CLAUDE CODE:")
    print("="*80)

    prompt = f"""Basándote en las fuentes filosóficas anteriores, sintetiza una respuesta comprehensiva a la siguiente pregunta:

**PREGUNTA**: {question}

Por favor, crea una síntesis que:
1. Responda directamente a la pregunta
2. Integre múltiples perspectivas filosóficas de las fuentes
3. Destaque acuerdos y desacuerdos entre tradiciones
4. Use conceptos y argumentos específicos de las fuentes
5. Mantenga precisión académica y matiz

Responde de manera estructurada y comprehensiva (~400-600 palabras)."""

    print(prompt)
    print("\n" + "="*80)

    # Summary
    traditions = sorted(set(c['tradition_name'] for c in chunks))
    print(f"\n✅ Fuentes consultadas: {len(chunks)} pasajes de {len(traditions)} tradiciones")
    print(f"📖 Tradiciones: {', '.join(traditions)}")
    print(f"💰 Costo: $0.00002 (solo embedding, síntesis gratis con Claude Code Max)")

    return {
        'question': question,
        'chunks': chunks,
        'traditions': traditions,
        'context': context,
        'prompt': prompt
    }

def main():
    """Command-line interface"""
    parser = argparse.ArgumentParser(
        description='Query RAG system (retrieval only, manual synthesis)'
    )
    parser.add_argument(
        'question',
        type=str,
        help='Pregunta filosófica'
    )
    parser.add_argument(
        '--top-k',
        type=int,
        default=DEFAULT_TOP_K,
        help=f'Número de chunks a recuperar (default: {DEFAULT_TOP_K})'
    )
    parser.add_argument(
        '--traditions',
        type=str,
        nargs='+',
        help='Filtrar por tradiciones específicas'
    )
    parser.add_argument(
        '--db',
        type=str,
        default='philosophical_traditions_sample.db',
        help='Path a la base de datos'
    )

    args = parser.parse_args()

    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ Error: OPENAI_API_KEY not found")
        print("Add to .env file: OPENAI_API_KEY=your_key_here")
        return

    # Run retrieval
    result = query_rag_retrieval(
        question=args.question,
        db_path=args.db,
        top_k=args.top_k,
        traditions_filter=args.traditions
    )

    if result is None:
        print("❌ Query failed")

if __name__ == '__main__':
    main()
