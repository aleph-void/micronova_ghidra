#!/usr/bin/env python3
"""Compare a dga listing with Ghidra's decode of the same words.

  asm_check.py <listing> <ghidra-all.txt>

ghidra-all.txt is DumpSlots.java output for all.bin (every word w at word address w), so a word
is looked up by its value; PC-relative targets are then relative to w. The source operands are
normalised: octal numbers by value, accumulators by number, "disp,1" to the absolute target.
"""
import re
import sys
from collections import Counter

g = {}
for line in open(sys.argv[2]):
    off, ln, t = line.rstrip('\n').split(' ', 2)
    g[int(off, 16) // 2] = t
DEV = {'HHC': 4, 'PROG': 5, 'TTI': 8, 'TTO': 9, 'DKT2': 24, 'DKT': 27, 'TTI1': 40, 'TTO1': 41,
       'DKT3': 56, 'DKT1': 59, 'MDV': 1}
c = Counter()
bad = []
for line in open(sys.argv[1]):
    m = re.match(r'^\d+ +[0-7]+ ([0-7]{6})\s+(.*)$', line.rstrip('\n'))
    if not m:
        continue
    w = int(m.group(1), 8)
    src = m.group(2).split(';')[0].strip()
    sm = re.match(r'(\S+)\s*(.*)$', src)
    smn, sops = sm.group(1).upper(), [x.strip() for x in sm.group(2).split(',')] if sm.group(2) else []
    gt = g[w]
    gm = re.match(r'(\S+)\s*(.*)$', gt)
    gmn, gops = gm.group(1).upper(), [x.strip() for x in gm.group(2).split(',')] if gm.group(2) else []
    # normalise Ghidra operands
    gn = []
    for o in gops:
        ind = o.startswith('@')
        o = o.lstrip('@')
        if re.fullmatch(r'AC[0-3]', o):
            o = o[2]
        elif o in DEV:
            o = str(DEV[o])
        elif re.fullmatch(r'-?0x[0-9a-f]+', o):
            o = str(int(o, 16))
        gn.append(('@' if ind else '') + o)
    # normalise source operands (octal; memory reference "disp,mode")
    sn = []
    memref = smn in ('JMP', 'JSR', 'ISZ', 'DSZ', 'LDA', 'STA')
    ops = list(sops)
    if memref:
        acc = [ops.pop(0)] if smn in ('LDA', 'STA') else []
        ind = ops[0].startswith('@')
        d = ops[0].lstrip('@')
        dv = int(d, 8)
        mode = int(ops[1]) if len(ops) > 1 else 0
        if mode == 1:
            ea = [str((w + dv) & 0x7fff)]      # word w sits at address w in all.bin
        elif mode == 0:
            ea = [str(dv)]
        else:
            ea = [str(dv), str(mode)]
        ea[0] = ('@' if ind else '') + ea[0]
        sn = acc + ea
    else:
        for o in ops:
            if o.upper() == 'CPU':
                sn.append('CPU')
            elif re.fullmatch(r'[0-7]+', o) and smn not in ('TRAP',):
                sn.append(str(int(o, 8)))
            else:
                sn.append(str(int(o, 8)) if re.fullmatch(r'[0-7]+', o) else o.upper())
        if smn.startswith(('SKP',)) and sn and sn[-1] == 'CPU':
            pass
    if smn == 'TRAP':
        sn = [sops[0], sops[1], str(int(sops[2], 8))]
    if smn.startswith('SKP') and gn == [] and gmn.startswith('SKP'):
        gn = ['CPU']
    if gmn.startswith('SKP') and gt.endswith('CPU'):
        gn = ['CPU']
    if smn == 'HALT' and gmn == 'HALT':
        sn = gn
    ok = smn == gmn and sn == gn
    if ok:
        c['same'] += 1
    elif smn == 'DIA' and gmn == 'READS' and sn[1:] == ['4'] and gn == sn[:1]:
        c['same (DIA ac,HHC is READS ac)'] += 1
    elif smn in ('MSKO', 'INTA') and gmn == smn and gn == ['0']:
        c['dga bug: MSKO/INTA ac assembled with AC0 (the operand is ORed into the device code, 77)'] += 1
    elif smn == 'IORST':
        c['dga IORST is the Nova DICC 0,CPU'] += 1
    else:
        c['different'] += 1
        if len(bad) < 15:
            bad.append(f'{w:06o} src "{src}" ghidra "{gt}"  ({smn} {sn} / {gmn} {gn})')
print(dict(c))
if bad:
    print('\n'.join(bad))
