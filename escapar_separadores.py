#!/usr/bin/env python3
"""
Escapa los asteriscos para que Org-mode no los interprete como lista/heading
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Cambiar las líneas de separadores con espacios + * * *
# por asteriscos escapados centrados
pattern = r'^\s+\* \* \*$'
replacement = r'                              \* \* \*'

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Asteriscos escapados para exportación correcta en Org-mode")
