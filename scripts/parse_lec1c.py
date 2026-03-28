#!/usr/bin/env python3
"""
Parse Lectures Part 1C (lec1c.html)
This file has a different structure with 3-line headers:
1. ID code
2. Scripture reference (with accented characters)
3. Location and date
"""

import re
import json
from bs4 import BeautifulSoup
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_lec1c(html_path: Path) -> list:
    """Parse LEC1C with its unique structure"""

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    lectures = []
    paras = soup.find_all('p')

    # Pattern for ID codes like "721102SB.VRN"
    id_pattern = re.compile(r'^\d{6}[A-Z]{2}\.[A-Z]{2,5}$')

    # Pattern for scripture references (with or without accents)
    scripture_pattern = re.compile(r'^(Śrīmad-Bhāgavatam|Bhagavad-gītā|Bhagavad-gita|Caitanya-caritāmṛta|Nectar|Sri Isopanisad)\s+', re.IGNORECASE)

    i = 0
    while i < len(paras):
        text = clean_text(paras[i].get_text())

        # Check if this is an ID code (start of lecture)
        if id_pattern.match(text):
            # Next should be scripture reference
            if i + 1 < len(paras):
                scripture = clean_text(paras[i + 1].get_text())

                # Check if it's a scripture reference
                if scripture_pattern.match(scripture):
                    # Next should be location and date
                    location = ""
                    if i + 2 < len(paras):
                        location = clean_text(paras[i + 2].get_text())

                    # Create lecture title
                    lecture_title = f"{scripture} – {location}" if location else scripture

                    # Collect lecture content until next ID code
                    content = []
                    j = i + 3
                    while j < len(paras):
                        next_text = clean_text(paras[j].get_text())

                        # Stop if we hit another ID code
                        if id_pattern.match(next_text):
                            break

                        # Skip empty, table of contents, and metadata
                        if (next_text and
                            next_text not in ['Table of Contents', 'LECTURES PART 1 of 2'] and
                            'His Divine Grace' not in next_text and
                            'A.C. Bhaktivedanta Swami' not in next_text):
                            content.append(next_text)

                        j += 1

                    # Save lecture if we have content
                    if content:
                        lectures.append({
                            'id_code': text,
                            'lecture_title': lecture_title,
                            'content': '\n\n'.join(content),
                            'word_count': sum(len(c.split()) for c in content)
                        })

                    # Move to next lecture
                    i = j
                    continue

        i += 1

    return lectures

def chunk_lecture(lecture: dict, max_words: int = 500) -> list:
    """Break a lecture into smaller chunks for RAG"""
    content = lecture['content']
    paragraphs = content.split('\n\n')

    chunks = []
    current_chunk = []
    current_words = 0

    for para in paragraphs:
        para_words = len(para.split())

        if current_words + para_words > max_words and current_chunk:
            chunks.append({
                'book': 'Lectures Part 1C',
                'lecture_title': lecture['lecture_title'],
                'content': '\n\n'.join(current_chunk),
                'chunk_index': len(chunks)
            })
            current_chunk = []
            current_words = 0

        current_chunk.append(para)
        current_words += para_words

    if current_chunk:
        chunks.append({
            'book': 'Lectures Part 1C',
            'lecture_title': lecture['lecture_title'],
            'content': '\n\n'.join(current_chunk),
            'chunk_index': len(chunks)
        })

    return chunks

if __name__ == '__main__':
    print("=" * 80)
    print("PARSING LECTURES PART 1C")
    print("=" * 80)

    file_path = Path('lec1c.html')

    if not file_path.exists():
        print(f"Error: {file_path} not found")
        exit(1)

    print(f"\nParsing {file_path} ({file_path.stat().st_size / (1024*1024):.1f} MB)...")

    lectures = parse_lec1c(file_path)
    print(f"  Found {len(lectures)} lectures")

    # Create chunks
    all_chunks = []
    for lecture in lectures:
        chunks = chunk_lecture(lecture)
        all_chunks.extend(chunks)

    print(f"  Created {len(all_chunks)} chunks")

    # Load existing lectures_parsed.json
    output_file = Path('lectures_parsed.json')
    if output_file.exists():
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    # Add lec1c
    data['lec1c'] = all_chunks

    # Save
    print(f"\nSaving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"  LEC1C lectures: {len(lectures)}")
    print(f"  LEC1C chunks: {len(all_chunks)}")
    print(f"  Total chunks in file: {sum(len(v) for v in data.values())}")
    print("=" * 80)
