#!/usr/bin/env python3
"""Test import with small sample"""
import json
import requests
import time

IMPORT_WORKER_URL = "https://vedabase-import.joanmanelferrera-400.workers.dev"

data = json.load(open('vedabase_sample.json'))
verses = data['bg']

print(f"Importing {len(verses)} sample verses...")

for i, verse in enumerate(verses, 1):
    print(f"  {i}/{len(verses)}: {verse['verse']}...", end=" ")

    try:
        response = requests.post(
            IMPORT_WORKER_URL,
            json={"verses": [verse], "book_code": "bg"},
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✓ ({result.get('chunks_created', 0)} chunks)")
        else:
            print(f"✗ Error {response.status_code}")
            break
    except Exception as e:
        print(f"✗ {e}")
        break

    time.sleep(3)  # Wait between requests

print("\nDone!")
