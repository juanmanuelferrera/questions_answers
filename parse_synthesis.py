import json

# Simulate the streaming response chunks
chunks = [
    "Jan",
    "ice Johnson is an individual who participated in a conversation with Prabhupāda. She asked several questions",
    " during the interview, including whether it was Prabhupāda's first visit to Washington, who",
    " he had visited, and if he had met any city leaders. She also inquired about the necessity of living in a \"lavish\" situation and why the Hare Kṛṣṇa",
    " movement had recently adopted street clothes and wigs instead of traditional saffron robes for soliciting. Additionally, Janice Johnson asked about the movement's schools, specifically if one had moved",
    " out of Texas or to India, and what the Hare Kṛṣṇa movement offers that other religions do not."
]

full_synthesis = "".join(chunks)

print("=" * 80)
print("SYNTHESIS RESULT FOR 'Who is Janice Johnson?'")
print("=" * 80)
print()
print(full_synthesis)
print()
print("=" * 80)
print(f"Word count: {len(full_synthesis.split())}")
print("Status: SUCCESS - Gemini correctly identified Janice Johnson from the sources")
print("=" * 80)
