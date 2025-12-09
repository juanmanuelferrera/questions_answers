#!/usr/bin/env python3
"""
Srimad Bhagavatam Text Parser
Extracts verses, translations, and purports from plain text file
Parses Cantos 4-10 from srimad_bhagavatam.txt
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional

# Line numbers where each Canto's detailed content starts (Chapter One markers)
CANTO_START_LINES = {
    1: 1225,
    2: 30069,
    3: 46409,
    4: 96141,
    5: 151279,
    6: 176411,
    7: 207139,
    8: 236581,
    9: 267247,
    10: 296879
}

CANTO_NAMES = {
    4: "Srimad Bhagavatam Canto 4",
    5: "Srimad Bhagavatam Canto 5",
    6: "Srimad Bhagavatam Canto 6",
    7: "Srimad Bhagavatam Canto 7",
    8: "Srimad Bhagavatam Canto 8",
    9: "Srimad Bhagavatam Canto 9",
    10: "Srimad Bhagavatam Canto 10"
}

def clean_text(text: str) -> str:
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_verse(lines: List[str], start_idx: int, verse_num: int, chapter: int) -> Optional[Dict]:
    """Parse a single verse starting from TEXT marker"""
    i = start_idx

    # Find TEXT marker
    if not lines[i].strip().startswith('TEXT'):
        return None

    i += 1

    # Skip empty lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    if i >= len(lines):
        return None

    # Collect Sanskrit lines (until SYNONYMS)
    sanskrit_lines = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == 'SYNONYMS':
            i += 1
            break
        sanskrit_lines.append(line)
        i += 1

    # Skip empty lines after SYNONYMS
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Collect synonyms (until empty lines, then translation)
    synonyms_lines = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            # Check if we've hit the translation section (2+ empty lines typically)
            if i < len(lines) and not lines[i].strip():
                break
            continue
        synonyms_lines.append(line)
        i += 1

    # Skip empty lines
    while i < len(lines) and not lines[i].strip():
        i += 1

    # Collect translation AND purport (everything until next TEXT marker)
    # The first 1-2 paragraphs are translation, rest is purport
    all_content_lines = []
    empty_count = 0
    while i < len(lines):
        line = lines[i].strip()

        # Stop if we hit the next TEXT marker
        if line.startswith('TEXT'):
            break

        # Stop if we hit Chapter marker
        if line.startswith('Chapter'):
            break

        if not line:
            empty_count += 1
            i += 1
            # If we hit many empty lines, peek ahead
            if empty_count >= 5:
                j = i
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines) and (lines[j].strip().startswith('TEXT') or
                                      lines[j].strip().startswith('Chapter')):
                    break
            continue

        empty_count = 0
        all_content_lines.append(line)
        i += 1

    # Now split into translation (first 1-2 paragraphs) and purport (rest)
    # Translation is typically short (1-2 sentences), purport is longer
    translation_lines = []
    purport_lines = []

    if all_content_lines:
        # First paragraph is always translation
        if len(all_content_lines) > 0:
            translation_lines.append(all_content_lines[0])

        # If second paragraph is short (< 200 chars), it's also translation
        # Otherwise it's purport
        if len(all_content_lines) > 1:
            if len(all_content_lines[1]) < 200:
                translation_lines.append(all_content_lines[1])
                purport_lines = all_content_lines[2:]
            else:
                purport_lines = all_content_lines[1:]

    # Join the sections
    sanskrit = '\n'.join(sanskrit_lines).strip()
    synonyms = ' '.join(synonyms_lines).strip()
    translation = '\n\n'.join(translation_lines).strip()
    purport = '\n\n'.join(purport_lines).strip()

    # Only return if we have at least sanskrit and translation
    if not sanskrit or not translation:
        return None

    return {
        'sanskrit': sanskrit,
        'synonyms': synonyms,
        'translation': translation,
        'purport': purport,
        'next_index': i
    }

def parse_canto(file_path: Path, canto_num: int) -> List[Dict]:
    """Parse a specific canto from the text file"""
    print(f"\nParsing Canto {canto_num}...")

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Determine start and end lines for this canto
    start_line = CANTO_START_LINES[canto_num]

    # End is either the next canto or end of file
    if canto_num < 10:
        end_line = CANTO_START_LINES[canto_num + 1]
    else:
        end_line = len(lines)

    verses = []
    current_chapter = None
    current_chapter_title = None

    i = start_line
    while i < end_line:
        line = lines[i].strip()

        # Detect chapter markers
        if line.startswith('Chapter') and i + 4 < len(lines):
            # Extract chapter number
            chapter_match = re.match(r'Chapter\s+(\w+)', line)
            if chapter_match:
                chapter_word = chapter_match.group(1)
                # Convert word to number
                chapter_map = {
                    'One': 1, 'Two': 2, 'Three': 3, 'Four': 4, 'Five': 5,
                    'Six': 6, 'Seven': 7, 'Eight': 8, 'Nine': 9, 'Ten': 10,
                    'Eleven': 11, 'Twelve': 12, 'Thirteen': 13, 'Fourteen': 14,
                    'Fifteen': 15, 'Sixteen': 16, 'Seventeen': 17, 'Eighteen': 18,
                    'Nineteen': 19, 'Twenty': 20, 'Twenty-one': 21, 'Twenty-two': 22,
                    'Twenty-three': 23, 'Twenty-four': 24, 'Twenty-five': 25,
                    'Twenty-six': 26, 'Twenty-seven': 27, 'Twenty-eight': 28,
                    'Twenty-nine': 29, 'Thirty': 30, 'Thirty-one': 31
                }
                current_chapter = chapter_map.get(chapter_word, None)

                # Get chapter title (usually a few lines down)
                j = i + 1
                while j < min(i + 10, len(lines)):
                    title = lines[j].strip()
                    if title and title != 'Chapter' and not title.startswith('TEXT'):
                        current_chapter_title = title
                        break
                    j += 1

                if current_chapter:
                    print(f"  Chapter {current_chapter}: {current_chapter_title}")
            i += 1
            continue

        # Detect verse markers
        if line.startswith('TEXT'):
            # Extract verse number
            verse_match = re.match(r'TEXT\s+(\d+)', line)
            if verse_match and current_chapter:
                verse_num = int(verse_match.group(1))

                # Parse the verse
                verse_data = parse_verse(lines, i, verse_num, current_chapter)

                if verse_data:
                    verses.append({
                        'book_code': f'sb{canto_num}',
                        'book_name': CANTO_NAMES[canto_num],
                        'chapter': current_chapter,
                        'chapter_title': current_chapter_title,
                        'verse_number': verse_num,
                        'verse_text': f"SB {canto_num}.{current_chapter}.{verse_num}",
                        'sanskrit': verse_data['sanskrit'],
                        'synonyms': verse_data['synonyms'],
                        'translation': verse_data['translation'],
                        'purport': verse_data['purport']
                    })

                    i = verse_data['next_index']
                    continue

        i += 1

    print(f"  Parsed {len(verses)} verses from Canto {canto_num}")
    return verses

def main():
    """Parse Cantos 4-10 from the text file"""
    input_file = Path('vedabase-source/srimad_bhagavatam.txt')
    output_file = Path('sb_cantos_4_10_parsed.json')

    if not input_file.exists():
        print(f"Error: {input_file} not found")
        return

    print("=" * 80)
    print("PARSING SRIMAD BHAGAVATAM CANTOS 4-10")
    print("=" * 80)

    all_verses = []

    # Parse each canto
    for canto_num in range(4, 11):
        verses = parse_canto(input_file, canto_num)
        all_verses.extend(verses)

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_verses, f, indent=2, ensure_ascii=False)

    file_size = output_file.stat().st_size / (1024 * 1024)

    print("\n" + "=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"  Total verses parsed: {len(all_verses)}")
    print(f"  Output file: {output_file}")
    print(f"  File size: {file_size:.2f} MB")

    # Print summary by canto
    print("\nBreakdown by Canto:")
    for canto_num in range(4, 11):
        count = sum(1 for v in all_verses if v['book_code'] == f'sb{canto_num}')
        print(f"  Canto {canto_num}: {count} verses")

    print("=" * 80)

if __name__ == '__main__':
    main()
