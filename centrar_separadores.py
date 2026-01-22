#!/usr/bin/env python3
"""
Convierte *** (línea completa) en * * * centrado
según la práctica literaria estándar
"""

import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar líneas que son solo *** por el formato literario centrado
# Solo líneas que son exactamente *** (no las que tienen texto después)
content = re.sub(r'^(\*\*\*)$', r'#+BEGIN_CENTER\n* * *\n#+END_CENTER', content, flags=re.MULTILINE)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Separadores centrados en formato literario estándar (* * *)")
