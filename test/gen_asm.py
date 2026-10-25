#!/usr/bin/env python3
"""Assembler corpus: Nova/microNOVA source lines with random operands for dga, the DG Nova
assembler of "The Didactic PDP-8 and DG Nova Assembler" (github.com/napobear/dpa, GPL-2.0).
Only numeric operands are used (dga's location counter is not usable in this build).
  gen_asm.py <out.sr> [rounds]
"""
import random
import sys

rng = random.Random(1976)
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
L = []
alc = ['com', 'neg', 'mov', 'inc', 'adc', 'sub', 'add', 'and']
skips = ['', ',skp', ',szc', ',snc', ',szr', ',snr', ',sez', ',sbn']
for _ in range(N):
    for m in alc:
        cy = rng.choice(['', 'z', 'o', 'c'])
        sh = rng.choice(['', 'l', 'r', 's'])
        sk = rng.choice(skips)
        nl = rng.choice(['', '#']) if sk else ''
        L.append(f'{m}{cy}{sh}{nl} {rng.randrange(4)},{rng.randrange(4)}{sk}')
    for m in ('jmp', 'jsr', 'isz', 'dsz', 'lda', 'sta'):
        ac = f'{rng.randrange(4)},' if m in ('lda', 'sta') else ''
        ind = rng.choice(['', '@'])
        mode = rng.randrange(4)
        if mode == 0:
            ea = f'{rng.randrange(0o400):o}'
        else:
            d = rng.randrange(-128, 128)
            ea = f'{"-" if d < 0 else ""}{abs(d):o},{mode}'
        L.append(f'{m} {ac}{ind}{ea}')
    dev = rng.choice([0o10, 0o11, 0o33, 0o50, 0o51, 0o4, 0o5])
    f = rng.choice(['', 's', 'c', 'p'])
    for m in ('dia', 'doa', 'dib', 'dob', 'dic', 'doc'):
        L.append(f'{m}{f} {rng.randrange(4)},{dev:o}')
    L.append(f'nio{f} {dev:o}')
    L.append(f'skp{rng.choice(["bn", "bz", "dn", "dz"])} {dev:o}')
    L.append(f'trap {rng.randrange(4)},{rng.randrange(4)},{rng.randrange(128):o}')
    L += ['mul', 'div', 'inten', 'intds', f'msko {rng.randrange(4)}', f'inta {rng.randrange(4)}', 'halt',
          f'skp{rng.choice(["bn", "bz"])} cpu']
open(sys.argv[1], 'w').write('\t.loc 1000\n' + ''.join(f'\t{x}\n' for x in L) + '\t.end\n')
