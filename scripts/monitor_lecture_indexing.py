#!/usr/bin/env python3
"""
Monitor Vectorize indexing of lecture embeddings
Checks every 5 minutes until lectures appear in search results
"""

import requests
import time
from datetime import datetime
import json

def check_lectures_indexed():
    """
    Test if lectures are searchable
    Returns (bool, dict) - (lectures_found, test_details)
    """
    try:
        # Test 1: Search for lecture-specific content
        response1 = requests.post(
            'https://philosophy-rag.joanmanelferrera-400.workers.dev',
            json={
                'query': 'general lecture location date',
                'topK': 10,
                'source': 'vedabase'
            },
            timeout=30
        )

        data1 = response1.json()
        lecture_results = [r for r in data1.get('results', [])
                          if r.get('sectionType') == 'lecture_content']

        # Test 2: Search with book filter for lectures
        response2 = requests.post(
            'https://philosophy-rag.joanmanelferrera-400.workers.dev',
            json={
                'query': 'devotional service',
                'topK': 10,
                'source': 'vedabase',
                'bookFilter': 'LEC1A'
            },
            timeout=30
        )

        data2 = response2.json()
        filtered_results = data2.get('count', 0)

        # Test 3: General search - check for ANY lecture results
        response3 = requests.post(
            'https://philosophy-rag.joanmanelferrera-400.workers.dev',
            json={
                'query': 'Krishna consciousness devotion',
                'topK': 20,
                'source': 'vedabase'
            },
            timeout=30
        )

        data3 = response3.json()
        any_lectures = any(r.get('sectionType') == 'lecture_content'
                          for r in data3.get('results', []))

        details = {
            'test1_lecture_results': len(lecture_results),
            'test2_filtered_count': filtered_results,
            'test3_any_lectures': any_lectures,
            'test1_total': data1.get('count', 0),
            'test2_total': data2.get('count', 0),
            'test3_total': data3.get('count', 0)
        }

        # Consider lectures indexed if ANY test finds them
        lectures_found = (len(lecture_results) > 0 or
                         filtered_results > 0 or
                         any_lectures)

        return lectures_found, details

    except Exception as e:
        return False, {'error': str(e)}

def main():
    print("=" * 80)
    print("LECTURE INDEXING MONITOR")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Checking every 5 minutes for lecture content in search results...")
    print("Press Ctrl+C to stop monitoring\n")

    check_count = 0
    start_time = time.time()

    try:
        while True:
            check_count += 1
            elapsed = int(time.time() - start_time)

            timestamp = datetime.now().strftime('%H:%M:%S')
            print(f"[{timestamp}] Check #{check_count} (elapsed: {elapsed//60}m {elapsed%60}s)")

            lectures_found, details = check_lectures_indexed()

            if 'error' in details:
                print(f"  ⚠️  Error: {details['error']}")
            else:
                print(f"  Test 1 (lecture query): {details['test1_lecture_results']}/{details['test1_total']} lecture results")
                print(f"  Test 2 (book filter):   {details['test2_filtered_count']} results with LEC1A filter")
                print(f"  Test 3 (general):       {'✓' if details['test3_any_lectures'] else '✗'} lectures in top 20 results")

            if lectures_found:
                print("\n" + "=" * 80)
                print("✅ LECTURES ARE NOW INDEXED AND SEARCHABLE!")
                print("=" * 80)
                print(f"Total time waited: {elapsed//60} minutes {elapsed%60} seconds")
                print("\nTest Details:")
                print(json.dumps(details, indent=2))
                print("\n🎉 The Vedabase RAG system is now complete with lectures!")
                print("=" * 80)
                break
            else:
                print("  ⏳ Lectures not yet indexed, waiting...")

                if check_count == 1:
                    print("\n  Note: Vectorize indexing typically takes 5-30 minutes")
                    print("        This is normal for Cloudflare's distributed system\n")

                # Wait 5 minutes before next check
                print(f"  Next check in 5 minutes...\n")
                time.sleep(300)  # 5 minutes

    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoring stopped by user")
        print(f"Total checks: {check_count}")
        print(f"Total time: {int(time.time() - start_time)//60} minutes")
        print("\nYou can resume monitoring later by running:")
        print("  python3 monitor_lecture_indexing.py")

if __name__ == '__main__':
    main()
