import json

with open('data.json', 'r') as f:
    data = json.load(f)

for category in data:
    for question in category['questions']:
        for response in question['responses']:
            if response['tradition'].startswith('1.1.1 '):
                content = response['content']
                print(f"ID: {response['tradition']}")
                print(f"Length: {len(content)}")
                print(f"Snippet: {content[:100]}...")
                exit()
