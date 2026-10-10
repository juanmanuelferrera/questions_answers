import re
import json

def parse_org_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    data = []
    current_category = None
    current_question = None
    current_response = None
    
    # Regex patterns
    category_pattern = re.compile(r'^\* (.*)')
    question_pattern = re.compile(r'^\*\* (.*)')
    response_pattern = re.compile(r'^\*\*\* (.*)')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for Category (* Level 1)
        cat_match = category_pattern.match(line)
        if cat_match:
            current_category = {
                "title": cat_match.group(1),
                "questions": []
            }
            data.append(current_category)
            current_question = None
            continue

        # Check for Question (** Level 2)
        q_match = question_pattern.match(line)
        if q_match:
            if current_category:
                current_question = {
                    "text": q_match.group(1),
                    "responses": []
                }
                current_category["questions"].append(current_question)
                current_response = None
            continue

        # Check for Response (*** Level 3)
        r_match = response_pattern.match(line)
        if r_match:
            if current_question:
                current_response = {
                    "tradition": r_match.group(1),
                    "content": ""
                }
                current_question["responses"].append(current_response)
            continue

        # Content lines
        if current_response:
            current_response["content"] += line + " "

    # Clean up whitespace
    for cat in data:
        for q in cat["questions"]:
            for r in q["responses"]:
                r["content"] = r["content"].strip()

    return data

if __name__ == "__main__":
    input_file = "/Users/jaganat/.gemini/antigravity/scratch/questions_answers/philosophical_questions.org"
    output_file = "/Users/jaganat/.gemini/antigravity/scratch/questions_answers/data.json"
    
    print(f"Parsing {input_file}...")
    parsed_data = parse_org_file(input_file)
    
    print(f"Found {len(parsed_data)} categories.")
    total_questions = sum(len(c["questions"]) for c in parsed_data)
    print(f"Found {total_questions} questions.")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(parsed_data, f, indent=2)
    
    print(f"Saved JSON to {output_file}")
