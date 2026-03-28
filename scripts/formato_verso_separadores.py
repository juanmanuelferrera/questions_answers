#!/usr/bin/env python3
"""
Usa BEGIN_VERSE para que los asteriscos se rendericen correctamente
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Cambiar las líneas escapadas por bloques VERSE centrados
pattern = r'^\s+\\\* \\\* \\\*$'
replacement = '''#+BEGIN_VERSE
                              * * *
#+END_VERSE'''

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Separadores en formato VERSE (exporta correctamente)")
