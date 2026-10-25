#!/usr/bin/env python3
"""microNOVA-specific encodings: Ghidra vs novadis (github.com/majenkotech/novadis, BSD-3-Clause),
a Nova disassembler that knows the microNOVA stack instructions.
  novadis_check.py <ghidra-all.txt> <novadis -s -x output>
"""
import re
import sys
from collections import Counter

g = {}
for line in open(sys.argv[1]):
    off, ln, t = line.rstrip('\n').split(' ', 2)
    g[int(off, 16) // 2] = t
nd = {}
for line in open(sys.argv[2]):
    p = [x.strip() for x in line.split(':')]
    if len(p) >= 4:
        nd[int(p[0], 16)] = ':'.join(p[3:])
c = Counter()
for w, t in g.items():
    mn = t.split()[0]
    if mn not in ('PSHA', 'POPA', 'MTSP', 'MFSP', 'MTFP', 'MFFP', 'SAV', 'RET', 'MUL', 'DIV', 'TRAP'):
        continue
    n = nd.get(w, '')
    ok = n.split()[0] == mn if n else False
    ok = ok and re.findall(r'AC(\d)', t) == re.findall(r'AC(\d)', n)[:len(re.findall(r'AC(\d)', t))]
    if ok:
        c['same'] += 1
    elif mn in ('MTFP', 'MFFP') and (w >> 11) & 3 == 0 and n.startswith('NIO'):
        c['novadis bug: its NIO entry shadows MTFP/MFFP AC0'] += 1
    elif mn == 'TRAP':
        c['novadis bug: its ALC entries shadow TRAP'] += 1
    else:
        c['different'] += 1
        print(f'  {w:06o}: novadis "{n}" ghidra "{t}"')
print(dict(c))
