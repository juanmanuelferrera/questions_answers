#!/usr/bin/env python3
"""
Simplifica separadores a formato plano que exporta correctamente
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar los bloques BEGIN_CENTER y dejar solo una línea con espacios + asteriscos
# Esto exporta mejor a LaTeX/HTML
pattern = r'#\+BEGIN_CENTER\n\* \* \*\n#\+END_CENTER'
replacement = '                                   * * *'

content = re.sub(pattern, replacement, content)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Separadores simplificados a formato plano (exporta correctamente)")
