import os
import re
import glob

def scan_files(directory):
    # Regex to match headers like "*** 1.1.1 Catholic Response"
    # We'll be flexible with the number of asterisks and whitespace
    header_pattern = re.compile(r'^\s*\*+\s*(\d+\.\d+\.\d+)\s+(.*)$')
    
    long_answers_found = 0
    files_with_content = 0
    
    # Files to ignore (the main file and backups)
    ignore_files = {
        'philosophical_questions.org', 
        'data.json', 
        'database.html', 
        'parse_data.py',
        'scan_long_answers.py'
    }

    # Debug specific file
    debug_file = 'new_responses_1.1.org'
    debug_path = os.path.join(directory, debug_file)
    if os.path.exists(debug_path):
        print(f"Debugging {debug_file}...")
        with open(debug_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:5]):
                print(f"Line {i}: {repr(line)}")
                match = header_pattern.search(line)
                if match:
                    print(f"  MATCH: {match.groups()}")
                else:
                    print(f"  NO MATCH")

    for filename in os.listdir(directory):
        if filename in ignore_files or filename.startswith('philosophical_questions.org.backup'):
            continue
            
        filepath = os.path.join(directory, filename)
        if not os.path.isfile(filepath):
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check if file has potential content
            matches = header_pattern.findall(content)
            if matches:
                files_with_content += 1
                long_answers_found += len(matches)
                # print(f"Found {len(matches)} answers in {filename}")
                
        except Exception as e:
            print(f"Error reading {filename}: {e}")

    print(f"Total files with content: {files_with_content}")
    print(f"Total long answers found: {long_answers_found}")

if __name__ == "__main__":
    scan_files('/Users/jaganat/.gemini/antigravity/scratch/questions_answers')
