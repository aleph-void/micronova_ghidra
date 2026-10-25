#!/usr/bin/env python3
"""P-code semantic tests for Ghidra's emulator (EmuCheck.java), microNOVA.

  emu_tests.py <outdir> [--break N]   -> emu.bin, emu.txt

Each test is a short sequence at word address 200h + 40h*N ending in "JMP ." (the stop address,
or the address named by 'stop'). Expected values were worked out by hand from the microNOVA
Programmer's Reference (DG 015-000050). Word addresses; SP starts at 1000h, carry at 0 unless
the test sets C. --break N makes the expectation of test N wrong.
"""
import struct
import sys

out = sys.argv[1]
brk = int(sys.argv[sys.argv.index('--break') + 1]) if '--break' in sys.argv else -1
OPS = dict(COM=0, NEG=1, MOV=2, INC=3, ADC=4, SUB=5, ADD=6, AND=7)
CY = {'': 0, 'Z': 1, 'O': 2, 'C': 3}
SH = {'': 0, 'L': 1, 'R': 2, 'S': 3}
SK = dict(NONE=0, SKP=1, SZC=2, SNC=3, SZR=4, SNR=5, SEZ=6, SBN=7)


def alc(op, s, d, cy='', sh='', nl=0, skip='NONE'):
    return 0x8000 | s << 13 | d << 11 | OPS[op] << 8 | SH[sh] << 6 | CY[cy] << 4 | nl << 3 | SK[skip]


def mem(op, ind, idx, disp):
    return op << 11 | ind << 10 | idx << 8 | (disp & 0xff)


JMP = lambda ind, idx, d: mem(0, ind, idx, d)
JSR = lambda ind, idx, d: mem(1, ind, idx, d)
ISZ = lambda ind, idx, d: mem(2, ind, idx, d)
DSZ = lambda ind, idx, d: mem(3, ind, idx, d)
LDA = lambda ac, ind, idx, d: 0x2000 | ac << 11 | ind << 10 | idx << 8 | (d & 0xff)
STA = lambda ac, ind, idx, d: 0x4000 | ac << 11 | ind << 10 | idx << 8 | (d & 0xff)
IO = lambda ac, op, ctl, dev: 0x6000 | ac << 11 | op << 8 | ctl << 6 | dev
TRAP = lambda s, d, n: 0x8000 | s << 13 | d << 11 | n << 4 | 8
HERE = JMP(0, 1, 0)                  # JMP . (PC relative, displacement 0)
PSHA = lambda a: IO(a, 3, 0, 1)
POPA = lambda a: IO(a, 3, 2, 1)
MTSP = lambda a: IO(a, 2, 0, 1)
MFSP = lambda a: IO(a, 2, 2, 1)
MTFP = lambda a: IO(a, 0, 0, 1)
MFFP = lambda a: IO(a, 0, 2, 1)
SAV, RET = IO(0, 5, 0, 1), IO(0, 5, 2, 1)
MUL, DIV = IO(2, 6, 3, 1), IO(2, 6, 1, 1)
INTEN, INTDS = IO(0, 0, 1, 0o77), IO(0, 0, 2, 0o77)
MSKO = lambda a: IO(a, 4, 0, 0o77)
SKPBN_CPU = IO(0, 7, 0, 0o77)
READS = lambda a: IO(a, 1, 0, 4)

# (name, words (None = stop marker inserted as JMP .), init, expect); 'B' in an init/expect
# value means the test's base address, 'B+n' that plus n.
T = [
    ('add', [alc('ADD', 1, 2)], {'AC1': 3, 'AC2': 4}, {'AC2': 7, 'C': 0}),
    ('add_carry', [alc('ADD', 1, 2)], {'AC1': 0xffff, 'AC2': 1}, {'AC2': 0, 'C': 1}),
    ('addz_base', [alc('ADD', 1, 2, 'Z')], {'AC1': 1, 'AC2': 1, 'C': 1}, {'AC2': 2, 'C': 0}),
    ('subo_borrow', [alc('SUB', 1, 2, 'O')], {'AC1': 5, 'AC2': 3}, {'AC2': 0xfffe, 'C': 1}),
    ('subz', [alc('SUB', 1, 2, 'Z')], {'AC1': 3, 'AC2': 5}, {'AC2': 2, 'C': 1}),
    ('negz_zero', [alc('NEG', 1, 1, 'Z')], {'AC1': 0}, {'AC1': 0, 'C': 1}),
    ('negz_one', [alc('NEG', 2, 2, 'Z')], {'AC2': 1}, {'AC2': 0xffff, 'C': 0}),
    ('incz_wrap', [alc('INC', 1, 1, 'Z')], {'AC1': 0xffff}, {'AC1': 0, 'C': 1}),
    ('adcz', [alc('ADC', 1, 2, 'Z')], {'AC1': 5, 'AC2': 7}, {'AC2': 1, 'C': 1}),
    ('com', [alc('COM', 1, 2)], {'AC1': 0x00ff}, {'AC2': 0xff00}),
    ('and', [alc('AND', 1, 2)], {'AC1': 0x0f0f, 'AC2': 0x00ff}, {'AC2': 0x000f}),
    ('movol', [alc('MOV', 1, 2, 'O', 'L')], {'AC1': 0x8001}, {'AC2': 3, 'C': 1}),
    ('movzr', [alc('MOV', 1, 2, 'Z', 'R')], {'AC1': 3, 'C': 0}, {'AC2': 1, 'C': 1}),
    ('movs', [alc('MOV', 1, 2, '', 'S')], {'AC1': 0x1234, 'C': 1}, {'AC2': 0x3412, 'C': 1}),
    ('noload_szr', [alc('MOV', 1, 1, nl=1, skip='SZR'), alc('INC', 2, 2), None],
     {'AC1': 0, 'C': 1}, {'AC2': 0, 'AC1': 0, 'C': 1}),
    ('noload_keeps_acd', [alc('ADD', 1, 2, 'Z', nl=1, skip='SKP'), alc('INC', 3, 3), None],
     {'AC1': 5, 'AC2': 6, 'C': 1}, {'AC2': 6, 'C': 1, 'AC3': 0}),
    ('snc_skip', [alc('ADD', 1, 2, 'Z', skip='SNC'), alc('INC', 3, 3), None], {'AC1': 0xffff, 'AC2': 1}, {'AC2': 0, 'C': 1, 'AC3': 0}),
    ('snc_noskip', [alc('ADD', 1, 2, 'Z', skip='SNC'), alc('INC', 3, 3), None], {'AC1': 1, 'AC2': 1}, {'AC3': 1}),
    ('sez_noskip', [alc('SUB', 1, 2, 'Z', skip='SEZ'), alc('INC', 3, 3), None], {'AC1': 3, 'AC2': 5}, {'AC3': 1}),
    ('sbn_skip', [alc('ADD', 1, 2, 'Z', skip='SBN'), alc('INC', 3, 3), None], {'AC1': 0xffff, 'AC2': 2},
     {'AC2': 1, 'C': 1, 'AC3': 0}),
    ('lda_sta_page0', [LDA(1, 0, 0, 0x50), STA(1, 0, 0, 0x51)], {'@50': 0x1234}, {'AC1': 0x1234, '@51': 0x1234}),
    ('lda_pcrel', [LDA(2, 0, 1, 3), None, 0, 0xbeef], {}, {'AC2': 0xbeef}),
    ('lda_ac2_index', [LDA(1, 0, 2, -2)], {'AC2': 0x4002, '@4000': 0x5555}, {'AC1': 0x5555}),
    ('lda_indirect', [LDA(1, 1, 0, 0x60)], {'@60': 0x4000, '@4000': 0x7777}, {'AC1': 0x7777}),
    ('lda_indirect_pcrel', [LDA(1, 1, 1, 3), None, 0, 0x4000], {'@4000': 0x9999}, {'AC1': 0x9999}),
    ('isz_indirect_ac2', [ISZ(1, 2, 1), None], {'AC2': 0x60, '@61': 0x4000, '@4000': 5}, {'@4000': 6}),
    ('lda_indirect_chain', [LDA(1, 1, 0, 0x60)], {'@60': 0x8061, '@61': 0x4001, '@4001': 0x1111}, {'AC1': 0x1111}),
    ('autoincrement', [LDA(1, 1, 0, 0x10)], {'@10': 0x4000, '@4001': 0x2222}, {'AC1': 0x2222, '@10': 0x4001}),
    ('autodecrement', [STA(1, 1, 0, 0x18)], {'@18': 0x4005, 'AC1': 0x3333}, {'@4004': 0x3333, '@18': 0x4004}),
    ('isz_skip', [ISZ(0, 0, 0x50), alc('INC', 3, 3), None], {'@50': 0xffff}, {'@50': 0, 'AC3': 0}),
    ('dsz_noskip', [DSZ(0, 0, 0x50), alc('INC', 3, 3), None], {'@50': 2}, {'@50': 1, 'AC3': 1}),
    ('jsr_return', [JSR(0, 1, 3), None, 0, alc('INC', 1, 1), JMP(0, 3, 0)], {}, {'AC3': 'B+1', 'AC1': 1}),
    ('jmp_ac3_index', [JMP(0, 3, 2), alc('INC', 1, 1), None], {'AC3': 'B'}, {'AC1': 0}),
    ('jmp_indirect', [JMP(1, 0, 0x60), alc('INC', 1, 1), None], {'@60': 'B+2'}, {'AC1': 0}),
    ('psha_popa', [PSHA(1), POPA(2)], {'AC1': 0xaaaa}, {'AC2': 0xaaaa, 'SP': 0x1000, '@1001': 0xaaaa}),
    ('stack_registers', [MTSP(1), MFSP(2), MTFP(1), MFFP(3)], {'AC1': 0x8123},
     {'SP': 0x0123, 'AC2': 0x0123, 'FP': 0x0123, 'AC3': 0x0123}),
    ('sav_ret', [JSR(0, 1, 3), None, 0, SAV, alc('INC', 0, 0), RET],
     {'AC0': 1, 'AC1': 2, 'AC2': 3, 'FP': 0x0f00, 'C': 1},
     {'AC0': 1, 'AC1': 2, 'AC2': 3, 'AC3': 0x0f00, 'SP': 0x1000, 'FP': 0x1005, 'C': 1,
      '@1001': 1, '@1004': 0x0f00, '@1005': 'B+1|8000'}),
    ('mul', [MUL], {'AC0': 5, 'AC1': 0x1000, 'AC2': 0x0100}, {'AC0': 0x0010, 'AC1': 0x0005, 'AC2': 0x0100}),
    ('div', [DIV], {'AC0': 1, 'AC1': 5, 'AC2': 0x10, 'C': 1}, {'AC1': 0x1000, 'AC0': 5, 'C': 0}),
    ('div_overflow', [DIV], {'AC0': 0x10, 'AC1': 5, 'AC2': 0x10}, {'AC0': 0x10, 'AC1': 5, 'C': 1}),
    ('trap', [TRAP(1, 2, 5), None, 0, alc('INC', 1, 1), JMP(0, 1, 0)], {'@27': 'B+3'}, {'@26': 'B', 'AC1': 1},
     'B+4'),
    ('inten_msko', [INTEN, MSKO(1)], {'AC1': 0x00f0}, {'ION': 1, 'MASK': 0x00f0}),
    ('intds', [INTDS], {'ION': 1}, {'ION': 0}),
    ('skpbn_cpu', [INTEN, SKPBN_CPU, alc('INC', 3, 3), None], {}, {'AC3': 0, 'ION': 1}),
    ('reads_hhc', [READS(1)], {'@7f7f': 0x4242}, {'AC1': 0x4242}),
]


def val(v, base):
    if isinstance(v, str):
        x, _, o = v.partition('|')
        n = base + (int(x[2:], 16) if x.startswith('B+') else 0)
        return n | (int(o, 16) if o else 0)
    return v


def fmt(d, base):
    return ','.join(f'{k}={val(v, base) & 0xffff:x}' for k, v in d.items()) or '-'


img = bytearray(0x10000 * 2)
lines = []
for i, t in enumerate(T):
    name, words, init, exp = t[:4]
    base = 0x200 + 0x40 * i
    stop = None
    code = []
    for w in words + ([None] if None not in words and len(t) < 5 else []):
        if w is None:
            stop = base + len(code)
            code.append(HERE)
        else:
            code.append(w & 0xffff)
    if len(t) > 4:
        stop = val(t[4], base)
    for k, w in enumerate(code):
        struct.pack_into('>H', img, 2 * (base + k), w)
    exp = dict(exp)
    if i == brk:
        k = next(iter(exp))
        exp[k] = val(exp[k], base) ^ 1
    lines.append(f'{name} {base:x} {stop:x} {fmt(init, base)} {fmt(exp, base)}')
open(f'{out}/emu.bin', 'wb').write(bytes(img[:0x8000 * 2]))
open(f'{out}/emu.txt', 'w').write('\n'.join(lines) + '\n')
print(f'{len(T)} tests')
