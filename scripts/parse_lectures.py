#!/usr/bin/env python3
"""
Parse Vedabase Lecture files
Lectures are structured differently - they're continuous text divided by lecture titles
"""

import re
import json
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_lectures(html_path: Path, book_name: str) -> List[Dict]:
    """
    Parse lecture HTML files
    Structure: Continuous paragraphs with lecture titles as markers
    """
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    lectures = []
    all_paras = soup.find_all('p')

    # Pattern to identify lecture titles (e.g., "Bhagavad-gita 1.1 – London, July 7, 1973")
    lecture_pattern = re.compile(r'^(Bhagavad-gita|Srimad-Bhagavatam|Caitanya-caritamrta|Nectar|Sri Isopanisad|Teachings|Mukunda-mala-stotra|Morning Walk|Room Conversation|Lecture|Festival Lecture)\s+(.+)$')

    current_lecture = None
    current_text = []

    for para in all_paras:
        text = clean_text(para.get_text())

        if not text:
            continue

        # Skip table of contents and headers
        if text in ['Table of Contents', 'LECTURES PART 1 of 2', 'LECTURES PART 2 of 2']:
            continue

        # Skip author info
        if 'His Divine Grace' in text or 'A.C. Bhaktivedanta Swami' in text:
            continue

        # Check if this is a lecture title
        match = lecture_pattern.match(text)

        if match or (len(text) > 20 and ' – ' in text and any(x in text for x in ['19', '20'])):  # Likely a lecture title with date
            # Save previous lecture if exists
            if current_lecture and current_text:
                lectures.append({
                    'book': book_name,
                    'lecture_title': current_lecture,
                    'content': '\n\n'.join(current_text),
                    'word_count': sum(len(t.split()) for t in current_text)
                })

            # Start new lecture
            current_lecture = text
            current_text = []
        else:
            # Add content to current lecture
            if current_lecture:
                current_text.append(text)

    # Save last lecture
    if current_lecture and current_text:
        lectures.append({
            'book': book_name,
            'lecture_title': current_lecture,
            'content': '\n\n'.join(current_text),
            'word_count': sum(len(t.split()) for t in current_text)
        })

    return lectures

def parse_other(html_path: Path) -> List[Dict]:
    """
    Parse 'other.html' which contains various shorter texts
    Similar structure to lectures but may have different patterns
    """
    return parse_lectures(html_path, 'Other Vedic Texts')

def chunk_lecture(lecture: Dict, max_words: int = 500) -> List[Dict]:
    """
    Break a lecture into smaller chunks for RAG
    """
    content = lecture['content']
    paragraphs = content.split('\n\n')

    chunks = []
    current_chunk = []
    current_words = 0

    for para in paragraphs:
        para_words = len(para.split())

        # If adding this paragraph would exceed max_words, save current chunk
        if current_words + para_words > max_words and current_chunk:
            chunks.append({
                'book': lecture['book'],
                'lecture_title': lecture['lecture_title'],
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
            'book': lecture['book'],
            'lecture_title': lecture['lecture_title'],
            'content': '\n\n'.join(current_chunk),
            'chunk_index': len(chunks)
        })

    return chunks

if __name__ == '__main__':
    # Parse all lecture files
    lecture_files = {
        'lec1a': 'Lectures Part 1A',
        'lec1b': 'Lectures Part 1B',
        'lec1c': 'Lectures Part 1C',
        'lec2a': 'Lectures Part 2A',
        'lec2b': 'Lectures Part 2B',
        'lec2c': 'Lectures Part 2C'
    }

    all_lectures = {}

    for file_key, book_name in lecture_files.items():
        file_path = Path(f'{file_key}.html')
        if file_path.exists():
            print(f"Parsing {book_name}...")
            lectures = parse_lectures(file_path, book_name)

            # Create chunks
            all_chunks = []
            for lecture in lectures:
                chunks = chunk_lecture(lecture)
                all_chunks.extend(chunks)

            all_lectures[file_key] = all_chunks
            print(f"  Found {len(lectures)} lectures, created {len(all_chunks)} chunks")

    # Parse other.html
    other_path = Path('other.html')
    if other_path.exists():
        print("Parsing other.html...")
        other_lectures = parse_other(other_path)
        other_chunks = []
        for lecture in other_lectures:
            chunks = chunk_lecture(lecture)
            other_chunks.extend(chunks)
        all_lectures['other'] = other_chunks
        print(f"  Found {len(other_lectures)} sections, created {len(other_chunks)} chunks")

    # Save to JSON
    output_file = Path('lectures_parsed.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_lectures, f, ensure_ascii=False, indent=2)

    # Print summary
    total_chunks = sum(len(chunks) for chunks in all_lectures.values())
    print(f"\nTotal chunks created: {total_chunks}")
    print(f"Saved to: {output_file}")
