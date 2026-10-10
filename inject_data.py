import os
import json

def inject_data(directory):
    data_path = os.path.join(directory, 'data.json')
    html_path = os.path.join(directory, 'database.html')

    with open(data_path, 'r', encoding='utf-8') as f:
        data_content = f.read()

    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Find the script tag containing "const database ="
    start_marker = "const database ="
    end_marker = "// ... rest of the script" # This marker might not be reliable if I changed the code.
    # Better to find the start and just replace the variable declaration until the semicolon?
    # Or just replace the whole block if I can identify it.
    
    # Let's look for the pattern: const database = [...];
    # We'll use regex to be safe.
    # Note: The JSON might be huge, so regex might be slow or hit limits.
    # But since we are replacing the *old* content, we can search for `const database = [` and the closing `];`.
    
    # Actually, the previous view of database.html showed:
    # const database = [ ... ];
    
    # Let's try to construct the new HTML string.
    # We'll look for `const database = ` and replace everything until the next variable or function or just the matching bracket.
    # But matching brackets with regex is hard.
    
    # Alternative: Read the HTML, split by `const database =`, take the first part, 
    # then find where the array ends in the second part?
    # That's risky if I don't know exactly where it ends.
    
    # Let's assume the structure is:
    # <script>
    #     const database = [...];
    #     const searchInput = ...
    
    # I'll use a placeholder in the HTML if I can, but I can't easily modify it first without knowing where it is.
    
    # Let's try to find the start index.
    start_idx = html_content.find("const database = [")
    if start_idx == -1:
        print("Could not find 'const database = [' in HTML")
        return

    # Find the end of the array. This is tricky.
    # But I know the next line usually starts with "const searchInput" or "const traditionFilter".
    # Let's look for the next variable declaration.
    next_var_idx = html_content.find("const searchInput =", start_idx)
    if next_var_idx == -1:
        # Maybe it's traditionFilter?
        next_var_idx = html_content.find("const traditionFilter =", start_idx)
    
    if next_var_idx == -1:
         print("Could not find next variable declaration")
         return
         
    # The end of the array should be before next_var_idx.
    # It should be a semicolon and newline.
    # Let's just replace from start_idx to next_var_idx with the new data.
    # But wait, next_var_idx includes "const searchInput ...".
    # So we replace up to next_var_idx.
    
    # We need to make sure we close the array properly and add a semicolon.
    new_data_js = f"const database = {data_content};\n    "
    
    new_html = html_content[:start_idx] + new_data_js + html_content[next_var_idx:]
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(new_html)
        
    print("Successfully injected data into database.html")

if __name__ == "__main__":
    inject_data('/Users/jaganat/.gemini/antigravity/scratch/questions_answers')
