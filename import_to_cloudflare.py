#!/usr/bin/env python3
"""
Import Vedabase verses to Cloudflare
Sends verses in batches to the import worker
"""

import json
import requests
import time
from pathlib import Path

IMPORT_WORKER_URL = "https://vedabase-import.joanmanelferrera-400.workers.dev"
BATCH_SIZE = 1  # Send 1 verse at a time (avoid Worker CPU limit)

def import_book(book_code: str, verses: list):
    """Import a single book's verses"""
    print(f"\nImporting {book_code}: {len(verses)} verses")

    total_batches = (len(verses) + BATCH_SIZE - 1) // BATCH_SIZE
    successful = 0
    failed = 0

    for i in range(0, len(verses), BATCH_SIZE):
        batch = verses[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        verse_ref = batch[0]['verse'] if batch else '?'

        print(f"  {batch_num}/{total_batches} ({verse_ref})...", end=" ", flush=True)

        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    IMPORT_WORKER_URL,
                    json={
                        "book_code": book_code,
                        "verses": batch
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    print(f"✓ {result.get('chunks_created', 0)} chunks")
                    successful += 1
                    break
                elif response.status_code == 503:
                    # Worker overloaded, wait and retry
                    if attempt < max_retries - 1:
                        print(f"⏳ retry {attempt + 1}...", end=" ", flush=True)
                        time.sleep(5)
                        continue
                    else:
                        print(f"✗ Error 503 (max retries)")
                        failed += 1
                        break
                else:
                    print(f"✗ Error {response.status_code}")
                    failed += 1
                    break

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    print(f"⏳ timeout, retry {attempt + 1}...", end=" ", flush=True)
                    time.sleep(5)
                    continue
                else:
                    print(f"✗ Timeout (max retries)")
                    failed += 1
                    break
            except Exception as e:
                print(f"✗ Exception: {str(e)[:50]}")
                failed += 1
                break

        # Rate limiting - wait between requests
        time.sleep(3)

        # Progress report every 50 verses
        if batch_num % 50 == 0:
            print(f"  Progress: {successful} successful, {failed} failed")

    print(f"\n  Final: {successful} successful, {failed} failed")
    return failed == 0

def main():
    # Load parsed data
    json_file = Path('vedabase_parsed.json')

    if not json_file.exists():
        print("Error: vedabase_parsed.json not found")
        print("Run parse_vedabase.py first")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        all_verses = json.load(f)

    print("=" * 60)
    print("VEDABASE IMPORT TO CLOUDFLARE")
    print("=" * 60)

    # Book mapping
    book_mapping = {
        'bg': 'Bhagavad Gita',
        'sb1': 'Srimad Bhagavatam Canto 1',
        'sb2': 'Srimad Bhagavatam Canto 2',
        'sb3': 'Srimad Bhagavatam Canto 3',
        'kb': 'Krishna Book',
        'cc1': 'Caitanya Caritamrita Vol 1',
        'cc2': 'Caitanya Caritamrita Vol 2',
        'cc3': 'Caitanya Caritamrita Vol 3'
    }

    # Summary
    print("\nBooks to import:")
    for code, name in book_mapping.items():
        count = len(all_verses.get(code, []))
        if count > 0:
            print(f"  {code}: {name} ({count} verses)")

    print("\nStarting import...")

    # Import each book
    for book_code in book_mapping.keys():
        verses = all_verses.get(book_code, [])

        if not verses:
            print(f"\nSkipping {book_code}: No verses found")
            continue

        success = import_book(book_code, verses)

        if not success:
            print(f"\n❌ Import failed for {book_code}, stopping")
            break

    print("\n" + "=" * 60)
    print("IMPORT COMPLETE")
    print("=" * 60)

if __name__ == '__main__':
    main()
