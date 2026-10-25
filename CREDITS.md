# Credits: Micronova module

This is a community SLEIGH module that Ghidra-Rare imported, tested and fixed. The original
processor module was written by its author below; Ghidra-Rare's changes are listed after.

## Upstream

| | |
|---|---|
| Source | [pkooiman/micronova_ghidra](https://github.com/pkooiman/micronova_ghidra), commit `0380ce8362c7baccdaea75d9072b2add9ff723c2` (2026-10-25) |
| Ghidra-Rare fork | [aleph-void/micronova_ghidra](https://github.com/aleph-void/micronova_ghidra/tree/ghidra-rare), branch `ghidra-rare` |
| License | MIT (`LICENSE`, "Copyright (c) 2026 Peter Kooiman", added by the author on 2026-10-25, unchanged) |
| Original author | Peter Kooiman ([@pkooiman](https://github.com/pkooiman)): the microNOVA SLEIGH specification, specs, extension skeleton and the 11.3.1 build in `dist/` (2025) |

Ghidra-Rare's changes are separate commits on branch `ghidra-rare` of a fork of the upstream
repository, on top of its full history, so the original license and authorship are preserved.

## References and test tools (not redistributed)

- Data General, *microNOVA Programmer's Reference* (015-000050-00, 1976, on bitsavers):
  instruction encodings and semantics, device codes.
- MAME's Nova disassembler (`src/devices/cpu/nova/novadasm.cpp`, BSD-3-Clause, AJR), MAME 0.285
  `unidasm -arch nova`: the decode oracle.
- [majenkotech/novadis](https://github.com/majenkotech/novadis) (BSD-3-Clause): a Nova
  disassembler that knows the microNOVA stack instructions, the second oracle for them.
- [napobear/dpa](https://github.com/napobear/dpa) `dga` (GPL-2.0, Toby Thain): the DG Nova
  assembler used for the assembler corpus (built by `test/build-dga.sh`).
- [scottlbaker/Nova-SOC](https://github.com/scottlbaker/Nova-SOC) (GPL-3.0, Scott L. Baker): the
  mini monitor listing used as real code (`test/fetch-real-samples.sh`).

## Ghidra-Rare changes

1. **Instruction set reworked** (`micronova.sinc`, `micronova.slaspec`):
   - Indirect addressing through a PC-relative pointer fixed. It used the pointer's contents
     as the address of the first pointer, one level too many; the original comment says the
     `export` semantics were unclear. All modes now share one pointer-chain walk (bit 15) with
     the auto-increment (20-27) and auto-decrement (30-37) locations.
   - Page-zero and PC-relative jumps are direct flows.
   - JSR now loads AC3 with the return address. It is taken from the disassembly-time word
     address; in p-code `inst_next` is a byte offset in this word-addressed space. `JMP 0,3`
     is a return.
   - TRAP decodes. It was matched on the wrong bits, so its 2,048 encodings decoded as ALC
     no-load instructions. It stores its address in 46 and jumps through 47.
   - All 65,536 words decode; 1,530 valid words used to be rejected, for example NIO with a
     nonzero accumulator field.
   - The carry is a register `C` and the Interrupt On flag `ION`; MUL/DIV, TRAP, JSR/SAV/RET
     and the CPU I/O instructions now run in the emulator. The original passed 18 of the 45
     emulator tests; many failures are because the carry was only a bit field.
   - ALC carry, shift, skip and no-load semantics were checked against the manual.
   - SAV/RET follow the manual's return block.
   - CPU device:
     - IORST/RTCDS/RTCEN are DOA 0/1/2,CPU.
     - INTEN/INTDS, INTA and MSKO.
     - HALT sets Interrupt On.
     - The CPU skip conditions are BN/BZ on Interrupt On, DN never, DZ always.
   - READS reads the console switches word.
   - Operand syntax is DG's `disp,index`, with microNOVA device names.
2. **Specs.** The pspec names the fixed low-memory locations. The cspec gives AC3 as the return
   address, the upward stack, and the killed registers.
3. **Build:**
   - The compiled `.sla` (Ghidra 11.3.1) is no longer tracked.
   - `build.gradle` is Ghidra-Rare's standard file. The original was Ghidra's extension
     skeleton with `ghidraInstallDir = "<REPLACE>"`.
   - `extension.properties` has a name, description and author.
4. **README.md:** current install and build steps and processor notes; the original text is
   kept.

Ghidra-Rare additions (not upstream): `GHIDRA-RARE.md`, `CREDITS.md`, `.github/` and `test/`.
