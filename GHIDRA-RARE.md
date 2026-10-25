# Data General microNOVA processor module for Ghidra

A SLEIGH processor module for the Data General microNOVA (mN601/mN602, 1976), the single-chip
member of the Nova family. It runs the Nova instruction set with 15-bit word addresses, plus a
hardware stack (PSHA, POPA, SAV, RET, MTSP, MTFP, MFSP, MFFP), MUL/DIV and TRAP. It is a
community module that Ghidra-Rare imported, tested against MAME and real code, and fixed:

- [pkooiman/micronova_ghidra](https://github.com/pkooiman/micronova_ghidra) by Peter Kooiman.
- MIT.
- See [CREDITS.md](CREDITS.md) for the upstream commit, the references used and every change.
- It targets Ghidra 12.1.4, and also builds on 12.1.3 and 12.2. Prebuilt zips are on the fork's
  [Releases page](https://github.com/aleph-void/micronova_ghidra/releases).

"Micronova" here is the Data General processor. It has nothing to do with the Micronova
pellet-stove controllers.

## Language

| Language ID | Description |
|---|---|
| `micronova:BE:16:default` | microNOVA, big-endian 16-bit words, word-addressed |

The `ram` space is word addressed: one Ghidra address is one 16-bit word, as in DG
documentation (numbers there are octal; Ghidra shows hex). Import a program as a raw binary.
The load address in the import options is in bytes: word address × 2. There is no ELF or
loader format for this processor.

## Files

- `data/languages/micronova.sinc`: the instruction set.
- `micronova.slaspec`: registers AC0-AC3, PC, SP, FP, the interrupt priority mask MASK, the
  carry C and Interrupt On ION; the I/O pcodeops.
- `micronova.pspec`: labels the fixed low-memory locations:
  - 0: interrupt return PC.
  - 1-3: I/O, real-time clock and stack-fault interrupt vectors.
  - 20-27 and 30-37: auto-increment and auto-decrement cells.
  - 46/47: TRAP return and vector.
  - 77577: console switches.
- `micronova.cspec`: AC3 holds the return address (JSR), the stack grows upward, and AC0-AC2
  are the default arguments with AC0 the result. There is no compiler ABI to follow.

## What is decoded

Every 16-bit word decodes:

- **Memory reference.** JMP, JSR, ISZ, DSZ, LDA and STA in all four addressing modes:
  page zero, PC relative, AC2+d, AC3+d, each direct or `@` indirect. Syntax is DG's: `disp,index`.
  Page-zero and PC-relative targets are shown as addresses.
- **ALC.** COM, NEG, MOV, INC, ADC, SUB, ADD and AND with carry (Z/O/C), shift (L/R/S),
  no-load (#) and the eight skips.
- **TRAP acs,acd,n**, the no-load, never-skip ALC form.
- **I/O.** NIO, DIA-DOC and SKP with the S/C/P and BN/BZ/DN/DZ variants, and microNOVA device
  names: MDV, HHC, PROG, TTI/TTO, TTI1/TTO1, DKT-DKT3.
- **Device 01:** PSHA, POPA, MTSP, MFSP, MTFP, MFFP, SAV, RET, MUL, DIV.
- **Device 77 (CPU):** INTEN, INTDS, INTA, MSKO, IORST, RTCDS, RTCEN and HALT, plus SKP CPU.
  IORST, RTCDS and RTCEN are DOA 0/1/2,CPU on the microNOVA (the Nova's IORST is DIC).
- **Device 04 (hand-held console):** READS.

## Semantics

Everything that is not a device operation has p-code:

- **ALC:**
  - Carry base, then the 17-bit operation with carry complement.
  - Rotate left/right through carry, and byte swap.
  - Load unless no-load.
  - Skip on the shifted result and carry.
- **Effective addresses:** the full indirect chain (bit 15), with the auto-increment and
  auto-decrement cells, all modulo 2^15.
- **Memory-reference instructions:**
  - JSR loads AC3 with the return address after computing the effective address.
  - `JMP 0,3` is a return.
  - ISZ and DSZ skip on zero.
- **Device 01 (stack and MDV):**
  - PSHA/POPA (pre-increment push, post-decrement pop).
  - SAV pushes the five-word return block (AC0, AC1, AC2, FP, carry with AC3) and sets
    FP = AC3 = SP.
  - RET restores from FP.
  - MUL: AC0:AC1 = AC1 × AC2 + AC0.
  - DIV: quotient AC1, remainder AC0; on overflow carry is set and nothing changes.
- **TRAP:** stores its address in 46 and jumps through 47 (with indirection).
- **Device 77 (CPU):**
  - INTEN/INTDS and the S/C function set or clear ION.
  - MSKO sets MASK; IORST clears MASK.
  - HALT sets ION.
  - SKP CPU tests ION (DN never skips, DZ always skips).
- **READS:** reads the switches word at 77577.

Device data transfers, Busy/Done flags, interrupt acknowledge, I/O reset, the real-time clock
and HALT's stop are pcodeops: they are external hardware.

## Test results

Run `test/run-tests.sh` for everything except real code, and `test/fetch-real-samples.sh`, then
`test/real-binaries.sh` for real code (see "Testing").

### Decoding vs MAME

MAME 0.285 `unidasm -arch nova` decodes the plain Nova. Every one of the 65,536 words was
compared:

| Result | Words |
|---|---|
| Same instruction (normalised: numbers by value, ACn = n, device names = codes) | 63,426 |
| Explained: microNOVA meaning of a Nova encoding | 2,110 |
| Different | 0 |
| Rejected by Ghidra | 0 |

The explained classes are all checked against the microNOVA Programmer's Reference:

- **TRAP (2,048):** a no-load, never-skip ALC word; MAME shows the ALC form.
- **Device-01 stack instructions (26):** MAME shows NIO/DIA/DOA/DIB/DIC to MDV.
- **microNOVA CPU device (32):**
  - IORST/RTCDS/RTCEN are DOA 0/1/2,CPU.
  - MAME's Nova IORST (DIC 0,CPU) and READS (DIA ac,CPU) are not microNOVA instructions.
  - HALT ignores S/C/P.
- **READS (4):** it is DIA ac,HHC on the microNOVA.

The original module compiled. With its syntax normalised, it disagreed on these words:

- It rejected 1,530 valid words.
- It decoded the 2,048 TRAP words as ALC instructions.
- It named PSHA "PUSHA" and printed INTEN with an S suffix.

**Every-entry test** (`test/entry_check.py`): all 108 SLEIGH constructors are used by the
corpus.

**microNOVA encodings vs novadis.** On the stack, MUL/DIV and TRAP encodings, novadis
(BSD-3-Clause) agrees on the 26 stack, MUL and DIV words that its table can reach. It cannot
reach the others: its NIO entry shadows MTFP/MFFP AC0 (2 words), and its ALC entries shadow
TRAP (2,048 words). See "Confirmed reference-tool bugs".

### Assembler corpus (dga)

`test/gen_asm.py` writes 1,240 lines with random operands. They cover every ALC
combination, every memory-reference mode, I/O to several devices, TRAP, MUL/DIV and the CPU
instructions. `dga` (the DG Nova assembler from napobear/dpa, GPL-2.0) assembles them, and
`test/asm_check.py` compares each word's decode with its source line:

| Result | Lines |
|---|---|
| Same as the source | 1,180 |
| dga bug: MSKO/INTA assembled with AC0 | 60 |
| Different | 0 |

### Emulator

`test/emu_tests.py` and `test/EmuCheck.java` run 45 sequences with hand-computed results. They
cover:

- Every ALC operation with carry bases, shifts, no-load and each skip condition.
- All addressing modes, including PC-relative indirect, multi-level indirect,
  auto-increment and auto-decrement.
- ISZ/DSZ skips, JSR and `JMP 0,3` return, indexed and indirect jumps.
- PSHA/POPA, the stack registers, SAV/RET round trip, MUL, DIV and DIV overflow.
- TRAP, INTEN/INTDS/MSKO, SKP CPU, READS.

Results: 45/45 on Ghidra 12.1.3, 12.1.4 and 12.2. With `--break N` exactly test N fails. The
original module passed 18 of these tests. Its carry was not a register, PC-relative indirect
went one level too far, and JSR, SAV/RET, MUL, DIV, TRAP and the CPU and console instructions
failed.

### Real code

There is little freely licensed microNOVA code. DG's own software (MP/OS, DTOS, diagnostics)
is not freely licensed, so it was not used. The sample is the Nova SOC mini monitor
([scottlbaker/Nova-SOC](https://github.com/scottlbaker/Nova-SOC), GPL-3.0). It is a
third-party program that uses the microNOVA stack instructions (MTSP, MTFP, SAV, RET). It is
fetched as its dga listing at a pinned commit (SHA-256 checked); `test/lst2bin.py` builds the
image, and analysis starts at its start address 400 (octal).

| Check | Result |
|---|---|
| Analysis | 10 functions, 194 instructions, 0 bad instructions, 0 error bookmarks |
| Decompile | 10/10 functions |
| vs MAME | 183 identical, 11 in the microNOVA classes above (MTSP, MTFP, SAV, RET), each matching its source line |
| vs source | Every source instruction is disassembled except the 11-word routine `isdig`, which nothing calls |

Notes on the sample:

- Six words are Nova 4 LDB/STB that the author hand-assembled for the Nova SOC (`060601`
  etc.). The microNOVA has no such instructions. Ghidra and MAME both decode them as DIAC/DOBC
  to device 01, which is what the microNOVA would execute.
- Locations 0-3 and 47 are also disassembled. The monitor returns through `JMP @retval`, and
  the run-time cell holds 0 in the image, so Ghidra's constant propagation follows it.

## Upstream limitations and issues

- **README:**
  - "Download the zip file from the dist directory": that zip is for Ghidra 11.3.1.
    README.md now points to the release zips for Ghidra 12.
  - "Building the extension: Coming soon": **fixed**, `gradle buildExtension`.
  - The note that addresses are words is kept: still true.
- **Comment in the original sinc:** "Somebody somewhere must understand the intricacies of the
  Sleigh `export *` statement but that someone is not me". This was about the effective
  addresses. **Fixed** (see CREDITS.md and the emulator tests).
- The repository has one issue, #1 (license request, closed after the author added MIT). It has
  no pull requests and no TODO/FIXME comments.

## Known gaps

These cannot be fixed in the module:

- **External hardware.** Device I/O (data buffers, Busy/Done, the interrupt request line and
  acknowledge, I/O reset, the real-time clock) and HALT's stop are pcodeops. Ghidra's emulator
  has no devices or interrupts, and the effects depend on the attached peripherals.
- **Stack overflow.** The microNOVA requests a stack interrupt when a push writes a word whose
  address is a multiple of 256. The push itself is modelled; the interrupt is not.
- **Indirect returns.** `JMP @cell` returns, through a cell that holds a saved AC3, decompile
  as computed jumps ("treating indirect jump as call"). The cell's contents are known only at
  run time.

### Unverified

- Real DG microNOVA software (MP/OS, DTOS, diagnostics): not freely licensed.
- The mN602's memory-management and data-channel differences from the mN601. The
  Programmer's Reference describes one instruction set, and this module follows it.

## Confirmed reference-tool bugs

- **dga (napobear/dpa):**
  - One-operand I/O-class mnemonics (PSHA, POPA, MTSP, MTFP, MFSP, MFFP, MSKO, INTA) treat the
    accumulator operand as part of the device code. For example, `psha 2` assembles as 061403
    (device 03, AC0) instead of 071401, and `msko 1` as 062077 instead of 066077.
  - Its IORST is the Nova DIC 0,CPU, not the microNOVA DOA 0,CPU.
  - Its listing location counter stays at 0 in this build.
  - `test/run-tests.sh` shows the operand bug.
- **novadis:** in its first-match opcode table, the NIO entry precedes MTFP/MFFP, so those
  print as NIO for AC0. The ALC entries precede TRAP, so TRAP is never printed.
- **MAME:** decodes the Nova, not the microNOVA (see the explained classes). There are no
  errors within the Nova set.

## Testing

```sh
export GHIDRA_INSTALL_DIR=/path/to/ghidra_12.1.4_PUBLIC   # with Ghidra/Processors/Micronova -> this module
export TMPDIR=/some/dir          # Ghidra refuses projects under dot-directories
test/build-dga.sh ~/dga && export DGA=~/dga/dga           # optional: the assembler corpus
export NOVADIS=/path/to/novadis                           # optional (github.com/majenkotech/novadis)
test/run-tests.sh work
test/fetch-real-samples.sh samples
test/real-binaries.sh samples work-real
```

`unidasm` (MAME's disassembler, MAME 0.285 was used) must be on PATH or in `UNIDASM`.
