#!/usr/bin/env python3
"""
RAG System - Streamlit Web Interface

Beautiful web interface for querying philosophical traditions.
Run with: streamlit run streamlit_app.py
"""

import os
import sqlite3
import numpy as np
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import streamlit as st
from typing import List, Dict

load_dotenv()

# Initialize API clients
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
anthropic_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

EMBEDDING_MODEL = "text-embedding-3-small"
CLAUDE_MODEL = "claude-sonnet-4-20250514"
DEFAULT_TOP_K = 8
DB_PATH = 'philosophical_traditions_sample.db'

# Page config
st.set_page_config(
    page_title="Universal Philosophy Reservoir",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .source-card {
        background-color: #f9fafb;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.5rem;
    }
    .similarity-score {
        display: inline-block;
        background-color: #dbeafe;
        color: #1e40af;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        font-weight: 600;
    }
    .synthesis-box {
        background-color: #fefce8;
        border: 2px solid #fbbf24;
        padding: 1.5rem;
        border-radius: 0.75rem;
        margin: 1.5rem 0;
    }
    .cost-badge {
        color: #059669;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

def get_query_embedding(query: str) -> np.ndarray:
    """Generate embedding for user query"""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=query
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        st.error(f"❌ Error generating query embedding: {e}")
        return None

def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def retrieve_relevant_chunks(
    query_embedding: np.ndarray,
    db_path: str = DB_PATH,
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

def format_sources_display(chunks: List[Dict]) -> str:
    """Format sources for context prompt"""
    context_parts = []

    for i, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"**Source {i}: {chunk['tradition_name']} "
            f"(Q{chunk['question_number']}, {chunk['section_type'].replace('_', ' ').title()}) "
            f"[Similarity: {chunk['similarity']:.3f}]**\n\n"
            f"{chunk['chunk_text']}\n"
        )

    return "\n" + "="*80 + "\n\n".join(context_parts)

def synthesize_answer(question: str, chunks: List[Dict], word_limit: int = 400) -> str:
    """Synthesize answer using OpenAI GPT-4 based on retrieved sources"""

    # Format context
    context = format_sources_display(chunks)

    # Create prompt with strict word limit
    prompt = f"""Based on the philosophical sources below, synthesize an answer to the question.

QUESTION: {question}

SOURCES:
{context}

CRITICAL REQUIREMENT: Your response MUST be EXACTLY {word_limit} words or fewer. This is a strict limit.

Please create a synthesis that:
1. Directly answers the question
2. Integrates multiple philosophical perspectives from the sources
3. Highlights agreements and disagreements between traditions
4. Uses specific concepts and arguments from the sources
5. Maintains academic precision and nuance

WORD LIMIT: {word_limit} words maximum. Count carefully and stop at {word_limit} words."""

    try:
        # Call OpenAI GPT-4
        # Adjust max_tokens based on word limit (roughly 1.3 tokens per word)
        max_tokens = int(word_limit * 1.5)

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": f"You are an expert in comparative philosophy. CRITICAL: Always respect the word limit strictly. Your responses must not exceed {word_limit} words."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Error generating synthesis: {e}"

# ============================================================================
# STREAMLIT UI
# ============================================================================

# Header
st.markdown('<div class="main-header">🏛️ Universal Philosophy Reservoir</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">RAG-Powered Philosophical Knowledge System</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")

    top_k = st.slider(
        "Number of sources to retrieve",
        min_value=3,
        max_value=15,
        value=8,
        help="More sources = more comprehensive but longer context"
    )

    word_limit = st.select_slider(
        "Answer length (words)",
        options=[30, 50, 100, 200, 400, 600, 800],
        value=400,
        help="Target word count for synthesized answer"
    )

    st.divider()

    st.header("📊 System Stats")

    # Get database stats
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM responses")
    response_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT tradition_id) FROM responses")
    tradition_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM embeddings")
    embedding_count = cursor.fetchone()[0]
    conn.close()

    st.metric("Responses", f"{response_count:,}")
    st.metric("Traditions", f"{tradition_count:,}")
    st.metric("Embeddings", f"{embedding_count:,}")

    st.divider()

    st.header("💡 Example Queries")
    st.markdown("""
    - What is śūnyatā in Mahayana Buddhism?
    - How do different traditions understand time?
    - What is the nature of consciousness?
    - Explain the concept of God in monotheism
    """)

    st.divider()
    st.markdown("**Cost per query:** ~$0.01")
    st.markdown("**Embeddings:** text-embedding-3-small")
    st.markdown("**Synthesis:** GPT-4o")

# Main content
query = st.text_input(
    "🔍 Enter your philosophical question:",
    placeholder="e.g., What is the difference between Thomism and Buddhism?",
    help="Ask any philosophical question about concepts, traditions, or comparisons"
)

if st.button("Search", type="primary", use_container_width=True) or query:
    if not query:
        st.warning("⚠️ Please enter a question")
    else:
        with st.spinner("🔍 Generating query embedding..."):
            query_embedding = get_query_embedding(query)

        if query_embedding is not None:
            with st.spinner("📚 Searching relevant sources..."):
                chunks = retrieve_relevant_chunks(
                    query_embedding,
                    db_path=DB_PATH,
                    top_k=top_k
                )

            if chunks:
                # Automatic Synthesis with OpenAI (shown first)
                st.header("🤖 Answer")

                with st.spinner(f"✨ Generating {word_limit}-word answer with GPT-4..."):
                    synthesis = synthesize_answer(query, chunks, word_limit)

                # Display synthesis in a nice box with copy button
                st.markdown(f"""
                <div style='background-color: #fefce8; border: 2px solid #fbbf24; padding: 1.5rem; border-radius: 0.75rem; margin: 1.5rem 0;'>
                {synthesis}
                </div>
                """, unsafe_allow_html=True)

                # Copy button for synthesis
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("📋 Copy Answer", key="copy_synthesis"):
                        st.code(synthesis, language="text")
                        st.success("✅ Answer copied to clipboard!")
                with col2:
                    # Word count
                    word_count = len(synthesis.split())
                    st.caption(f"Words: {word_count}")

                st.divider()

                # Display statistics (below the answer)
                traditions = sorted(set(c['tradition_name'] for c in chunks))
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Sources Found", len(chunks))
                with col2:
                    st.metric("Traditions", len(traditions))
                with col3:
                    st.metric("Cost", "~$0.01")

                st.divider()

                # Display sources (collapsible)
                with st.expander("📖 View Retrieved Sources", expanded=False):
                    # Copy all sources button
                    if st.button("📋 Copy All Sources", key="copy_all_sources"):
                        all_sources_text = f"Query: {query}\n\n" + "="*80 + "\n\n"
                        for i, chunk in enumerate(chunks, 1):
                            all_sources_text += f"Source {i}: {chunk['tradition_name']} ({chunk['section_type'].replace('_', ' ').title()})\n"
                            all_sources_text += f"Similarity: {chunk['similarity']:.3f}\n"
                            all_sources_text += f"Question {chunk['question_number']}: {chunk['question_title']}\n\n"
                            all_sources_text += f"{chunk['chunk_text']}\n\n"
                            all_sources_text += "="*80 + "\n\n"
                        st.code(all_sources_text, language="text")
                        st.success("✅ All sources copied!")

                    st.divider()

                    for i, chunk in enumerate(chunks, 1):
                        st.markdown(f"**{i}. {chunk['tradition_name']}** ({chunk['section_type'].replace('_', ' ').title()}) • Similarity: {chunk['similarity']:.3f}")
                        st.markdown(f"<div class='source-card'>{chunk['chunk_text']}</div>", unsafe_allow_html=True)
                        st.caption(f"Question {chunk['question_number']} • {chunk['section_type']}")

                        # Copy button for this source
                        if st.button(f"📋 Copy Source {i}", key=f"copy_source_{i}"):
                            source_text = f"**{chunk['tradition_name']}** ({chunk['section_type'].replace('_', ' ').title()})\n\n{chunk['chunk_text']}\n\nQuestion {chunk['question_number']}: {chunk['question_title']}"
                            st.code(source_text, language="text")
                            st.success(f"✅ Source {i} copied!")

                        if i < len(chunks):
                            st.markdown("---")

                # Traditions list
                st.divider()
                st.subheader("🌍 Traditions Consulted")
                st.write(", ".join(traditions))

                # Optional: Show raw context in expander
                st.divider()
                with st.expander("📋 View Raw Sources Context", expanded=False):
                    context = format_sources_display(chunks)
                    st.code(context, language="markdown")

            else:
                st.error("❌ No relevant sources found. Try rephrasing your question.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #6b7280; font-size: 0.875rem;'>
    Powered by OpenAI (text-embedding-3-small + GPT-4o) • RAG System v1.0
</div>
""", unsafe_allow_html=True)
