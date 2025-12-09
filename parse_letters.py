#!/usr/bin/env python3
"""
Parse Srila Prabhupada's letters for RAG integration
"""

import json
from pathlib import Path

def parse_letters():
    """Parse letters JSON into RAG-compatible format"""

    source_file = Path('/Users/jaganat/.emacs.d/git_projects/siksamrta_app/letters_parsed.json')

    print("=" * 80)
    print("PARSING SRILA PRABHUPADA'S LETTERS FOR RAG")
    print("=" * 80)

    # Load source letters
    with open(source_file, 'r') as f:
        letters = json.load(f)

    print(f"\nLoaded {len(letters)} letters")
    print(f"Date range: {letters[0]['full_date']} to {letters[-1]['full_date']}")

    # Parse into book structure
    book = {
        'code': 'LETTERS',
        'name': "Srila Prabhupada's Letters",
        'chapters': []
    }

    # Group letters by year
    letters_by_year = {}
    for letter in letters:
        year = letter['year']
        if year not in letters_by_year:
            letters_by_year[year] = []
        letters_by_year[year].append(letter)

    print(f"\nGrouped into {len(letters_by_year)} years")

    # Create chapters (one per year) and chunks
    total_chunks = 0
    for year in sorted(letters_by_year.keys()):
        year_letters = letters_by_year[year]

        chapter = {
            'chapter_name': f"Letters {year}",
            'verses': []
        }

        for letter in year_letters:
            # Each letter is a "verse"
            verse = {
                'verse_number': letter['date_code'],
                'chapter': f"Letters {year}",
                'full_date': letter['full_date'],
                'recipient': letter['recipient'],
                'location': letter.get('location', ''),
                'chunks': []
            }

            # Split long letters into paragraphs for better chunking
            content = letter['content']
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

            # Create header chunk with metadata
            header_text = f"Letter to {letter['recipient']}\n{letter['full_date']}"
            if letter.get('location'):
                header_text += f"\n{letter['location']}"

            verse['chunks'].append({
                'chunk_type': 'letter_header',
                'content': header_text
            })

            # Add content chunks (group small paragraphs, split large ones)
            current_chunk = []
            current_length = 0
            max_chunk_size = 1000  # characters

            for para in paragraphs:
                para_length = len(para)

                # If paragraph itself is too long, make it its own chunk
                if para_length > max_chunk_size:
                    # Save current chunk if any
                    if current_chunk:
                        verse['chunks'].append({
                            'chunk_type': 'letter_content',
                            'content': '\n\n'.join(current_chunk)
                        })
                        current_chunk = []
                        current_length = 0

                    # Add large paragraph as single chunk
                    verse['chunks'].append({
                        'chunk_type': 'letter_content',
                        'content': para
                    })

                # If adding this para exceeds limit, save current and start new
                elif current_length + para_length > max_chunk_size:
                    verse['chunks'].append({
                        'chunk_type': 'letter_content',
                        'content': '\n\n'.join(current_chunk)
                    })
                    current_chunk = [para]
                    current_length = para_length

                # Otherwise add to current chunk
                else:
                    current_chunk.append(para)
                    current_length += para_length

            # Save remaining chunk
            if current_chunk:
                verse['chunks'].append({
                    'chunk_type': 'letter_content',
                    'content': '\n\n'.join(current_chunk)
                })

            total_chunks += len(verse['chunks'])
            chapter['verses'].append(verse)

        book['chapters'].append(chapter)

    # Save parsed data
    output_file = 'letters_parsed_for_rag.json'
    with open(output_file, 'w') as f:
        json.dump(book, f, indent=2)

    file_size = Path(output_file).stat().st_size / (1024 * 1024)

    print("\n" + "=" * 80)
    print("PARSING COMPLETE")
    print("=" * 80)
    print(f"  Total letters: {len(letters)}")
    print(f"  Years covered: {len(letters_by_year)}")
    print(f"  Total chunks: {total_chunks}")
    print(f"  Output file: {output_file} ({file_size:.2f} MB)")
    print("=" * 80)

if __name__ == '__main__':
    parse_letters()
