#!/usr/bin/env python3
import re

with open('LIBRO_COMPLETO.org', 'r', encoding='utf-8') as f:
    content = f.read()

# Cambiar "** I." (solo número) por separador ***
content = re.sub(r'^\*\* [IVX]+\.\s*$', '***', content, flags=re.MULTILINE)

# Cambiar "** I. Título" por "** Título" (eliminar número romano)
content = re.sub(r'^\*\* [IVX]+\.\s+(.+)$', r'** \1', content, flags=re.MULTILINE)

with open('LIBRO_COMPLETO.org', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Números romanos eliminados")
print("   - Secciones sin título: cambiadas a ***")
print("   - Secciones con título: eliminado número romano")
