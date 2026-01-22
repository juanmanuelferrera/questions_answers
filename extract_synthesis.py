#!/usr/bin/env python3
"""
Extract coincidences and enriching differences from philosophical traditions.
Analyzes responses to find common ground and complementary perspectives.
"""

import re
from collections import defaultdict, OrderedDict

INPUT_FILE = "2philosophical_questions.org"
OUTPUT_FILE = "BOOK_SYNTHESIS.org"

# Key questions to analyze (the most complete ones mapped to human problems)
KEY_QUESTIONS = {
    "existence": [
        "What exists?",
        "What is the relationship between being and existence?",
    ],
    "consciousness": [
        "What is the nature of consciousness?",
        "What is the nature of mind?",
    ],
    "free_will": [
        "Do we have free will?",
    ],
    "knowledge": [
        "What is the source of knowledge?",
        "What are the limits of human knowledge?",
    ],
    "truth": [
        "Is truth absolute or relative?",
        "What makes a statement true?",
    ],
    "faith_reason": [
        "What is the relationship between faith and reason?",
    ],
    "time": [
        "Is time real or an illusion?",
        "What is the nature of time and space?",
    ],
    "mind_body": [
        "What is the relationship between mind and body?",
    ],
    "causation": [
        "What is the nature of causation?",
    ],
    "material_immaterial": [
        "What distinguishes material from immaterial reality?",
    ],
    "ethics": [
        "What is the source of moral authority?",
        "What makes an action right or wrong?",
    ],
    "suffering": [
        "Does suffering have meaning?",
        "How can evil exist if God is all-good and all-powerful?",
    ],
}

# Group traditions into families for synthesis
TRADITION_FAMILIES = {
    "Cristianismo": ["Catholic", "Protestant", "Orthodox", "Oriental Orthodox", "Evangelical"],
    "Islam": ["Islamic", "Sunni", "Shia", "Sufi"],
    "Judaismo": ["Jewish", "Kabbalah", "Reform Judaism"],
    "Hinduismo": ["Hindu", "Advaita", "Vishishtadvaita", "Vaishnavism"],
    "Budismo": ["Buddhist", "Theravada", "Mahayana", "Zen", "Vajrayana"],
    "Tradiciones Chinas": ["Confucian", "Taoist", "Chinese"],
    "Filosofia Occidental": ["Platonic", "Aristotelian", "Stoic", "Kantian", "Existentialist"],
    "Tradiciones Indigenas": ["Native American", "African Traditional", "Indigenous"],
}

def find_family(tradition_name):
    """Find which family a tradition belongs to."""
    for family, keywords in TRADITION_FAMILIES.items():
        for keyword in keywords:
            if keyword.lower() in tradition_name.lower():
                return family
    return "Otras"

def parse_org_file(filename):
    """Parse the org file and extract responses by question."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    questions_data = defaultdict(dict)
    current_question = None
    current_tradition = None
    current_response = []

    for line in content.split('\n'):
        # Question header
        if re.match(r'^\*\* \d+\.\d+', line):
            # Save previous
            if current_tradition and current_response and current_question:
                response_text = ' '.join(current_response).strip()
                questions_data[current_question][current_tradition] = response_text

            match = re.match(r'^\*\* [\d.]+\s+(.+)', line)
            if match:
                current_question = match.group(1).strip()
            current_tradition = None
            current_response = []

        # Tradition response
        elif re.match(r'^\*\*\* ', line):
            # Save previous
            if current_tradition and current_response and current_question:
                response_text = ' '.join(current_response).strip()
                questions_data[current_question][current_tradition] = response_text

            match = re.match(r'^\*\*\* [\d.]+\s+(.+?)\s*Response', line)
            if match:
                current_tradition = match.group(1).strip()
            current_response = []

        # Response content
        elif line.strip() and not line.startswith('*') and not line.startswith('#'):
            current_response.append(line.strip())

    # Save last
    if current_tradition and current_response and current_question:
        response_text = ' '.join(current_response).strip()
        questions_data[current_question][current_tradition] = response_text

    return questions_data

def extract_key_concepts(response):
    """Extract key philosophical concepts from a response."""
    # Key concept patterns
    concepts = []

    # Look for common philosophical terms
    patterns = [
        (r'\b(divine|God|transcendent|sacred|holy)\b', 'trascendencia'),
        (r'\b(soul|spirit|consciousness|mind|self)\b', 'interioridad'),
        (r'\b(illusion|maya|appearance|phenomenal)\b', 'ilusión'),
        (r'\b(liberation|salvation|enlightenment|freedom|moksha|nirvana)\b', 'liberación'),
        (r'\b(karma|causation|cause|effect|consequence)\b', 'causalidad'),
        (r'\b(suffering|pain|evil|dukkha)\b', 'sufrimiento'),
        (r'\b(love|compassion|mercy|grace)\b', 'amor/compasión'),
        (r'\b(truth|reality|being|existence)\b', 'verdad/realidad'),
        (r'\b(virtue|ethics|moral|duty|dharma)\b', 'virtud/deber'),
        (r'\b(unity|oneness|non-dual|interconnected)\b', 'unidad'),
        (r'\b(transformation|change|becoming|process)\b', 'transformación'),
        (r'\b(eternal|timeless|permanent|unchanging)\b', 'eternidad'),
        (r'\b(revelation|scripture|tradition|teaching)\b', 'revelación'),
        (r'\b(reason|rational|logic|intellect)\b', 'razón'),
        (r'\b(experience|practice|meditation|contemplation)\b', 'práctica'),
    ]

    response_lower = response.lower()
    for pattern, concept in patterns:
        if re.search(pattern, response_lower):
            concepts.append(concept)

    return list(set(concepts))

def find_common_themes(responses_by_family):
    """Find themes common across all or most families."""
    all_concepts = defaultdict(int)
    family_concepts = {}

    for family, response in responses_by_family.items():
        concepts = extract_key_concepts(response)
        family_concepts[family] = concepts
        for c in concepts:
            all_concepts[c] += 1

    # Concepts present in 50%+ of families
    threshold = len(responses_by_family) / 2
    common = [c for c, count in all_concepts.items() if count >= threshold]

    return common, family_concepts

def analyze_differences(responses_by_family, family_concepts):
    """Identify enriching differences (complementary perspectives)."""
    differences = []

    # Find unique concepts per family
    all_concepts = set()
    for concepts in family_concepts.values():
        all_concepts.update(concepts)

    for family, concepts in family_concepts.items():
        unique = [c for c in concepts if sum(1 for f, cs in family_concepts.items() if c in cs) <= 2]
        if unique:
            differences.append({
                'family': family,
                'unique_emphasis': unique,
                'response_snippet': responses_by_family.get(family, '')[:200]
            })

    return differences

def generate_synthesis_document(questions_data):
    """Generate the synthesis document."""

    output = []
    output.append("""#+TITLE: Síntesis Filosófica: Coincidencias y Diferencias Enriquecedoras
#+SUBTITLE: Análisis Comparativo de las Grandes Tradiciones
#+DATE: 2026

* Introducción

Este documento presenta el análisis de las respuestas de las grandes tradiciones
filosóficas y religiosas a las preguntas fundamentales de la existencia.

Para cada tema se identifican:
1. *Coincidencias*: Lo que la mayoría de tradiciones comparten
2. *Diferencias enriquecedoras*: Perspectivas únicas que complementan la comprensión

""")

    chapter_titles = {
        "existence": "¿Qué Existe Realmente?",
        "consciousness": "¿Qué es la Consciencia?",
        "free_will": "¿Tenemos Libre Albedrío?",
        "knowledge": "¿Qué Podemos Conocer?",
        "truth": "¿Es la Verdad Absoluta o Relativa?",
        "faith_reason": "¿Fe o Razón?",
        "time": "¿Qué es el Tiempo?",
        "mind_body": "¿Mente y Cuerpo son Uno?",
        "causation": "¿Qué Causa Qué?",
        "material_immaterial": "¿Qué es lo Material y lo Espiritual?",
        "ethics": "¿Cómo Debo Vivir?",
        "suffering": "¿Por Qué Sufrimos?",
    }

    for theme_key, question_list in KEY_QUESTIONS.items():
        title = chapter_titles.get(theme_key, theme_key.title())
        output.append(f"\n* {title}\n")

        # Gather all responses for this theme
        all_responses = {}
        for q in question_list:
            if q in questions_data:
                for tradition, response in questions_data[q].items():
                    family = find_family(tradition)
                    if family not in all_responses:
                        all_responses[family] = response

        if not all_responses:
            output.append("/(No hay suficientes respuestas para este tema)/\n")
            continue

        # Find common themes
        common_themes, family_concepts = find_common_themes(all_responses)

        # Find differences
        differences = analyze_differences(all_responses, family_concepts)

        # Write coincidences
        output.append("\n** Coincidencias (Lo que Comparten)\n")
        if common_themes:
            output.append("Las tradiciones coinciden en reconocer:\n")
            for theme in common_themes:
                output.append(f"- *{theme.title()}*\n")
        else:
            output.append("/(Análisis pendiente - revisar manualmente)/\n")

        # Write sample responses grouped by family
        output.append("\n** Voces de las Tradiciones\n")
        for family, response in sorted(all_responses.items()):
            if response:
                snippet = response[:300] + "..." if len(response) > 300 else response
                output.append(f"\n*** {family}\n")
                output.append(f"{snippet}\n")

        # Write enriching differences
        output.append("\n** Diferencias Enriquecedoras\n")
        output.append("Cada tradición aporta un énfasis único:\n\n")

        for diff in differences:
            if diff['unique_emphasis']:
                output.append(f"- *{diff['family']}* enfatiza: {', '.join(diff['unique_emphasis'])}\n")

        # Synthesis prompt (for manual completion)
        output.append("\n** Síntesis Narrativa (Para Desarrollar)\n")
        output.append("#+BEGIN_QUOTE\n")
        output.append("[Aquí va la síntesis narrativa que conecta las perspectivas]\n")
        output.append("#+END_QUOTE\n")

    return '\n'.join(output)

def main():
    print("Parsing philosophical questions database...")
    questions_data = parse_org_file(INPUT_FILE)
    print(f"Found {len(questions_data)} questions")

    print("\nGenerating synthesis document...")
    synthesis = generate_synthesis_document(questions_data)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(synthesis)

    print(f"\nSynthesis saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
