#!/usr/bin/env python3
"""
Usa marcadores de exportación explícitos para HTML y LaTeX
que garantizan centrado correcto
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar bloques VERSE por marcadores de exportación
pattern = r'#\+BEGIN_VERSE\n\s+\* \* \*\n#\+END_VERSE'

# Usar función lambda para evitar problemas de escaping en re.sub
def make_separator(match):
    html_line = '#+HTML: <p style="text-align:center;">* * *</p>'
    latex_line = '#+LATEX: \\begin{center}* * *\\end{center}'
    return html_line + '\n' + latex_line

content = re.sub(pattern, make_separator, content)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Separadores con marcadores de exportación explícitos (HTML + LaTeX)")
