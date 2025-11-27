#!/usr/bin/env python3
"""
Parse Krishna Book (kb.html)
Extracts chapters from Krishna Book HTML file
Since KB is a narrative book, we treat each chapter as a "verse" unit
"""
import json
from pathlib import Path
from bs4 import BeautifulSoup
import re

def parse_krishna_book(html_path: Path) -> list:
    """Parse Krishna Book HTML and extract chapters as verse units"""

    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    verses = []
    verse_id = 1

    # Find all chapter sections (h3 with ids)
    chapters = soup.find_all('h3', id=True)

    for chapter in chapters:
        chapter_id = chapter.get('id', '')
        chapter_title = chapter.get_text(strip=True)

        # Skip table of contents, intro, and other non-chapter headings
        if not chapter_title or 'Table of Contents' in chapter_title or 'Words from Apple' in chapter_title or 'Introduction' in chapter_title:
            continue

        # Skip if doesn't start with a number (not a chapter)
        if not re.match(r'^\d+\s*/', chapter_title):
            continue

        # Get the content - paragraphs are inside a div after the h3
        content_parts = []
        content_div = chapter.find_next_sibling('div')

        if content_div:
            # Find all paragraphs inside this div
            paragraphs = content_div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text:
                    content_parts.append(text)

        if content_parts:
            # Combine all paragraphs for this chapter
            full_content = '\n\n'.join(content_parts)

            verses.append({
                'chapter': chapter_title,
                'verse_number': str(verse_id),
                'sanskrit': '',  # KB doesn't have Sanskrit verses
                'synonyms': '',  # KB doesn't have synonyms
                'translation': '',  # KB is narrative, not translation
                'purport': full_content  # Store chapter content as purport
            })

            verse_id += 1

    return verses

def main():
    print("=" * 80)
    print("PARSING KRISHNA BOOK")
    print("=" * 80)

    current_dir = Path('.')
    kb_path = current_dir / 'kb.html'

    if not kb_path.exists():
        print(f"\nError: kb.html not found in {current_dir}")
        return

    print(f"\nParsing kb.html ({kb_path.stat().st_size / (1024*1024):.1f} MB)...")

    try:
        verses = parse_krishna_book(kb_path)
        print(f"  ✓ Found {len(verses)} chapters in Krishna Book")

        # Save to JSON
        output_file = 'kb_parsed.json'
        print(f"\nSaving to {output_file}...")

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'kb': verses
            }, f, indent=2, ensure_ascii=False)

        file_size = Path(output_file).stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved {file_size:.2f} MB")

        print("\n" + "=" * 80)
        print("PARSING COMPLETE")
        print("=" * 80)
        print(f"  Krishna Book chapters: {len(verses)}")
        print(f"  Output file: {output_file}")
        print("=" * 80)

    except Exception as e:
        print(f"  ✗ Error parsing kb.html: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
