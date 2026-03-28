#!/usr/bin/env python3
"""
Convierte *** en * * * centrado para el archivo de audio
"""

import re

with open('LIBRO_COMPLETO_AUDIO.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar líneas que son solo *** por * * * centrado con espacios
# Centrado aproximado a 40 espacios (asumiendo línea de 80 caracteres)
content = re.sub(r'^(\*\*\*)$', r'                                        * * *', content, flags=re.MULTILINE)

with open('LIBRO_COMPLETO_AUDIO.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Separadores de audio centrados (* * *)")
