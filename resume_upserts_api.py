#!/usr/bin/env python3
"""
Resume vector upserts using Cloudflare REST API
Avoids OAuth token expiration issues
"""
import json
import requests
import os
import time
from pathlib import Path

# Cloudflare credentials
ACCOUNT_ID = "40035612bce74407c306499494965595"
INDEX_NAME = "philosophy-vectors"

# Get API token from environment
API_TOKEN = os.getenv('CLOUDFLARE_API_TOKEN')
if not API_TOKEN:
    print("ERROR: CLOUDFLARE_API_TOKEN environment variable not set")
    print("Set it with: export CLOUDFLARE_API_TOKEN='your-token-here'")
    exit(1)

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/vectorize/v2/indexes/{INDEX_NAME}"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/x-ndjson"
}

def upsert_batch(vectors_ndjson_chunk):
    """Upsert a batch of vectors via API"""
    url = f"{BASE_URL}/upsert"

    response = requests.post(url, headers=HEADERS, data=vectors_ndjson_chunk)

    if response.status_code == 200:
        result = response.json()
        return result.get('result', {})
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def upsert_file_from_offset(filepath, start_line, batch_size=100):
    """Resume upsert from a specific line offset"""
    print(f"\n{'='*80}")
    print(f"Upserting: {filepath}")
    print(f"Starting from line: {start_line}")
    print(f"Batch size: {batch_size}")
    print(f"{'='*80}\n")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total vectors in file: {total_lines}")
    print(f"Remaining vectors: {total_lines - start_line}\n")

    current_line = start_line
    batch_count = 0

    while current_line < total_lines:
        end_line = min(current_line + batch_size, total_lines)
        batch_lines = lines[current_line:end_line]
        batch_ndjson = ''.join(batch_lines)

        batch_count += 1
        vectors_in_batch = end_line - current_line

        print(f"Batch {batch_count}: Upserting vectors {current_line+1}-{end_line} ({vectors_in_batch} vectors)...", end=' ')

        result = upsert_batch(batch_ndjson)

        if result:
            mutation_id = result.get('mutationId', 'unknown')
            print(f"✓ Success (mutation: {mutation_id[:8]}...)")
        else:
            print(f"✗ Failed - stopping at line {current_line}")
            return current_line

        current_line = end_line

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    print(f"\n✅ Completed! All {total_lines} vectors upserted.")
    return total_lines

def main():
    """Resume all pending upserts"""

    # Files and their starting offsets (based on progress report)
    files_to_resume = [
        ("sb_cantos_1_3_for_upsert.ndjson", 8300),   # 46% complete, 9,724 remaining
        ("sb_cantos_4_10_for_upsert.ndjson", 7300),  # 45% complete, 8,904 remaining
        ("kb_for_upsert.ndjson", 1300),               # 70% complete, 560 remaining
        ("rechunked_for_upsert.ndjson", 1100),        # 3% complete, 33,231 remaining
    ]

    total_uploaded = 0

    for filepath, start_offset in files_to_resume:
        if not Path(filepath).exists():
            print(f"⚠️  File not found: {filepath}")
            continue

        final_offset = upsert_file_from_offset(filepath, start_offset, batch_size=100)
        uploaded = final_offset - start_offset
        total_uploaded += uploaded

        print(f"Uploaded {uploaded} vectors from {filepath}\n")

    print(f"\n{'='*80}")
    print(f"TOTAL VECTORS UPLOADED: {total_uploaded}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
