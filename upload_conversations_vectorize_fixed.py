#!/usr/bin/env python3
"""
Upload conversation embeddings to Vectorize with CORRECT index name
"""
import json
import subprocess
import time
from pathlib import Path

EMBEDDINGS_FILE = "conversation_embeddings.json"
BATCH_SIZE = 500  # Larger batches since it's working now
INDEX_NAME = "philosophy-vectors"  # CORRECT INDEX NAME

def main():
    print("=" * 80)
    print(f"UPLOADING CONVERSATIONS TO VECTORIZE: {INDEX_NAME}")
    print("=" * 80)
    print(f"Batch size: {BATCH_SIZE}")
    print("=" * 80)
    print()
    
    # Load embeddings
    with open(EMBEDDINGS_FILE, 'r') as f:
        embeddings = json.load(f)
    
    total = len(embeddings)
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"📂 Total embeddings: {total:,}")
    print(f"📦 Batches: {num_batches}")
    print()
    
    success_count = 0
    failed_batches = []
    start_time = time.time()
    
    for i in range(0, total, BATCH_SIZE):
        batch_num = i // BATCH_SIZE + 1
        batch = embeddings[i:i + BATCH_SIZE]
        batch_end = min(i + BATCH_SIZE, total)
        
        print(f"[{batch_num}/{num_batches}] Uploading {i+1}-{batch_end}...", end=" ", flush=True)
        
        # Create temp NDJSON
        batch_file = f"temp_conv_{batch_num}.ndjson"
        with open(batch_file, 'w') as f:
            for item in batch:
                ndjson_item = {
                    "id": str(item['id']),
                    "values": item['embedding'],
                    "metadata": {
                        "source": "vedabase",
                        "book_code": "conversations",
                        "chunk_id": item['id'],
                        "chunk_type": item['chunk_type'],
                        "verse_id": item['verse_id']
                    }
                }
                f.write(json.dumps(ndjson_item) + '\n')
        
        # Upload
        try:
            result = subprocess.run(
                ['npx', 'wrangler', 'vectorize', 'upsert', INDEX_NAME,
                 '--file', batch_file],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            Path(batch_file).unlink(missing_ok=True)
            
            if result.returncode == 0:
                print("✅")
                success_count += len(batch)
            else:
                error = result.stderr[:80] if result.stderr else result.stdout[:80]
                print(f"❌ {error}")
                failed_batches.append(batch_num)
        
        except Exception as e:
            Path(batch_file).unlink(missing_ok=True)
            print(f"❌ {str(e)[:50]}")
            failed_batches.append(batch_num)
        
        if batch_num % 5 == 0:
            elapsed = time.time() - start_time
            rate = batch_num / (elapsed / 60) if elapsed > 0 else 0
            print(f"   Progress: {batch_num}/{num_batches} ({batch_num*100//num_batches}%) | Rate: {rate:.1f} batches/min")
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print("UPLOAD COMPLETE")
    print("=" * 80)
    print(f"  Success: {success_count:,}/{total:,} ({success_count*100//total if total > 0 else 0}%)")
    print(f"  Failed batches: {len(failed_batches)}")
    print(f"  Time: {elapsed/60:.1f} min")
    print("=" * 80)
    
    if failed_batches:
        print(f"\n⚠️  Failed: {failed_batches[:10]}")
    else:
        print("\n✅ ALL CONVERSATIONS UPLOADED TO VECTORIZE!")

if __name__ == '__main__':
    main()
