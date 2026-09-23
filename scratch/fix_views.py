"""
Fix: elimina el bloque corrupto/duplicado de views.py (lineas 1244-1439)
Deja solo la version correcta del cronograma intercalado (lineas 1440+)
"""
import sys

filepath = r'c:\Users\varga\OneDrive\Desktop\Django\interfichas\views.py'

with open(filepath, 'rb') as f:
    raw = f.read()

content = raw.decode('utf-8', errors='replace')
lines = content.splitlines(keepends=True)
print(f'Total lineas antes: {len(lines)}')

# Lineas a conservar:
# 1-1243 (original hasta el final del OCR)  --> indices 0-1242
# 1440-1549 (version correcta del cronograma) --> indices 1439-1548

lineas_buenas = lines[0:1243] + lines[1439:]
print(f'Total lineas despues: {len(lineas_buenas)}')

# Guardar con encoding UTF-8
resultado = ''.join(lineas_buenas)
with open(filepath, 'w', encoding='utf-8') as f:
    f.write(resultado)

print('Archivo corregido exitosamente!')

# Verificar sintaxis Python
import ast, sys
try:
    ast.parse(resultado)
    print('Sintaxis Python: OK')
except SyntaxError as e:
    print(f'ERROR de sintaxis: {e}')
    sys.exit(1)
