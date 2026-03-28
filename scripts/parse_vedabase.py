#!/usr/bin/env python3
"""
Vedabase HTML Parser
Extracts verses, translations, and purports from Vedabase HTML files
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

def extract_verse_data(verse_div) -> Dict:
    """Extract verse components (sanskrit, synonyms, translation, purport)"""
    text_content = verse_div.find('div', class_='outline-text-3') or verse_div.find('div', class_='outline-text-4')

    if not text_content:
        return None

    # Get all paragraphs
    paras = text_content.find_all('p')

    if not paras:
        return None

    verse_data = {
        'sanskrit': [],
        'synonyms': '',
        'translation': [],
        'purport': []
    }

    current_section = 'sanskrit'
    found_synonyms = False

    for para in paras:
        text = clean_text(para.get_text())

        if not text:
            continue

        # Check for section markers
        if text == 'SYNONYMS':
            current_section = 'synonyms'
            found_synonyms = True
            continue
        elif text == 'TRANSLATION':
            current_section = 'translation'
            continue
        elif text == 'PURPORT':
            current_section = 'purport'
            continue

        # Add content to appropriate section
        if current_section == 'sanskrit':
            # Stop adding to sanskrit if we hit synonyms
            if not found_synonyms:
                verse_data['sanskrit'].append(text)
        elif current_section == 'synonyms':
            verse_data['synonyms'] += text + ' '
            # After synonyms, next paragraph is translation
            current_section = 'post_synonyms'
        elif current_section == 'post_synonyms':
            # First paragraph after synonyms is translation
            verse_data['translation'].append(text)
            current_section = 'purport'
        elif current_section == 'translation':
            verse_data['translation'].append(text)
        elif current_section == 'purport':
            verse_data['purport'].append(text)

    # Join sections
    verse_data['sanskrit'] = '\n'.join(verse_data['sanskrit'])
    verse_data['synonyms'] = verse_data['synonyms'].strip()
    verse_data['translation'] = '\n\n'.join(verse_data['translation'])
    verse_data['purport'] = '\n\n'.join(verse_data['purport'])

    return verse_data

def parse_bhagavad_gita(html_path: Path) -> List[Dict]:
    """Parse Bhagavad Gita (outline-3 structure)"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    verses = []
    current_chapter = None
    current_chapter_title = None

    # Find all chapters (outline-2) and verses (outline-3)
    for element in soup.find_all('div', class_='outline-2'):
        h2 = element.find('h2')
        if h2:
            # Extract chapter number and title
            chapter_text = clean_text(h2.get_text())
            current_chapter = chapter_text
            current_chapter_title = chapter_text

        # Find verses in this chapter
        for verse_div in element.find_all('div', class_='outline-3'):
            h3 = verse_div.find('h3')
            if not h3:
                continue

            verse_number = clean_text(h3.get_text())
            verse_data = extract_verse_data(verse_div)

            if verse_data and (verse_data['translation'] or verse_data['purport']):
                verses.append({
                    'book': 'Bhagavad Gita',
                    'chapter': current_chapter,
                    'chapter_title': current_chapter_title,
                    'verse': verse_number,
                    'sanskrit': verse_data['sanskrit'],
                    'synonyms': verse_data['synonyms'],
                    'translation': verse_data['translation'],
                    'purport': verse_data['purport']
                })

    return verses

def parse_srimad_bhagavatam(html_path: Path, canto_number: str) -> List[Dict]:
    """Parse Srimad Bhagavatam (outline-4 structure)"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    verses = []
    current_part = None
    current_chapter = None

    # Find all parts/sections (outline-2), chapters (outline-3), and verses (outline-4)
    for part_div in soup.find_all('div', class_='outline-2'):
        h2 = part_div.find('h2', recursive=False)
        if h2:
            current_part = clean_text(h2.get_text())

        for chapter_div in part_div.find_all('div', class_='outline-3'):
            h3 = chapter_div.find('h3', recursive=False)
            if h3:
                current_chapter = clean_text(h3.get_text())

            for verse_div in chapter_div.find_all('div', class_='outline-4'):
                h4 = verse_div.find('h4')
                if not h4:
                    continue

                verse_number = clean_text(h4.get_text())
                verse_data = extract_verse_data(verse_div)

                if verse_data and (verse_data['translation'] or verse_data['purport']):
                    verses.append({
                        'book': f'Srimad Bhagavatam Canto {canto_number}',
                        'part': current_part,
                        'chapter': current_chapter,
                        'verse': verse_number,
                        'sanskrit': verse_data['sanskrit'],
                        'synonyms': verse_data['synonyms'],
                        'translation': verse_data['translation'],
                        'purport': verse_data['purport']
                    })

    return verses

def parse_caitanya_caritamrta(html_path: Path, lila_number: str) -> List[Dict]:
    """Parse Caitanya Caritamrta (different structure - uses TEXT markers)"""
    with open(html_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    verses = []

    # Find all TEXT markers
    text_pattern = re.compile(r'^TEXT\s+(\d+)$')

    # Get all paragraphs
    all_paras = soup.find_all('p')

    current_chapter = None
    i = 0

    while i < len(all_paras):
        para_text = clean_text(all_paras[i].get_text())

        # Check if this is a chapter header (starts with "Chapter")
        if para_text.startswith('Chapter'):
            current_chapter = para_text
            i += 1
            continue

        # Check if this is a TEXT marker
        text_match = text_pattern.match(para_text)
        if text_match:
            verse_number = f"TEXT {text_match.group(1)}"

            # Collect verse components
            verse_data = {
                'sanskrit': [],
                'synonyms': '',
                'translation': [],
                'purport': []
            }

            current_section = 'sanskrit'
            i += 1

            # Process paragraphs until next TEXT or end
            while i < len(all_paras):
                next_text = clean_text(all_paras[i].get_text())

                # Stop if we hit another TEXT marker
                if text_pattern.match(next_text):
                    break

                # Stop if we hit another chapter
                if next_text.startswith('Chapter'):
                    break

                # Check for section markers
                if next_text == 'SYNONYMS':
                    current_section = 'synonyms'
                    i += 1
                    continue
                elif next_text == 'TRANSLATION':
                    current_section = 'translation'
                    i += 1
                    continue
                elif next_text == 'PURPORT':
                    current_section = 'purport'
                    i += 1
                    continue

                # Add content to appropriate section
                if current_section == 'sanskrit':
                    verse_data['sanskrit'].append(next_text)
                elif current_section == 'synonyms':
                    verse_data['synonyms'] += next_text + ' '
                    current_section = 'post_synonyms'
                elif current_section == 'post_synonyms':
                    verse_data['translation'].append(next_text)
                    current_section = 'purport'
                elif current_section == 'translation':
                    verse_data['translation'].append(next_text)
                elif current_section == 'purport':
                    verse_data['purport'].append(next_text)

                i += 1

            # Join sections
            verse_data['sanskrit'] = '\n'.join(verse_data['sanskrit'])
            verse_data['synonyms'] = verse_data['synonyms'].strip()
            verse_data['translation'] = '\n\n'.join(verse_data['translation'])
            verse_data['purport'] = '\n\n'.join(verse_data['purport'])

            # Add verse if it has content
            if verse_data['translation'] or verse_data['purport']:
                lila_names = {
                    '1': 'Adi-lila',
                    '2': 'Madhya-lila',
                    '3': 'Antya-lila'
                }

                verses.append({
                    'book': f'Caitanya Caritamrita {lila_names.get(lila_number, lila_number)}',
                    'part': '',
                    'chapter': current_chapter or '',
                    'verse': verse_number,
                    'sanskrit': verse_data['sanskrit'],
                    'synonyms': verse_data['synonyms'],
                    'translation': verse_data['translation'],
                    'purport': verse_data['purport']
                })
        else:
            i += 1

    return verses

def parse_all_vedabase(source_dir: Path) -> Dict[str, List[Dict]]:
    """Parse all Vedabase HTML files"""
    all_verses = {}

    # Parse Bhagavad Gita
    print("Parsing Bhagavad Gita...")
    bg_path = source_dir / 'bg.html'
    if bg_path.exists():
        all_verses['bg'] = parse_bhagavad_gita(bg_path)
        print(f"  Found {len(all_verses['bg'])} verses")

    # Parse Srimad Bhagavatam Cantos
    for canto in [1, 2, 3]:
        print(f"Parsing Srimad Bhagavatam Canto {canto}...")
        sb_path = source_dir / f'sb{canto}.html'
        if sb_path.exists():
            all_verses[f'sb{canto}'] = parse_srimad_bhagavatam(sb_path, str(canto))
            print(f"  Found {len(all_verses[f'sb{canto}'])} verses")

    # Parse Krishna Book
    print("Parsing Krishna Book...")
    kb_path = source_dir / 'kb.html'
    if kb_path.exists():
        all_verses['kb'] = parse_bhagavad_gita(kb_path)  # Same structure as BG
        print(f"  Found {len(all_verses['kb'])} verses")

    # Parse Caitanya Caritamrita
    for volume in [1, 2, 3]:
        print(f"Parsing Caitanya Caritamrita Volume {volume}...")
        cc_path = source_dir / f'cc{volume}.html'
        if cc_path.exists():
            all_verses[f'cc{volume}'] = parse_caitanya_caritamrta(cc_path, str(volume))
            print(f"  Found {len(all_verses[f'cc{volume}'])} verses")

    return all_verses

if __name__ == '__main__':
    source_dir = Path('/Users/jaganat/.emacs.d/git_projects/vedabase-app-website/vedabase-app/vedabase-source')

    print("Starting Vedabase parsing...")
    all_verses = parse_all_vedabase(source_dir)

    # Save to JSON
    output_file = Path('vedabase_parsed.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_verses, f, ensure_ascii=False, indent=2)

    # Print summary
    total = sum(len(verses) for verses in all_verses.values())
    print(f"\nTotal verses parsed: {total}")
    print(f"Saved to: {output_file}")
