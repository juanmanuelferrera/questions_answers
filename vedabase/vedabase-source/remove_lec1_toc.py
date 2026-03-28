#!/usr/bin/env python3
"""
Remove the table of contents from lec1.html (lines 125-8210)
"""

import os

def remove_toc_from_lec1():
    """Remove TOC section from lec1.html"""
    filepath = 'lec1.html'
    print(f"Removing TOC from {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)
    print(f"Total lines before: {total_lines}")

    # Keep lines 0-124 (before TOC)
    # Skip lines 125-8210 (the TOC)
    # Keep lines 8211 onwards (actual lecture content)

    # Note: line numbers in editor are 1-indexed, Python list is 0-indexed
    # Line 125 in editor = index 124
    # Line 8210 in editor = index 8209

    new_lines = lines[:124] + lines[8210:]

    # Write back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    new_total = len(new_lines)
    removed = total_lines - new_total
    print(f"Total lines after: {new_total}")
    print(f"Removed {removed:,} lines of TOC")

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"New file size: {size_mb:.1f} MB")
    print(f"✓ TOC removed from {filepath}\n")

if __name__ == '__main__':
    remove_toc_from_lec1()
