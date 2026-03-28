#!/usr/bin/env python3
"""
Generate a 200-page philosophy book from the philosophical questions database.
Extracts questions and responses organized by category.
"""

import re
from collections import defaultdict, OrderedDict
from datetime import datetime

INPUT_FILE = "2philosophical_questions.org"
OUTPUT_FILE = "philosophy_book.org"

def parse_org_file(filename):
    """Parse the org file and extract all content."""
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Structure to hold everything
    categories = OrderedDict()

    current_category = None
    current_question = None
    current_tradition = None
    current_response_lines = []

    lines = content.split('\n')

    for i, line in enumerate(lines):
        # Category header: * 1. METAPHYSICS: What is the nature of reality?
        if re.match(r'^\* \d+\.', line):
            # Save previous
            if current_tradition and current_response_lines and current_category and current_question:
                response = ' '.join(current_response_lines).strip()
                if response:
                    if current_category not in categories:
                        categories[current_category] = OrderedDict()
                    if current_question not in categories[current_category]:
                        categories[current_category][current_question] = OrderedDict()
                    categories[current_category][current_question][current_tradition] = response

            match = re.match(r'^\* \d+\.\s*([A-Z][A-Z\s]+):', line)
            if match:
                current_category = match.group(1).strip()
            current_question = None
            current_tradition = None
            current_response_lines = []

        # Question header: ** 1.1 What exists? or ** 2.1.1 Are moral truths...
        elif re.match(r'^\*\* \d+\.\d+', line):
            # Save previous
            if current_tradition and current_response_lines and current_category and current_question:
                response = ' '.join(current_response_lines).strip()
                if response:
                    if current_category not in categories:
                        categories[current_category] = OrderedDict()
                    if current_question not in categories[current_category]:
                        categories[current_category][current_question] = OrderedDict()
                    categories[current_category][current_question][current_tradition] = response

            match = re.match(r'^\*\* [\d.]+\s+(.+)', line)
            if match:
                current_question = match.group(1).strip()
            current_tradition = None
            current_response_lines = []

        # Tradition response: *** 2.1.1 Catholic Response
        elif re.match(r'^\*\*\* ', line):
            # Save previous
            if current_tradition and current_response_lines and current_category and current_question:
                response = ' '.join(current_response_lines).strip()
                if response:
                    if current_category not in categories:
                        categories[current_category] = OrderedDict()
                    if current_question not in categories[current_category]:
                        categories[current_category][current_question] = OrderedDict()
                    categories[current_category][current_question][current_tradition] = response

            # Extract tradition name
            match = re.match(r'^\*\*\* [\d.]+\s+(.+?)\s*Response', line)
            if match:
                current_tradition = match.group(1).strip()
            else:
                match = re.match(r'^\*\*\* [\d.]+\s+(.+)', line)
                if match:
                    trad = match.group(1).strip()
                    current_tradition = trad.replace(' Response', '')
            current_response_lines = []

        # Response content (non-heading lines)
        elif line.strip() and not line.startswith('*') and not line.startswith('#'):
            current_response_lines.append(line.strip())

    # Save last item
    if current_tradition and current_response_lines and current_category and current_question:
        response = ' '.join(current_response_lines).strip()
        if response:
            if current_category not in categories:
                categories[current_category] = OrderedDict()
            if current_question not in categories[current_category]:
                categories[current_category][current_question] = OrderedDict()
            categories[current_category][current_question][current_tradition] = response

    return categories

def generate_book(categories):
    """Generate book content from parsed categories."""

    # Spanish translations for categories
    cat_spanish = {
        "METAPHYSICS": "Metafisica",
        "EPISTEMOLOGY": "Epistemologia",
        "ETHICS": "Etica",
        "POLITICAL PHILOSOPHY": "Filosofia Politica",
        "PHILOSOPHY OF MIND": "Filosofia de la Mente",
        "AESTHETICS": "Estetica",
        "PHILOSOPHY OF RELIGION": "Filosofia de la Religion",
        "PHILOSOPHY OF SCIENCE": "Filosofia de la Ciencia"
    }

    # Tradition name translations
    trad_spanish = {
        "Catholic": "Catolica",
        "Protestant": "Protestante",
        "Orthodox": "Ortodoxa",
        "Jewish": "Judia",
        "Islamic": "Islamica",
        "Hindu": "Hindu",
        "Buddhist": "Budista",
        "Confucian": "Confuciana",
        "Kantian": "Kantiana",
        "Utilitarian": "Utilitarista",
        "Relativist": "Relativista",
        "Humean": "Humeana",
        "Taoist": "Taoista",
        "Existentialist": "Existencialista",
        "Naturalist": "Naturalista",
        "Phenomenological": "Fenomenologica",
        "Analytic": "Analitica"
    }

    book = []

    # Header
    book.append(f"""#+TITLE: Grandes Preguntas, Diversas Respuestas
#+SUBTITLE: Filosofia Comparada de las Tradiciones del Mundo
#+AUTHOR: Compilacion de Respuestas Filosoficas
#+DATE: {datetime.now().strftime('%Y')}
#+LANGUAGE: es

#+LATEX_CLASS: book
#+LATEX_CLASS_OPTIONS: [11pt,twoside,openany]
#+LATEX_COMPILER: xelatex
#+OPTIONS: toc:2 num:t H:3

# Page size 6x9 inches for Amazon KDP
#+LATEX_HEADER: \\usepackage[paperwidth=6in,paperheight=9in]{{geometry}}
#+LATEX_HEADER: \\geometry{{inner=18mm, outer=13mm, top=18mm, bottom=18mm}}

# Typography
#+LATEX_HEADER: \\usepackage{{fontspec}}
#+LATEX_HEADER: \\setmainfont{{Libertinus Serif}}
#+LATEX_HEADER: \\usepackage[spanish]{{babel}}
#+LATEX_HEADER: \\usepackage{{setspace}}
#+LATEX_HEADER: \\setstretch{{1.12}}
#+LATEX_HEADER: \\setlength{{\\parindent}}{{1.2em}}
#+LATEX_HEADER: \\setlength{{\\parskip}}{{0.3em}}

# Headers
#+LATEX_HEADER: \\usepackage{{fancyhdr}}
#+LATEX_HEADER: \\pagestyle{{fancy}}
#+LATEX_HEADER: \\fancyhf{{}}
#+LATEX_HEADER: \\fancyhead[LE]{{\\small\\textsc{{Grandes Preguntas}}}}
#+LATEX_HEADER: \\fancyhead[RO]{{\\small\\textsc{{\\rightmark}}}}
#+LATEX_HEADER: \\fancyfoot[C]{{\\thepage}}
#+LATEX_HEADER: \\renewcommand{{\\headrulewidth}}{{0.4pt}}

# Chapter styling
#+LATEX_HEADER: \\usepackage{{titlesec}}
#+LATEX_HEADER: \\titleformat{{\\chapter}}[display]{{\\normalfont\\Large\\bfseries}}{{\\chaptertitlename\\ \\thechapter}}{{10pt}}{{\\LARGE}}

\\newpage

""")

    # Introduction
    book.append("""* Introduccion
:PROPERTIES:
:UNNUMBERED: t
:END:

A lo largo de la historia, los seres humanos han reflexionado sobre las mismas preguntas fundamentales: /Que existe realmente? Como debemos vivir? Existe Dios? Que es la justicia?/

Este libro presenta las respuestas de las principales tradiciones filosoficas y religiosas del mundo a estas preguntas eternas. No pretende determinar cual tradicion tiene "la razon", sino mostrar la riqueza del pensamiento humano en su busqueda de comprension.

** Como usar este libro

Cada capitulo aborda una rama de la filosofia. Dentro de cada capitulo encontraras preguntas especificas, seguidas de las respuestas sintetizadas de diversas tradiciones:

- *Tradiciones religiosas*: Catolicismo, Protestantismo, Ortodoxia, Judaismo, Islam, Hinduismo, Budismo
- *Tradiciones filosoficas*: Confucianismo, Taoismo, Kantianismo, Utilitarismo, Existencialismo

Las respuestas son necesariamente breves. Cada una representa siglos de desarrollo intelectual condensados en unas pocas lineas. Considere este libro como una puerta de entrada, no como la ultima palabra.

** Una invitacion al dialogo

La diversidad de respuestas no es un defecto sino una virtud. Cada tradicion ilumina aspectos diferentes de preguntas que, por su misma naturaleza, resisten respuestas simples.

Le invitamos a leer con mente abierta, a considerar perspectivas diferentes a la suya, y a usar estas paginas como punto de partida para su propia reflexion.

\\newpage

""")

    word_count = 500  # Intro words
    questions_included = 0
    max_questions = 80  # Limit for ~200 pages

    # Process categories
    for category, questions in categories.items():
        if questions_included >= max_questions:
            break

        cat_title = cat_spanish.get(category, category.title())
        book.append(f"\n* {cat_title}\n\n")

        for question, traditions in questions.items():
            if questions_included >= max_questions:
                break

            # Skip questions with very few responses
            if len(traditions) < 3:
                continue

            book.append(f"\n** {question}\n\n")
            questions_included += 1

            for tradition, response in traditions.items():
                if not response or len(response) < 30:
                    continue

                # Translate tradition name if available
                trad_name = tradition
                for eng, esp in trad_spanish.items():
                    if eng.lower() in tradition.lower():
                        trad_name = tradition.replace(eng, esp)
                        break

                # Clean up response
                response = response.strip()
                if len(response) > 600:
                    response = response[:597] + "..."

                book.append(f"*** Respuesta {trad_name}\n\n")
                book.append(f"{response}\n\n")
                word_count += len(response.split())

    # Conclusion
    book.append("""
* Conclusion
:PROPERTIES:
:UNNUMBERED: t
:END:

** Patrones que emergen

A traves de todas las tradiciones, ciertos temas aparecen una y otra vez:

1. *La busqueda de lo trascendente* - Ya sea Dios, Brahman, el Tao, o la Razon universal, las tradiciones reconocen algo que supera la experiencia ordinaria.

2. *La importancia de la virtud* - Todas las tradiciones valoran el cultivo del caracter moral, aunque difieran sobre que virtudes son centrales.

3. *La conexion entre conocimiento y transformacion* - El verdadero conocimiento no es meramente intelectual sino transformador de la persona.

4. *La tension entre individuo y comunidad* - Las tradiciones luchan por equilibrar la autonomia personal con la responsabilidad social.

** Diferencias irreducibles

Sin embargo, las diferencias son reales y significativas:

- *Sobre lo divino*: Personal vs. impersonal, uno vs. muchos, trascendente vs. inmanente
- *Sobre el conocimiento*: Revelacion vs. razon vs. experiencia mistica
- *Sobre la etica*: Mandato divino vs. ley natural vs. consecuencias
- *Sobre el destino humano*: Salvacion vs. liberacion vs. disolucion

** Una ultima reflexion

Estas preguntas no tienen respuestas definitivas porque tocan los limites de la comprension humana. Cada tradicion representa el esfuerzo sincero de seres humanos por dar sentido a la existencia.

La humildad intelectual es quiza la mayor leccion: reconocer que ninguna tradicion posee toda la verdad, y que el dialogo respetuoso entre perspectivas diferentes enriquece nuestra comprension comun.

* Glosario
:PROPERTIES:
:UNNUMBERED: t
:END:

- *Brahman* - En el hinduismo, la realidad ultima, absoluta e infinita
- *Dharma* - Ley cosmica, deber moral, ensenanza espiritual (hinduismo/budismo)
- *Nirvana* - Estado de liberacion del sufrimiento y el ciclo de renacimientos (budismo)
- *Tao* - El camino, principio cosmico inefable que subyace a toda realidad (taoismo)
- *Theosis* - Divinizacion o deificacion del ser humano (cristianismo oriental)
- *Tawhid* - La unicidad absoluta de Dios (islam)
- *Torah* - La ley revelada, los cinco libros de Moises (judaismo)
- *Logos* - Razon universal, palabra divina (filosofia griega/cristianismo)
- *Karma* - Ley de causa y efecto moral (hinduismo/budismo)
- *Samsara* - Ciclo de nacimiento, muerte y renacimiento (hinduismo/budismo)

""")

    return '\n'.join(book), word_count, questions_included

def main():
    print("=" * 60)
    print("GENERADOR DE LIBRO DE FILOSOFIA COMPARADA")
    print("=" * 60)

    print(f"\nLeyendo archivo: {INPUT_FILE}")
    categories = parse_org_file(INPUT_FILE)

    print(f"\nCategorias encontradas: {len(categories)}")
    total_questions = 0
    total_responses = 0
    for cat, questions in categories.items():
        q_count = len(questions)
        r_count = sum(len(traditions) for traditions in questions.values())
        total_questions += q_count
        total_responses += r_count
        print(f"  - {cat}: {q_count} preguntas, {r_count} respuestas")

    print(f"\nTotal: {total_questions} preguntas, {total_responses} respuestas")

    print("\nGenerando libro...")
    book_content, word_count, questions_used = generate_book(categories)

    estimated_pages = word_count // 275

    print(f"\n" + "=" * 60)
    print("RESULTADO:")
    print(f"  - Palabras generadas: {word_count:,}")
    print(f"  - Paginas estimadas: ~{estimated_pages}")
    print(f"  - Preguntas incluidas: {questions_used}")
    print("=" * 60)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(book_content)

    print(f"\nLibro guardado en: {OUTPUT_FILE}")
    print("\nPara exportar a PDF en Emacs:")
    print("  1. Abrir el archivo en Emacs")
    print("  2. Ejecutar: C-c C-e l p (org-latex-export-to-pdf)")
    print("\nO desde la terminal:")
    print(f"  emacs --batch -l org {OUTPUT_FILE} -f org-latex-export-to-pdf")

if __name__ == "__main__":
    main()
