#!/usr/bin/env python3
# parse_and_import_new_format.py
"""
Parse NEW format philosophical responses (8 sections with headers)
and import into SQLite database for RAG system.

NEW Format:
- Opening paragraph (no header)
- **Historical Development:**
- **Key Concepts:**
- **Core Arguments:**
- **Counter-Arguments:**
- **Textual Foundation:**
- **Internal Variations:**
- **Contemporary Applications:**
"""

import re
import sqlite3
from pathlib import Path
from typing import Dict, List

def parse_new_format_file(filepath: Path) -> List[Dict]:
    """Extract structured data from new format .txt files"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for new format: *** 1.24.1 Catholic Response
    pattern = r'\*\*\* (\d+\.\d+)\.(\d+) (.+?) Response\n\n(.+?)(?=\n\*\*\* \d+\.\d+\.\d+|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    parsed_data = []
    for question_num, tradition_num, tradition_name, full_text in matches:
        sections = extract_sections_new_format(full_text)

        parsed_data.append({
            'question_number': question_num,
            'tradition_number': int(tradition_num),
            'tradition_name': tradition_name.strip(),
            'full_text': full_text.strip(),
            'sections': sections
        })

    return parsed_data

def extract_sections_new_format(text: str) -> Dict[str, str]:
    """Parse the 8 sections from NEW format response text"""
    sections = {}

    # Opening paragraph (everything before first **)
    opening_match = re.search(r'^(.+?)(?=\*\*|\Z)', text, re.DOTALL)
    if opening_match:
        sections['opening'] = opening_match.group(1).strip()

    # Extract bolded sections with flexible patterns
    section_patterns = {
        'historical_development': r'\*\*Historical Development:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'key_concepts': r'\*\*Key Concepts:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'core_arguments': r'\*\*Core Arguments:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'counter_arguments': r'\*\*Counter-?Arguments:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'textual_foundation': r'\*\*Textual Foundation:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'internal_variations': r'\*\*Internal Variations:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)',
        'contemporary_applications': r'\*\*Contemporary Applications:?\*\*\s*(.+?)(?=\n\*\*[A-Z]|\Z)'
    }

    for key, pattern in section_patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    return sections

def import_to_database(db_path='philosophical_traditions_sample.db', file_pattern='question_1.2*.txt'):
    """Import all new format .txt files into SQLite database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Parse all matching question files
    txt_files = sorted(Path('.').glob(file_pattern))
    print(f"📁 Found {len(txt_files)} files matching pattern '{file_pattern}'")
    print(f"📂 Files: {[f.name for f in txt_files]}\n")

    if not txt_files:
        print("❌ No files found! Check your file pattern.")
        return

    total_imported = 0
    questions_found = set()

    for filepath in txt_files:
        print(f"Processing {filepath.name}...")
        try:
            traditions = parse_new_format_file(filepath)

            if not traditions:
                print(f"  ⚠️  No traditions parsed from {filepath.name}")
                continue

            for trad in traditions:
                questions_found.add(trad['question_number'])

                # Insert or get question
                cursor.execute("""
                    INSERT OR IGNORE INTO questions (number, title, category, section)
                    VALUES (?, ?, ?, ?)
                """, (trad['question_number'], f"Question {trad['question_number']}", 'METAPHYSICS', 1))

                cursor.execute("SELECT id FROM questions WHERE number = ?", (trad['question_number'],))
                question_id = cursor.fetchone()[0]

                # Insert or get tradition
                cursor.execute("""
                    INSERT OR IGNORE INTO traditions (number, name)
                    VALUES (?, ?)
                """, (trad['tradition_number'], trad['tradition_name']))

                cursor.execute("SELECT id FROM traditions WHERE number = ?", (trad['tradition_number'],))
                tradition_id = cursor.fetchone()[0]

                # Insert response
                sections = trad['sections']
                word_count = len(trad['full_text'].split())

                cursor.execute("""
                    INSERT OR REPLACE INTO responses
                    (question_id, tradition_id, full_text, opening, historical_development,
                     key_concepts, core_arguments, counter_arguments, textual_foundation,
                     internal_variations, contemporary_applications, word_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    question_id, tradition_id, trad['full_text'],
                    sections.get('opening'), sections.get('historical_development'),
                    sections.get('key_concepts'), sections.get('core_arguments'),
                    sections.get('counter_arguments'), sections.get('textual_foundation'),
                    sections.get('internal_variations'), sections.get('contemporary_applications'),
                    word_count
                ))

            conn.commit()
            total_imported += len(traditions)
            print(f"  ✅ Imported {len(traditions)} traditions from {filepath.name}\n")

        except Exception as e:
            print(f"  ❌ Error processing {filepath.name}: {e}\n")

    conn.close()

    print(f"\n{'='*70}")
    print(f"✅ IMPORT COMPLETE!")
    print(f"{'='*70}")
    print(f"Total responses imported: {total_imported}")
    print(f"Questions imported: {sorted(questions_found)}")
    print(f"Database: {db_path}")
    print(f"{'='*70}")

    # Verify database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM responses")
    response_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT question_id) FROM responses")
    question_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(DISTINCT tradition_id) FROM responses")
    tradition_count = cursor.fetchone()[0]
    conn.close()

    print(f"\n📊 Database Statistics:")
    print(f"   Responses: {response_count}")
    print(f"   Questions: {question_count}")
    print(f"   Traditions: {tradition_count}")

if __name__ == '__main__':
    import sys

    # Allow custom file pattern from command line
    file_pattern = sys.argv[1] if len(sys.argv) > 1 else 'question_1.2[45]*.txt'

    print("="*70)
    print("PHILOSOPHICAL RESPONSES IMPORTER (NEW FORMAT)")
    print("="*70)
    print(f"File pattern: {file_pattern}")
    print(f"Target: Questions with 8-section format\n")

    import_to_database(file_pattern=file_pattern)
