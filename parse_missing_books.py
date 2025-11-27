#!/usr/bin/env python3
"""
Parse missing Vedabase books: CC1, CC2, CC3, and LEC1C
Combines both Vedabase parser for CC books and Lecture parser for LEC1C
"""

import json
import sys
from pathlib import Path

# Import parsing functions
sys.path.insert(0, str(Path(__file__).parent))
from parse_vedabase import parse_caitanya_caritamrta
from parse_lectures import parse_lectures

def main():
    print("=" * 80)
    print("PARSING MISSING VEDABASE BOOKS")
    print("=" * 80)

    current_dir = Path('.')
    all_new_books = {}

    # Parse Caitanya Caritamrita (CC1, CC2, CC3)
    print("\n1. Parsing Caitanya Caritamrita volumes...")
    for volume in [1, 2, 3]:
        cc_path = current_dir / f'cc{volume}.html'
        if cc_path.exists():
            print(f"\n  Parsing cc{volume}.html...")
            try:
                verses = parse_caitanya_caritamrta(cc_path, str(volume))
                all_new_books[f'cc{volume}'] = verses
                print(f"  ✓ Found {len(verses)} verses in CC{volume}")
            except Exception as e:
                print(f"  ✗ Error parsing cc{volume}.html: {e}")
        else:
            print(f"  ✗ File not found: cc{volume}.html")

    # Parse LEC1C lectures
    print("\n2. Parsing Lectures Part 1C...")
    lec1c_path = current_dir / 'lec1c.html'
    if lec1c_path.exists():
        print(f"\n  Parsing lec1c.html...")
        try:
            lectures = parse_lectures(lec1c_path, 'Lectures Part 1C')
            all_new_books['lec1c'] = lectures
            print(f"  ✓ Found {len(lectures)} lecture sections in LEC1C")
        except Exception as e:
            print(f"  ✗ Error parsing lec1c.html: {e}")
    else:
        print(f"  ✗ File not found: lec1c.html")

    # Save results
    if all_new_books:
        output_file = Path('missing_books_parsed.json')
        print(f"\n3. Saving parsed data to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_new_books, f, ensure_ascii=False, indent=2)

        # Print summary
        print("\n" + "=" * 80)
        print("PARSING COMPLETE")
        print("=" * 80)
        for book_code, content in all_new_books.items():
            print(f"  {book_code.upper()}: {len(content)} sections")

        total = sum(len(content) for content in all_new_books.values())
        print(f"\nTotal sections parsed: {total}")
        print(f"Saved to: {output_file}")
        print("=" * 80)
    else:
        print("\n✗ No books were successfully parsed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
