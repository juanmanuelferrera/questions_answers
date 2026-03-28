#!/usr/bin/env python3
"""
Split Lectures part 2 into three files at natural lecture boundaries.
"""

import os

def split_lec2():
    """Split lec2.html into three roughly equal parts."""
    filepath = 'lec2.html'
    print(f"Splitting {filepath} into three parts...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total lines: {total_lines}")

    # Header includes everything up to and including the opening of table-of-contents div (line 110)
    # but NOT the content divs (outline-container-org2aaab64 and outline-text-2)
    header_end = 111  # After the blank line following </div></div> at line 110
    header = lines[:header_end]

    # Footer starts at postamble (line 285655, index 285654)
    footer_start = 285654
    footer = lines[footer_start:]

    # Split point: line 142869 is <p> opening the next lecture
    # This is roughly the middle (142,869 out of 285,661 lines)
    split_point = 142869

    # Opening divs for content (needed for both parts after header)
    content_open = [
        '<div id="outline-container-org2aaab64" class="outline-2">\n',
        '<h2 id="org2aaab64">LECTURES  PART 2 OF 2</h2>\n',
        '<div class="outline-text-2" id="text-org2aaab64">\n'
    ]

    # Closing divs for content (3 closing divs before footer)
    content_close = [
        '</div>\n',  # close outline-text-2
        '</div>\n',  # close outline-container
        '</div>\n'   # close content
    ]

    # Split into 3 parts at natural lecture boundaries
    # Line 115 (0-indexed 114) is <p> opening tag for first lecture
    # Line 95517 (0-indexed 95516) is <p> opening tag for lecture at ~1/3
    # Line 190011 (0-indexed 190010) is <p> opening tag for lecture at ~2/3

    splits = [
        ('lec2a.html', 114, 95516, 'Lectures part 2a'),
        ('lec2b.html', 95516, 190010, 'Lectures part 2b'),
        ('lec2c.html', 190010, 285651, 'Lectures part 2c')
    ]

    for filename, start_idx, end_idx, description in splits:
        print(f"  Creating {filename} ({description})...")

        with open(filename, 'w', encoding='utf-8') as f:
            # Write header (up to line 111)
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

    print(f"  ✓ Lectures part 2 split complete\n")

if __name__ == '__main__':
    split_lec2()
