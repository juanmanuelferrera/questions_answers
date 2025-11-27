#!/usr/bin/env python3
"""
Detect which files are in old format vs new format
by checking for section headers.
"""

import re
from pathlib import Path

def detect_format(file_path):
    """Detect if file is old format (4 paragraphs) or new format (8 sections)"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(5000)  # Read first 5000 chars

        # Check for new format section headers
        section_headers = [
            r'\*\*Historical Development\*\*',
            r'\*\*Key Concepts\*\*',
            r'\*\*Core Arguments\*\*',
            r'\*\*Counter-Arguments\*\*',
            r'\*\*Textual Foundation\*\*',
            r'\*\*Internal Variations\*\*',
            r'\*\*Contemporary Applications\*\*'
        ]

        header_count = 0
        for pattern in section_headers:
            if re.search(pattern, content):
                header_count += 1

        # If we find 3+ section headers, it's new format
        if header_count >= 3:
            return 'NEW'
        else:
            return 'OLD'

    except Exception as e:
        return f'ERROR: {e}'

def main():
    print("="*80)
    print("FILE FORMAT DETECTOR")
    print("="*80)
    print("\nScanning all .org and .txt files...\n")

    # Get all potential response files
    all_files = list(Path('.').glob('*.org')) + list(Path('.').glob('*.txt'))

    # Filter to likely response files
    response_files = [
        f for f in all_files
        if any(x in f.name.lower() for x in ['question', 'response', 'tradition', 'q1.', '1.'])
        and 'backup' not in f.name.lower()
        and 'converted' not in f.name.lower()
        and 'philosophical_questions' not in f.name.lower()
    ]

    old_format_files = []
    new_format_files = []
    error_files = []

    for file_path in sorted(response_files):
        format_type = detect_format(file_path)

        if format_type == 'OLD':
            old_format_files.append(file_path)
            print(f"📜 OLD: {file_path.name}")
        elif format_type == 'NEW':
            new_format_files.append(file_path)
            print(f"✨ NEW: {file_path.name}")
        else:
            error_files.append(file_path)
            print(f"❌ ERR: {file_path.name} - {format_type}")

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Old format files (need conversion): {len(old_format_files)}")
    print(f"New format files (already good): {len(new_format_files)}")
    print(f"Error files: {len(error_files)}")

    # Extract question numbers from old format files
    questions_needing_conversion = set()
    for f in old_format_files:
        # Extract question number like 1.1, 1.2, etc
        match = re.search(r'1\.(\d+)', f.name)
        if match:
            q_num = f"1.{match.group(1)}"
            questions_needing_conversion.add(q_num)

    print(f"\nQuestions needing conversion: {sorted(questions_needing_conversion)}")

    # Estimate responses and cost
    total_responses = 0
    for f in old_format_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                content = file.read()
                # Count response markers
                count = len(re.findall(r'\*\*\* \d+\.\d+\.\d+ .+ Response', content))
                total_responses += count
        except:
            pass

    estimated_cost = total_responses * 0.02  # ~$0.02 per response

    print(f"\n📊 Total responses to convert: ~{total_responses}")
    print(f"💰 Estimated conversion cost: ${estimated_cost:.2f}")

    # Save list to file
    with open('files_to_convert.txt', 'w') as f:
        f.write("OLD FORMAT FILES (NEED CONVERSION):\n")
        f.write("="*80 + "\n")
        for file in sorted(old_format_files):
            f.write(f"{file.name}\n")

        f.write("\n\nNEW FORMAT FILES (ALREADY GOOD):\n")
        f.write("="*80 + "\n")
        for file in sorted(new_format_files):
            f.write(f"{file.name}\n")

    print(f"\n📝 Full list saved to: files_to_convert.txt")

if __name__ == '__main__':
    main()
