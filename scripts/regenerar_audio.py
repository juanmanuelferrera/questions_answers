#!/usr/bin/env python3
"""
Regenera LIBRO_COMPLETO_AUDIO.txt desde LIBRO_COMPLETO.org
Elimina todo el markup de Org-mode para optimizar para TTS
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Eliminar directivas de Org-mode al inicio
content = re.sub(r'#\+TITLE:.*\n', '', content)
content = re.sub(r'#\+AUTHOR:.*\n', '', content)
content = re.sub(r'#\+DATE:.*\n', '', content)
content = re.sub(r'#\+OPTIONS:.*\n', '', content)

# Eliminar directivas de exportación HTML y LaTeX
content = re.sub(r'#\+HTML:.*\n', '', content)
content = re.sub(r'#\+LATEX:.*\n', '', content)
content = re.sub(r'#\+BEGIN_HTML.*?#\+END_HTML\n?', '', content, flags=re.DOTALL)
content = re.sub(r'#\+BEGIN_LATEX.*?#\+END_LATEX\n?', '', content, flags=re.DOTALL)

# Eliminar bloques CENTER pero mantener contenido
content = re.sub(r'#\+BEGIN_CENTER\n', '', content)
content = re.sub(r'#\+END_CENTER\n', '', content)

# Eliminar bloques QUOTE pero mantener contenido
content = re.sub(r'#\+BEGIN_QUOTE\n', '', content)
content = re.sub(r'#\+END_QUOTE\n', '', content)

# Eliminar bloques VERSE pero mantener contenido
content = re.sub(r'#\+BEGIN_VERSE\n', '', content)
content = re.sub(r'#\+END_VERSE\n', '', content)

# Convertir headers de Org-mode a texto simple
# * CAPÍTULO 1 -> CAPÍTULO 1
content = re.sub(r'^\* (CAPÍTULO \d+.*)', r'\1', content, flags=re.MULTILINE)
# ** Sección -> Sección (con línea en blanco antes)
content = re.sub(r'^\*\* (.+)', r'\n\1', content, flags=re.MULTILINE)
# *** Subsección -> Subsección
content = re.sub(r'^\*\*\* (.+)', r'\1', content, flags=re.MULTILINE)

# Limpiar énfasis de Org-mode
content = re.sub(r'/([^/]+)/', r'\1', content)  # /cursiva/ -> cursiva
content = re.sub(r'\*([^\*]+)\*', r'\1', content)  # *negrita* -> negrita (solo single *)

# Limpiar líneas que solo tienen guiones o líneas separadoras
content = re.sub(r'^-{3,}\s*$', '', content, flags=re.MULTILINE)
content = re.sub(r'^─+\s*$', '', content, flags=re.MULTILINE)

# Limpiar múltiples líneas en blanco
content = re.sub(r'\n{4,}', '\n\n\n', content)

# Limpiar espacios al final de líneas
content = re.sub(r' +\n', '\n', content)

# Asegurar que el archivo termina con newline
if not content.endswith('\n'):
    content += '\n'

with open('LIBRO_COMPLETO_AUDIO.txt', 'w', encoding='utf-8') as f:
    f.write(content)

# Contar palabras y caracteres
words = len(content.split())
chars = len(content)

print(f"✅ LIBRO_COMPLETO_AUDIO.txt regenerado")
print(f"   Palabras: {words:,}")
print(f"   Caracteres: {chars:,}")
