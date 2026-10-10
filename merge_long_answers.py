import os
import re
import json

def merge_long_answers(directory):
    data_path = os.path.join(directory, 'data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Create a map for quick lookup: ID -> (category_index, question_index, response_index)
    id_map = {}
    for c_idx, category in enumerate(data):
        for q_idx, question in enumerate(category['questions']):
            for r_idx, response in enumerate(question['responses']):
                # Extract ID from tradition string "1.1.1 Catholic Response"
                match = re.match(r'^(\d+\.\d+\.\d+)', response['tradition'])
                if match:
                    res_id = match.group(1)
                    id_map[res_id] = (c_idx, q_idx, r_idx)

    print(f"Mapped {len(id_map)} existing responses.")
    if '1.1.1' in id_map:
        print("ID 1.1.1 found in map")
    else:
        print("ID 1.1.1 NOT found in map")

    # Regex to match headers
    header_pattern = re.compile(r'^\s*\*+\s*(\d+\.\d+\.\d+)\s+(.*)$')
    
    updated_count = 0
    
    for filename in os.listdir(directory):
        if filename in ['philosophical_questions.org', 'data.json', 'database.html', 'merge_long_answers.py', 'scan_long_answers.py', 'inject_data.py', 'parse_data.py']:
            continue
            
        filepath = os.path.join(directory, filename)
        print(f"Processing file: {filename}")
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            current_id = None
            current_content = []
            
            for line in lines:
                match = header_pattern.search(line)
                if match:
                    # Process previous block
                    if current_id and current_content:
                        full_content = ''.join(current_content).strip()
                        if current_id in id_map:
                            c_idx, q_idx, r_idx = id_map[current_id]
                            old_content = data[c_idx]['questions'][q_idx]['responses'][r_idx]['content']
                            
                            # Debug print
                            print(f"Checking {current_id}: Old len {len(old_content)}, New len {len(full_content)}")

                            # Check if old content is a compilation (contains other IDs)
                            is_compilation = False
                            if '*** ' in old_content and len(old_content) > 10000:
                                is_compilation = True
                                print(f"Detected compilation in {current_id}")

                            # Only update if new content is significantly longer (e.g. > 20% longer) 
                            # or if old content was very short (< 200 chars) and new is longer
                            # or if old content was a compilation
                            if is_compilation or len(full_content) > len(old_content) * 1.2 or (len(old_content) < 200 and len(full_content) > len(old_content)):
                                data[c_idx]['questions'][q_idx]['responses'][r_idx]['content'] = full_content
                                updated_count += 1
                                print(f"Updated {current_id} (len: {len(full_content)})")
                            else:
                                # pass
                                print(f"Skipped {current_id}: Not longer enough")
                        else:
                            # pass
                            print(f"ID {current_id} not found in map")
                    
                    # Start new block
                    current_id = match.group(1)
                    current_content = []
                else:
                    if current_id:
                        current_content.append(line)
            
            # Process last block
            if current_id and current_content:
                full_content = ''.join(current_content).strip()
                if current_id in id_map:
                    c_idx, q_idx, r_idx = id_map[current_id]
                    old_content = data[c_idx]['questions'][q_idx]['responses'][r_idx]['content']
                    
                    if len(full_content) > len(old_content) * 1.2 or (len(old_content) < 200 and len(full_content) > len(old_content)):
                        data[c_idx]['questions'][q_idx]['responses'][r_idx]['content'] = full_content
                        updated_count += 1
                        print(f"Updated {current_id} (len: {len(full_content)})")

        except Exception as e:
            print(f"Error processing {filename}: {e}")

    print(f"Total responses updated: {updated_count}")
    
    # Save updated data
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    merge_long_answers('/Users/jaganat/.gemini/antigravity/scratch/questions_answers')
