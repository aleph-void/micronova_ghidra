#!/usr/bin/env python3
"""Compare a Ghidra listing (RealCheck.java, word addresses) with MAME's Nova disassembly at the
same addresses (normalised and classified as in compare.py), and report which source
instructions of the listing (lst2bin.py words file) Ghidra did not disassemble.

  listing_check.py <ghidra.lst> <mame.txt> <words-file>
"""
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C  # noqa: E402

g = {}
for line in open(sys.argv[1]):
    a, b, t = line.rstrip('\n').split(' ', 2)
    g[int(a, 16)] = t
mm = {}
for line in open(sys.argv[2]):
    m = re.match(r'^([0-9a-f]+): ([0-9a-f]{4})\s+(.*)$', line.rstrip('\n'))
    if m:
        mm[int(m.group(1), 16)] = m.group(3)
c = Counter()
diff = []
for a, t in sorted(g.items()):
    gn, go = C.toks(t, False)
    mn, mo = C.toks(mm[a], True)
    if (gn, go) == (mn, mo):
        c['identical'] += 1
    elif gn in ('PSHA', 'POPA', 'MTSP', 'MFSP', 'MTFP', 'MFFP', 'SAV', 'RET', 'TRAP', 'READS', 'IORST', 'HALT'):
        c['microNOVA form (see compare.py classes)'] += 1
    else:
        c['different'] += 1
        diff.append(f'{a:05o}: mame "{mm[a]}" ghidra "{t}"')
print(f'vs MAME: {sum(c.values())} instructions: {dict(c)}')
for d in diff[:20]:
    print('  ' + d)
src = {}
for line in open(sys.argv[3]):
    p = line.rstrip('\n').split(' ', 2)
    src[int(p[0], 8)] = p[2] if len(p) > 2 else ''
MN = re.compile(r'^(com|neg|mov|inc|adc|sub|add|and)[zoc]?[lrs]?#?$|^(lda|sta|jmp|jsr|isz|dsz|nio[scp]?|'
                r'd[io][abc][scp]?|skp(bn|bz|dn|dz)|psha|popa|sav|ret|mtsp|mfsp|mtfp|mffp|mul|div|trap|'
                r'inten|intds|inta|msko|iorst|halt|reads)$', re.I)


def is_code(s):
    s = s.split(';')[0]
    s = re.sub(r'^\s*\w+:', '', s).strip()
    return bool(s) and bool(MN.match(s.split()[0]))


code = [a for a, s in src.items() if is_code(s)]
miss = [a for a in code if a not in g]
print(f'source instruction lines: {len(code)}, not disassembled: {len(miss)}')
for a in miss[:20]:
    print(f'  {a:05o}: {src[a].strip()}')
