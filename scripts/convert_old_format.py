#!/usr/bin/env python3
"""
Convert old format philosophical responses (4 paragraphs)
to new format (8 explicit sections) for optimal RAG performance.

Old format: ~900 words, 4 paragraphs
New format: ~400 words, 8 sections with headers
"""

import os
import re
import time
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Track conversion stats
conversion_stats = {
    'total_responses': 0,
    'successful': 0,
    'failed': 0,
    'total_cost': 0.0
}

def extract_old_format_responses(file_path):
    """Extract responses from old format .org files"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Pattern for old format: *** 1.1.1 Catholic Response
    pattern = r'\*\*\* (\d+\.\d+)\.(\d+) (.+?) Response\n\n(.+?)(?=\n\*\*\* \d+\.\d+\.\d+|\Z)'
    matches = re.findall(pattern, content, re.DOTALL)

    responses = []
    for question_num, tradition_num, tradition_name, full_text in matches:
        responses.append({
            'question_number': question_num,
            'tradition_number': int(tradition_num),
            'tradition_name': tradition_name.strip(),
            'old_text': full_text.strip()
        })

    return responses

def restructure_response(old_text, tradition_name):
    """Use Claude to restructure response into 8-section format"""

    prompt = f"""You are restructuring a philosophical response to follow a specific format.

ORIGINAL RESPONSE:
{old_text}

TASK: Restructure this response into EXACTLY 8 sections with these specifications:

1. **Opening Paragraph** (~75 words)
   - Direct answer to the question from this tradition's perspective
   - Core position statement
   - Key ontological/epistemological commitments
   - NO section header, just the paragraph

2. **Historical Development** (~75 words)
   - Start with: "**Historical Development:**"
   - Key figures, texts, periods
   - Evolution of the position
   - Schools, movements, controversies

3. **Key Concepts** (~50 words)
   - Start with: "**Key Concepts:**"
   - 8-12 technical terms with translations (if applicable)
   - Format: *term* (explanation) or *foreign-term* (English translation)
   - Example: *Brahman* (ultimate reality), *maya* (illusion)

4. **Core Arguments** (~100 words)
   - Start with: "**Core Arguments:**"
   - Numbered arguments (1, 2, 3, 4)
   - Main philosophical positions
   - Reasoning and justifications

5. **Counter-Arguments** (~40 words)
   - Start with: "**Counter-Arguments:**"
   - Positions this tradition argues against
   - Format: "Against X: explanation"
   - Critical engagement with alternatives

6. **Textual Foundation** (~40 words)
   - Start with: "**Textual Foundation:**"
   - Primary sources (sutras, scriptures, philosophical works)
   - Specific chapters/sections
   - Key commentaries

7. **Internal Variations** (~40 words)
   - Start with: "**Internal Variations:**"
   - Sub-schools, interpretive debates
   - Regional variations
   - Contested interpretations

8. **Contemporary Applications** (~40 words)
   - Start with: "**Contemporary Applications:**"
   - Modern philosophical debates
   - Relevant fields (science, ethics, etc.)
   - Ongoing influence

CRITICAL REQUIREMENTS:
- Target total: ~400 words (can be 350-450)
- Opening paragraph has NO header
- All other sections start with **Section Name:**
- Maintain scholarly accuracy - don't invent information
- Preserve all key philosophical concepts from original
- Use clear, concise language
- If original lacks info for a section, briefly note what exists

Return ONLY the restructured response, no explanations."""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        restructured = message.content[0].text

        # Estimate cost (input + output tokens)
        input_tokens = len(prompt.split()) * 1.3  # rough estimate
        output_tokens = len(restructured.split()) * 1.3
        cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
        conversion_stats['total_cost'] += cost

        return restructured, cost

    except Exception as e:
        print(f"   ❌ Error restructuring: {e}")
        return None, 0

def convert_file(input_path, output_path, dry_run=False):
    """Convert an old format file to new format"""
    print(f"\n{'='*80}")
    print(f"Processing: {input_path.name}")
    print(f"{'='*80}")

    # Extract responses
    responses = extract_old_format_responses(input_path)
    print(f"Found {len(responses)} responses to convert")

    if dry_run:
        print("DRY RUN - No API calls or file writes")
        return len(responses)

    # Convert each response
    converted_responses = []
    for i, resp in enumerate(responses, 1):
        print(f"\n[{i}/{len(responses)}] Converting {resp['tradition_name']}...", end=' ')
        conversion_stats['total_responses'] += 1

        new_text, cost = restructure_response(resp['old_text'], resp['tradition_name'])

        if new_text:
            converted_responses.append({
                'question_number': resp['question_number'],
                'tradition_number': resp['tradition_number'],
                'tradition_name': resp['tradition_name'],
                'new_text': new_text
            })
            conversion_stats['successful'] += 1
            print(f"✅ (${cost:.4f})")
        else:
            conversion_stats['failed'] += 1
            print(f"❌ Failed")

        # Rate limit: pause between requests
        time.sleep(1)

    # Write converted file
    if converted_responses:
        output_content = []
        for resp in converted_responses:
            header = f"*** {resp['question_number']}.{resp['tradition_number']} {resp['tradition_name']} Response\n\n"
            output_content.append(header + resp['new_text'] + "\n\n")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(''.join(output_content))

        print(f"\n✅ Saved to: {output_path}")

    return len(responses)

def backup_file(file_path):
    """Create backup of original file"""
    backup_dir = Path(file_path).parent / 'backups_original_format'
    backup_dir.mkdir(exist_ok=True)

    backup_path = backup_dir / f"{file_path.name}.backup"

    import shutil
    shutil.copy2(file_path, backup_path)
    print(f"📦 Backed up to: {backup_path}")

def main():
    print("="*80)
    print("PHILOSOPHICAL RESPONSES FORMAT CONVERTER")
    print("="*80)
    print("\nThis script converts old format (4 paragraphs) to new format (8 sections)")
    print("for optimal RAG performance.\n")

    # Find all old format files
    old_format_patterns = [
        'new_responses_1.1.org',
        'responses_1.1_traditions_*.org',
        'q1.2_responses_*.org',
        'new_1.2_traditions_*.org',
        'new_responses_1.2.*.org',
        'question_1.2_responses_*.org'
    ]

    files_to_convert = []
    for pattern in old_format_patterns:
        files_to_convert.extend(Path('.').glob(pattern))

    files_to_convert = sorted(set(files_to_convert))

    print(f"Found {len(files_to_convert)} files to convert:")
    for f in files_to_convert:
        print(f"  - {f.name}")

    # Estimate cost
    total_responses = 0
    for file_path in files_to_convert:
        responses = extract_old_format_responses(file_path)
        total_responses += len(responses)

    estimated_cost = total_responses * 0.02  # ~$0.02 per response
    print(f"\n📊 Total responses: {total_responses}")
    print(f"💰 Estimated cost: ${estimated_cost:.2f}")

    # Confirm
    print("\n" + "="*80)
    response = input("Proceed with conversion? (yes/no): ").strip().lower()

    if response != 'yes':
        print("❌ Cancelled")
        return

    # Convert files
    print("\n🚀 Starting conversion...\n")

    for file_path in files_to_convert:
        # Backup original
        backup_file(file_path)

        # Determine output path
        output_path = file_path.parent / f"{file_path.stem}_CONVERTED.txt"

        # Convert
        convert_file(file_path, output_path, dry_run=False)

    # Print summary
    print("\n" + "="*80)
    print("CONVERSION COMPLETE")
    print("="*80)
    print(f"Total responses processed: {conversion_stats['total_responses']}")
    print(f"Successful: {conversion_stats['successful']} ✅")
    print(f"Failed: {conversion_stats['failed']} ❌")
    print(f"Total cost: ${conversion_stats['total_cost']:.2f}")
    print(f"\n📂 Original files backed up to: backups_original_format/")
    print(f"📝 Converted files saved with _CONVERTED.txt suffix")

if __name__ == '__main__':
    main()
