#!/usr/bin/env python3
"""
Parse other.html and split into individual books
Creates separate entries for each of the 21 books
"""

import json
import re
from bs4 import BeautifulSoup
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_other_individual(html_path: Path) -> dict:
    """Parse other.html and split into individual books"""

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    # Find all h2 headings (book titles)
    h2_headings = soup.find_all('h2')

    books = {}
    current_book = None
    current_content = []

    # Get all paragraphs
    all_elements = soup.find_all(['h2', 'h3', 'p'])

    for elem in all_elements:
        if elem.name == 'h2':
            # Save previous book if exists
            if current_book and current_content:
                books[current_book] = current_content

            # Start new book
            book_title = clean_text(elem.get_text())
            if book_title and book_title != "Table of Contents":
                current_book = book_title
                current_content = []

        elif elem.name == 'h3':
            # Chapter heading
            chapter = clean_text(elem.get_text())
            if chapter and chapter != "Table of Contents" and current_book:
                current_content.append({
                    'type': 'chapter',
                    'content': chapter
                })

        elif elem.name == 'p':
            # Paragraph content
            text = clean_text(elem.get_text())
            if text and current_book:
                current_content.append({
                    'type': 'paragraph',
                    'content': text
                })

    # Save last book
    if current_book and current_content:
        books[current_book] = current_content

    return books

def chunk_book(book_title: str, content: list, max_words: int = 500) -> list:
    """Create chunks from book content"""
    chunks = []
    current_chapter = ""
    current_chunk = []
    current_words = 0

    for item in content:
        if item['type'] == 'chapter':
            # Save previous chunk if exists
            if current_chunk:
                chunks.append({
                    'book': book_title,
                    'chapter': current_chapter,
                    'content': '\n\n'.join(current_chunk),
                    'chunk_index': len(chunks)
                })
                current_chunk = []
                current_words = 0

            current_chapter = item['content']

        elif item['type'] == 'paragraph':
            para = item['content']
            para_words = len(para.split())

            # If adding this would exceed max, save current chunk
            if current_words + para_words > max_words and current_chunk:
                chunks.append({
                    'book': book_title,
                    'chapter': current_chapter,
                    'content': '\n\n'.join(current_chunk),
                    'chunk_index': len(chunks)
                })
                current_chunk = []
                current_words = 0

            current_chunk.append(para)
            current_words += para_words

    # Save last chunk
    if current_chunk:
        chunks.append({
            'book': book_title,
            'chapter': current_chapter,
            'content': '\n\n'.join(current_chunk),
            'chunk_index': len(chunks)
        })

    return chunks

def create_book_code(book_title: str) -> str:
    """Create a short book code from title"""
    # Manual mappings for known books
    code_map = {
        'Sri Isopanisad - 1974 Edition': 'ISO',
        'The Nectar of Devotion - 1970 Edition': 'NOD',
        'The Nectar of Instruction': 'NOI',
        'Teachings of Lord Caitanya - 1968 Edition': 'TLC',
        'Perfect Questions, Perfect Answers': 'PQPA',
        'Beyond Birth and Death': 'BBD',
        'Easy Journey to Other Planets - 1972 Edition': 'EJOP',
        'Elevation to Krsna Consciousness': 'EKC',
        'Krsna Consciousness The Topmost Yoga System': 'KCTYS',
        'Krsna, the Reservoir of Pleasure': 'KRP',
        'Life Comes from Life': 'LCFL',
        'Light of the Bhagavata': 'LOB',
        'On the Way to Krsna': 'OWK',
        'Raja - Vidya: The King of Knowledge': 'RV',
        'Teachings of Lord Kapila, the Son of Devahuti': 'TLKD',
        'Teachings of Queen Kunti': 'TQK',
        'The Path of Perfection': 'POP',
        'The Perfection of Yoga': 'POY',
        'The Science of Self Realization': 'SSR',
        'Transcendental Teachings of Prahlada Maharaja': 'TTPM',
        'A Second Chance: The Story of a Near - Death Experience': 'SC'
    }

    return code_map.get(book_title, 'OTHER')

if __name__ == '__main__':
    print("=" * 80)
    print("PARSING OTHER.HTML - SPLITTING INTO INDIVIDUAL BOOKS")
    print("=" * 80)

    html_path = Path('/Users/jaganat/.emacs.d/git_projects/questions_answers/vedabase-source/other.html')

    if not html_path.exists():
        print(f"Error: {html_path} not found")
        exit(1)

    print(f"\nParsing {html_path}...")
    books = parse_other_individual(html_path)

    print(f"\nFound {len(books)} individual books")

    # Create chunks for each book
    all_books_data = {}
    total_chunks = 0

    for book_title, content in books.items():
        chunks = chunk_book(book_title, content)
        book_code = create_book_code(book_title)

        all_books_data[book_code] = {
            'title': book_title,
            'code': book_code,
            'chunks': chunks
        }

        total_chunks += len(chunks)
        print(f"  {book_code}: {book_title} - {len(chunks)} chunks")

    # Save to JSON
    output_file = 'other_individual_parsed.json'
    print(f"\nSaving to {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_books_data, f, ensure_ascii=False, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)
    print(f"  ✓ Saved {file_size:.2f} MB")

    print("\n" + "=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"  Individual books: {len(books)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Output file: {output_file}")
    print("=" * 80)
