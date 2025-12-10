#!/usr/bin/env python3
"""
Parse Conversations.epub HTML files and prepare for RAG
Extracts Room Conversations and Morning Walks
"""

import sqlite3
import re
from pathlib import Path
from bs4 import BeautifulSoup
import json

EPUB_DIR = "/Users/jaganat/.emacs.d/git_projects/questions_answers/Conversations.epub"
LOCAL_DB = ".wrangler/state/v3/d1/miniflare-D1DatabaseObject/3e3b090d-245a-42b9-a77b-cef0fca9db31.sqlite"
CONVERSATIONS_BOOK_ID = 45  # book_id for Conversations collection

def parse_conversation_html(html_path):
    """Parse a single conversation HTML file"""

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract title from <title> tag
    title_tag = soup.find('title')
    if not title_tag:
        return None

    title = title_tag.text.strip()

    # Extract conversation code
    code_div = soup.find('div', class_='Conv-code')
    code = None
    if code_div:
        code_span = code_div.find('span', class_='code')
        if code_span:
            code = code_span.text.strip()

    # Extract all paragraph content
    paragraphs = soup.find_all('div', class_='Purp-para')

    # Build full conversation text
    conversation_lines = []
    for para in paragraphs:
        # Get text with speaker formatting preserved
        text = para.get_text(separator=' ', strip=True)
        if text:
            conversation_lines.append(text)

    full_text = '\n\n'.join(conversation_lines)

    # Determine conversation type
    if 'Morning Walk' in title:
        conv_type = 'morning_walk'
    elif 'Room Conversation' in title:
        conv_type = 'room_conversation'
    else:
        conv_type = 'conversation'

    return {
        'title': title,
        'code': code,
        'type': conv_type,
        'content': full_text,
        'word_count': len(full_text.split())
    }

def chunk_conversation(conversation, max_words=500):
    """
    Chunk conversation into manageable segments
    Try to preserve speaker turns when possible
    """

    lines = conversation['content'].split('\n\n')
    chunks = []
    current_chunk = []
    current_word_count = 0
    chunk_index = 0

    for line in lines:
        line_words = len(line.split())

        # If adding this line would exceed max_words, save current chunk
        if current_word_count + line_words > max_words and current_chunk:
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                'chunk_index': chunk_index,
                'content': chunk_text,
                'word_count': current_word_count
            })
            chunk_index += 1
            current_chunk = []
            current_word_count = 0

        current_chunk.append(line)
        current_word_count += line_words

    # Add final chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append({
            'chunk_index': chunk_index,
            'content': chunk_text,
            'word_count': current_word_count
        })

    return chunks

def main():
    print("=" * 80)
    print("PARSING CONVERSATIONS FROM EPUB")
    print("=" * 80)
    print()

    # Find all section HTML files
    epub_path = Path(EPUB_DIR)
    section_files = sorted(epub_path.glob('section_*.html'))

    print(f"Found {len(section_files)} section files")
    print()

    all_conversations = []
    morning_walks = 0
    room_conversations = 0
    other = 0

    # Parse each file
    for section_file in section_files:
        conv = parse_conversation_html(section_file)
        if conv:
            all_conversations.append(conv)

            if conv['type'] == 'morning_walk':
                morning_walks += 1
            elif conv['type'] == 'room_conversation':
                room_conversations += 1
            else:
                other += 1

    print(f"✅ Parsed {len(all_conversations)} conversations:")
    print(f"   Morning Walks: {morning_walks}")
    print(f"   Room Conversations: {room_conversations}")
    print(f"   Other: {other}")
    print()

    # Connect to database and get next available verse_id
    conn = sqlite3.connect(LOCAL_DB)
    cursor = conn.cursor()

    cursor.execute("SELECT MAX(id) FROM vedabase_verses")
    max_verse_id = cursor.fetchone()[0]
    next_verse_id = max_verse_id + 1

    print(f"📊 Next available verse_id: {next_verse_id}")
    print()

    # Create verse entries and chunk conversations
    all_chunks = []
    verse_entries = []
    total_chunks = 0

    for i, conv in enumerate(all_conversations):
        verse_id = next_verse_id + i

        # Create verse entry (using conversations as "verses" for reference)
        verse_entries.append({
            'id': verse_id,
            'book_id': CONVERSATIONS_BOOK_ID,
            'chapter': conv['type'],
            'verse_number': conv['code'] or f"conv_{i}",
            'sanskrit': None,
            'synonyms': None,
            'translation': conv['title'],
            'created_at': None
        })

        # Chunk the conversation
        chunks = chunk_conversation(conv, max_words=500)

        for chunk in chunks:
            all_chunks.append({
                'verse_id': verse_id,
                'chunk_type': f"{conv['type']}_segment",
                'chunk_index': chunk['chunk_index'],
                'content': chunk['content'],
                'word_count': chunk['word_count']
            })
            total_chunks += 1

    print(f"📦 Generated {total_chunks} chunks from {len(all_conversations)} conversations")
    print()

    # Save to JSON for review
    output = {
        'verse_entries': verse_entries,
        'chunks': all_chunks,
        'stats': {
            'total_conversations': len(all_conversations),
            'morning_walks': morning_walks,
            'room_conversations': room_conversations,
            'other': other,
            'total_chunks': total_chunks,
            'next_verse_id': next_verse_id
        }
    }

    output_file = 'conversations_parsed.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Saved parsed data to {output_file}")
    print()

    # Insert into local database
    print("📥 Inserting into local database...")

    # Insert verses
    for verse in verse_entries:
        cursor.execute("""
            INSERT INTO vedabase_verses (id, book_id, chapter, verse_number, sanskrit, synonyms, translation, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            verse['id'],
            verse['book_id'],
            verse['chapter'],
            verse['verse_number'],
            verse['sanskrit'],
            verse['synonyms'],
            verse['translation'],
            verse['created_at']
        ))

    # Insert chunks
    for chunk in all_chunks:
        cursor.execute("""
            INSERT INTO vedabase_chunks (verse_id, chunk_type, chunk_index, content, word_count)
            VALUES (?, ?, ?, ?, ?)
        """, (
            chunk['verse_id'],
            chunk['chunk_type'],
            chunk['chunk_index'],
            chunk['content'],
            chunk['word_count']
        ))

    conn.commit()
    conn.close()

    print(f"✅ Inserted {len(verse_entries)} verse entries")
    print(f"✅ Inserted {len(all_chunks)} chunks")
    print()

    print("=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"Total conversations: {len(all_conversations)}")
    print(f"Total chunks: {total_chunks}")
    print(f"Average chunks per conversation: {total_chunks / len(all_conversations):.1f}")
    print()
    print("Next steps:")
    print("1. Generate embeddings for conversation chunks")
    print("2. Upload conversation verses to remote D1")
    print("3. Upload conversation chunks to remote D1")
    print("4. Upload embeddings to Vectorize")

if __name__ == '__main__':
    main()
