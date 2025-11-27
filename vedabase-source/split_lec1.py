#!/usr/bin/env python3
"""
Split Lectures part 1 into three files at natural lecture boundaries.
"""

import os

def split_lec1():
    """Split lec1.html into three roughly equal parts."""
    filepath = 'lec1.html'
    print(f"Splitting {filepath} into three parts...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total lines: {total_lines}")

    # Header includes everything up to and including the opening of table-of-contents div (line 97)
    # but NOT the content divs (outline-container-orgc477097 and outline-text-2)
    header_end = 98  # After the blank line following </div></div> at line 97
    header = lines[:header_end]

    # Footer starts at postamble (line 241326, index 241325)
    footer_start = 241325
    footer = lines[footer_start:]

    # Split point: line 120656 is the end of one lecture before next starts
    # This is roughly the middle (120,656 out of 241,333 lines)
    split_point = 120656

    # Opening divs for content (needed for both parts after header)
    content_open = [
        '<div id="outline-container-orgc477097" class="outline-2">\n',
        '<h2 id="orgc477097">LECTURES  PART 1 of 2</h2>\n',
        '<div class="outline-text-2" id="text-orgc477097">\n'
    ]

    # Closing divs for content (3 closing divs before footer)
    content_close = [
        '</div>\n',  # close outline-text-2
        '</div>\n',  # close outline-container
        '</div>\n'   # close content
    ]

    # Split into 3 parts at natural lecture boundaries
    # Line 102 (0-indexed 101) is <p> opening tag for TOC
    # Line 80248 (0-indexed 80247) is <p> opening tag for lecture at ~1/3
    # Line 160022 (0-indexed 160021) is <p> opening tag for lecture at ~2/3

    splits = [
        ('lec1a.html', 101, 80247, 'Lectures part 1a'),
        ('lec1b.html', 80247, 160021, 'Lectures part 1b'),
        ('lec1c.html', 160021, 241322, 'Lectures part 1c')
    ]

    for filename, start_idx, end_idx, description in splits:
        print(f"  Creating {filename} ({description})...")

        with open(filename, 'w', encoding='utf-8') as f:
            # Write header (up to line 98)
            f.writelines(header)
            # Write content opening divs
            f.writelines(content_open)
            # Write content from split point
            f.writelines(lines[start_idx:end_idx])
            # Write content closing divs (3 closing divs)
            f.writelines(content_close)
            # Write footer (postamble)
            f.writelines(footer)

        size_mb = os.path.getsize(filename) / (1024 * 1024)
        line_count = end_idx - start_idx
        print(f"    ✓ Created {filename} ({size_mb:.1f} MB, {line_count:,} lines)")

    print(f"  ✓ Lectures part 1 split complete\n")

if __name__ == '__main__':
    split_lec1()
