#!/usr/bin/env python3
"""Compare Ghidra's decode of every 16-bit word (DumpSlots.java, slot 2) with MAME's Nova
disassembler (unidasm -arch nova) for the microNOVA module.

  compare.py <ghidra.txt> <mame.txt> [--list N]

MAME implements the plain Nova. The microNOVA gives some encodings other meanings; those are
"explained" when the encoding is what the microNOVA Programmer's Reference (DG 015-000050) gives:
  - device 01: PSHA/POPA (DIB, f=-/C), MTSP/MFSP (DOA), MTFP/MFFP (NIO), SAV/RET (DIC 0), where
    MAME shows the Nova I/O form to device MDV
  - TRAP acs,acd,n: a no-load ALC instruction with "never skip" (MAME shows the ALC form)
  - device 77 (CPU): IORST/RTCDS/RTCEN are DOA 0/1/2,CPU (MAME: DOA); MAME's Nova IORST (DIC
    0,CPU) and READS (DIA ac,CPU) are not microNOVA instructions; HALT is DOC 0,CPU with any f
  - device 04: READS is DIA ac,HHC (MAME: DIA ac,MAP2)
Normalisation: numbers by value (MAME octal, Ghidra hex), accumulators ACn -> n, device names
-> codes, MAME's padding.
"""
import re
import sys
from collections import Counter, defaultdict

MAME_DEV = {'MDV': 1, 'MAP0': 2, 'MAP1': 3, 'MAP2': 4, 'MCAT': 6, 'MCAR': 7, 'TTI': 8, 'TTO': 9,
            'PTR': 10, 'PTP': 11, 'RTC': 12, 'PLT': 13, 'CDR': 14, 'LPT': 15, 'DSK': 16,
            'ADCV': 17, 'MTA': 18, 'DACV': 19, 'DCM': 20, 'DKP': 27, 'SCR': 32, 'SCT': 33, 'CPU': 63}
G_DEV = {'MDV': 1, 'HHC': 4, 'PROG': 5, 'TTI': 8, 'TTO': 9, 'DKT2': 24, 'DKT': 27, 'TTI1': 40,
         'TTO1': 41, 'DKT3': 56, 'DKT1': 59, 'CPU': 63}


def toks(text, mame):
    m = re.match(r'(\S+)\s*(.*)$', text.strip())
    mn, rest = m.group(1).upper(), m.group(2)
    out = []
    for o in [x.strip() for x in rest.split(',')] if rest else []:
        ind = o.startswith('@')
        o = o.lstrip('@')
        if mame:
            if o in MAME_DEV:
                v = str(MAME_DEV[o])
            elif re.fullmatch(r'-?[0-7]+', o) and (len(o.lstrip('-')) == 5 or o.lstrip('-').startswith('0') or mn.startswith(('NIO', 'DI', 'DO', 'SKP')) or True):
                v = str(int(o, 8))
            else:
                v = o
        else:
            if o in G_DEV:
                v = str(G_DEV[o])
            elif re.fullmatch(r'AC[0-3]', o):
                v = o[2]
            elif re.fullmatch(r'-?0x[0-9a-fA-F]+', o):
                v = str(int(o, 16))
            else:
                v = o
        out.append(('@' if ind else '') + v)
    return mn, out


def main():
    nlist = int(sys.argv[sys.argv.index('--list') + 1]) if '--list' in sys.argv else 0
    g = {}
    for line in open(sys.argv[1]):
        off, ln, text = line.rstrip('\n').split(' ', 2)
        g[int(off, 16) // 2] = text
    mm = {}
    for line in open(sys.argv[2]):
        m = re.match(r'^([0-9a-f]+): ([0-9a-f]{4})\s+(.*)$', line.rstrip('\n'))
        if m:
            mm[int(m.group(1), 16)] = m.group(3)
    c, d = Counter(), defaultdict(list)
    for w in sorted(g):
        gt, mt = g[w], mm[w]
        if gt.startswith('BAD'):
            c['ghidra-only invalid'] += 1
            d['ghidra rejects'].append(f'{w:06o}: mame "{mt}"')
            continue
        gn, go = toks(gt, False)
        mn, mo = toks(mt, True)
        # MAME prints MUL/DIV/INTEN/... from the instruction bits
        if (gn, go) == (mn, mo):
            c['same'] += 1
            continue
        ioop, ctl, dev, acc = (w >> 8) & 7, (w >> 6) & 3, w & 63, (w >> 11) & 3
        io = (w >> 13) == 3
        why = None
        nova_io = ['NIO', 'DIA', 'DOA', 'DIB', 'DOB', 'DIC', 'DOC', 'SKP'][ioop] + ' SCP'[ctl].strip()
        if io and dev == 1 and gn in ('PSHA', 'POPA', 'MTSP', 'MFSP', 'MTFP', 'MFFP', 'SAV', 'RET'):
            exp = {'PSHA': (3, 0), 'POPA': (3, 2), 'MTSP': (2, 0), 'MFSP': (2, 2), 'MTFP': (0, 0),
                   'MFFP': (0, 2), 'SAV': (5, 0), 'RET': (5, 2)}[gn]
            if (ioop, ctl) == exp and mn == nova_io:
                why = 'microNOVA stack instruction (device 01), MAME shows the Nova I/O form'
        elif gn == 'TRAP' and w >> 15 and (w & 15) == 8 and mn.endswith('#'):
            why = 'microNOVA TRAP (no-load, never skip), MAME shows the ALC form'
        elif io and dev == 63 and gn in ('IORST', 'RTCDS', 'RTCEN', 'IORSTS', 'IORSTC', 'IORSTP',
                                         'RTCDSS', 'RTCDSC', 'RTCDSP', 'RTCENS', 'RTCENC', 'RTCENP') and ioop == 2:
            why = 'microNOVA IORST/RTCDS/RTCEN are DOA 0/1/2,CPU'
        elif io and dev == 63 and mn in ('IORST', 'READS') or (io and dev == 63 and gn == 'HALT' and ioop == 6):
            why = 'MAME Nova CPU mnemonic (IORST = DIC 0,CPU, READS = DIA ac,CPU) or HALT with S/C/P; microNOVA CPU device'
        elif io and dev == 4 and gn == 'READS' and ioop == 1 and ctl == 0:
            why = 'microNOVA READS is DIA ac,HHC'
        elif io and dev == 63 and ioop == 0 and mn in ('INTEN', 'INTDS') and gn == mn:
            why = None
        if why:
            c['explained'] += 1
            d['explained: ' + why].append(f'{w:06o}: mame "{mt}" ghidra "{gt}"')
        else:
            c['different'] += 1
            d['different ' + gn].append(f'{w:06o}: mame "{mt}" ghidra "{gt}"')
    tot = sum(c.values())
    print(f'{c["same"]}/{tot} same, {c["explained"]} explained, {c["different"]} different, '
          f'{c["ghidra-only invalid"]} rejected by Ghidra')
    for k in sorted(d, key=lambda k: -len(d[k])):
        print(f'  {len(d[k]):6d} {k}')
        for e in d[k][:nlist]:
            print(f'           {e}')


if __name__ == '__main__':
    main()
