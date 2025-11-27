#!/usr/bin/env python3
"""Monitor upload progress and notify when complete"""
import subprocess
import time
import sys

print("Monitoring upload progress...")
print("=" * 60)

last_batch = 0
while True:
    # Check if upload process is running
    result = subprocess.run(
        ['ps', 'aux'],
        capture_output=True,
        text=True
    )

    if 'temp_batch' in result.stdout and '.sql' in result.stdout:
        # Extract batch number
        for line in result.stdout.split('\n'):
            if 'temp_batch' in line and '.sql' in line:
                import re
                match = re.search(r'temp_batch_(\d+)\.sql', line)
                if match:
                    batch = int(match.group(1))
                    if batch != last_batch:
                        progress = (batch / 170) * 100
                        print(f"[{time.strftime('%H:%M:%S')}] Batch {batch}/170 ({progress:.1f}%)")
                        last_batch = batch
                break
        time.sleep(10)
    else:
        print("\n" + "=" * 60)
        print("Upload process completed!")
        print("=" * 60)

        # Verify count
        print("\nVerifying upload...")
        result = subprocess.run(
            ['npx', 'wrangler', 'd1', 'execute', 'philosophy-db', '--remote',
             '--command', 'SELECT COUNT(*) FROM vedabase_verses'],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, 'CLOUDFLARE_API_TOKEN': ''}
        )

        if 'COUNT(*)' in result.stdout:
            import re
            match = re.search(r'"COUNT\(\*\)":\s*(\d+)', result.stdout)
            if match:
                count = int(match.group(1))
                print(f"✓ Total verses in remote D1: {count:,}")

                if count == 8481:
                    print("✓ All verses uploaded successfully!")
                elif count > 0:
                    print(f"⚠ Partial upload: {count}/8,481 verses")
                else:
                    print("✗ No verses found in remote database")

        break
