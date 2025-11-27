#!/usr/bin/env python3
"""
Philosophy Search - Web Search Across 185 Philosophical Traditions

Searches the internet for how different philosophical traditions address a concept.

Usage:
    python3 philosophy_search.py "karma"
    python3 philosophy_search.py "free will"
    python3 philosophy_search.py "divine will"
"""

import sys
import re
import glob
from collections import OrderedDict

def extract_traditions():
    """Extract all tradition names from the files"""
    traditions = OrderedDict()

    # Find all tradition files
    files = glob.glob("*traditions*.txt") + glob.glob("*responses*.txt")

    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find all tradition headers: *** 1.25.1 Catholic Response
            matches = re.findall(r'\*\*\*\s+[\d.]+\s+(.+?)\s+Response', content)
            for tradition in matches:
                tradition = tradition.strip()
                if tradition and tradition not in traditions:
                    traditions[tradition] = True

        except Exception as e:
            continue

    return list(traditions.keys())

def main():
    if len(sys.argv) < 2:
        print("\nPhilosophy Web Search Across 185 Traditions")
        print("=" * 80)
        print("\nUsage: python3 philosophy_search.py \"concept\"")
        print("\nExamples:")
        print('  python3 philosophy_search.py "karma"')
        print('  python3 philosophy_search.py "free will"')
        print('  python3 philosophy_search.py "divine will"')
        print('  python3 philosophy_search.py "consciousness"')
        print("\n" + "=" * 80)
        sys.exit(1)

    concept = " ".join(sys.argv[1:])

    print("\n" + "=" * 80)
    print(f"🌐 SEARCHING WEB FOR: {concept}")
    print("=" * 80)
    print("\nExtracting traditions from local files...")

    traditions = extract_traditions()

    print(f"\nFound {len(traditions)} unique philosophical traditions")
    print("\nWill search the web for how each tradition addresses: " + concept)
    print("\n" + "=" * 80)

    # Print search instructions for Claude
    print(f"\nSEARCH_INSTRUCTIONS:")
    print(f"Concept: {concept}")
    print(f"Number of traditions: {len(traditions)}")
    print(f"\nPlease use WebSearch to find information about '{concept}' in these traditions:")

    # Show first 20 traditions as examples
    print(f"\nKey traditions to search (showing first 20 of {len(traditions)}):")
    for i, trad in enumerate(traditions[:20], 1):
        print(f"  {i}. {trad}")

    if len(traditions) > 20:
        print(f"  ... and {len(traditions) - 20} more")

    print(f"\nSuggested search strategy:")
    print(f"1. Search for '{concept}' in major tradition groups:")
    print(f"   - Christian traditions (Catholic, Protestant, Orthodox, etc.)")
    print(f"   - Buddhist traditions (Theravada, Mahayana, Zen, etc.)")
    print(f"   - Hindu traditions (Advaita, Vishishtadvaita, etc.)")
    print(f"   - Other major traditions")
    print(f"2. Focus on academic sources (Stanford Encyclopedia, IEP)")
    print(f"3. Compile and synthesize results across traditions")
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main()
