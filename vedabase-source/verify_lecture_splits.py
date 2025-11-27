#!/usr/bin/env python3
"""
Verify that split lecture files contain the same content as originals.
"""

def extract_content(filepath):
    """Extract just the lecture content between opening divs and closing divs."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find where content starts (after header/TOC)
    # Look for the opening content div
    content_start = None
    for i, line in enumerate(lines):
        if '<div class="outline-text-2"' in line:
            content_start = i + 1
            break

    # Find where content ends (before postamble)
    content_end = None
    for i, line in enumerate(lines):
        if '<div id="postamble"' in line:
            content_end = i
            break

    if content_start is None or content_end is None:
        print(f"ERROR: Could not find content boundaries in {filepath}")
        return []

    # Extract content lines, removing closing divs at the end
    content = lines[content_start:content_end]

    # Remove trailing closing divs (typically 3 divs before postamble)
    while content and content[-1].strip() in ['</div>', '']:
        content.pop()

    return content

def verify_splits():
    """Verify that split files match originals."""
    print("Verifying lecture splits...\n")

    # Extract content from originals
    print("Reading lec1.html...")
    lec1_content = extract_content('lec1.html')
    print(f"  lec1.html content: {len(lec1_content):,} lines")

    print("Reading lec2.html...")
    lec2_content = extract_content('lec2.html')
    print(f"  lec2.html content: {len(lec2_content):,} lines")

    # Extract content from splits
    print("\nReading split files...")
    lec1a_content = extract_content('lec1a.html')
    print(f"  lec1a.html content: {len(lec1a_content):,} lines")

    lec1b_content = extract_content('lec1b.html')
    print(f"  lec1b.html content: {len(lec1b_content):,} lines")

    lec1c_content = extract_content('lec1c.html')
    print(f"  lec1c.html content: {len(lec1c_content):,} lines")

    lec2a_content = extract_content('lec2a.html')
    print(f"  lec2a.html content: {len(lec2a_content):,} lines")

    lec2b_content = extract_content('lec2b.html')
    print(f"  lec2b.html content: {len(lec2b_content):,} lines")

    lec2c_content = extract_content('lec2c.html')
    print(f"  lec2c.html content: {len(lec2c_content):,} lines")

    # Combine split contents
    lec1_combined = lec1a_content + lec1b_content + lec1c_content
    lec2_combined = lec2a_content + lec2b_content + lec2c_content

    print(f"\nCombined lec1 splits: {len(lec1_combined):,} lines")
    print(f"Combined lec2 splits: {len(lec2_combined):,} lines")

    # Compare
    print("\n" + "="*60)
    print("VERIFICATION RESULTS:")
    print("="*60)

    if lec1_content == lec1_combined:
        print("✓ lec1: PERFECT MATCH - All content preserved")
    else:
        print("✗ lec1: MISMATCH DETECTED")
        print(f"  Original: {len(lec1_content):,} lines")
        print(f"  Combined: {len(lec1_combined):,} lines")
        print(f"  Difference: {len(lec1_content) - len(lec1_combined):,} lines")

        # Find where they differ
        for i in range(min(len(lec1_content), len(lec1_combined))):
            if lec1_content[i] != lec1_combined[i]:
                print(f"  First difference at line {i+1}")
                print(f"    Original: {lec1_content[i][:80]}")
                print(f"    Combined: {lec1_combined[i][:80]}")
                break

    if lec2_content == lec2_combined:
        print("✓ lec2: PERFECT MATCH - All content preserved")
    else:
        print("✗ lec2: MISMATCH DETECTED")
        print(f"  Original: {len(lec2_content):,} lines")
        print(f"  Combined: {len(lec2_combined):,} lines")
        print(f"  Difference: {len(lec2_content) - len(lec2_combined):,} lines")

        # Find where they differ
        for i in range(min(len(lec2_content), len(lec2_combined))):
            if lec2_content[i] != lec2_combined[i]:
                print(f"  First difference at line {i+1}")
                print(f"    Original: {lec2_content[i][:80]}")
                print(f"    Combined: {lec2_combined[i][:80]}")
                break

    print("="*60)

    # Summary
    total_original = len(lec1_content) + len(lec2_content)
    total_combined = len(lec1_combined) + len(lec2_combined)

    print(f"\nTotal original lines: {total_original:,}")
    print(f"Total combined lines: {total_combined:,}")

    if total_original == total_combined and lec1_content == lec1_combined and lec2_content == lec2_combined:
        print("\n✓✓✓ SUCCESS: All content matches perfectly! ✓✓✓")
    else:
        print(f"\n✗✗✗ WARNING: Content mismatch of {abs(total_original - total_combined):,} lines ✗✗✗")

if __name__ == '__main__':
    verify_splits()
