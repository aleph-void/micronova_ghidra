#!/usr/bin/env bash
# microNOVA module tests that need no third-party binaries:
#   1. compile the .slaspec
#   2. decode every 16-bit word vs MAME's Nova disassembler (compare.py classifies the encodings
#      the microNOVA defines differently from the Nova)
#   3. every-entry test: every SLEIGH constructor is used
#   4. microNOVA-specific encodings (stack, MUL/DIV) vs novadis (optional, NOVADIS)
#   5. assembler corpus with dga (optional, DGA)
#   6. p-code emulator tests; one deliberately broken run must fail
#
#   test/run-tests.sh [workdir]
# Environment: GHIDRA_INSTALL_DIR (with Ghidra/Processors/Micronova -> this module), UNIDASM
#   (default unidasm; MAME 0.285 used), DGA (test/build-dga.sh), NOVADIS (optional), TMPDIR
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
MOD=$(cd "$HERE/.." && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
UNIDASM=${UNIDASM:-unidasm}
W=$(mkdir -p "${1:-micronova-test-work}" && cd "${1:-micronova-test-work}" && pwd)
cd "$W"
gs() { "$HERE/ghidra-script.sh" raw micronova:BE:16:default "$@"; }

echo "== compiling SLEIGH"
(cd "$MOD/data/languages" && "$GHIDRA_INSTALL_DIR/support/sleigh" micronova.slaspec 2>&1 |
	grep -E "^(ERROR|Error)" || true)
ls -la "$MOD"/data/languages/*.sla | awk '{print "   " $9 ": " $5 " bytes"}'

echo "== every 16-bit word vs MAME ($UNIDASM -arch nova)"
python3 -c "import struct; open('all.bin','wb').write(struct.pack('>65536H', *range(65536)))"
"$UNIDASM" all.bin -arch nova >m_all.txt
gs all.bin DumpSlots.java "$W/g_all.txt" 2 "$W/ctor_all.txt"
python3 "$HERE/compare.py" g_all.txt m_all.txt --list 1 | sed 's/^/   /'

echo "== every-entry decode test"
python3 "$HERE/entry_check.py" "$MOD/data/languages" ctor_all.txt | sed 's/^/   /'

if [[ -n ${NOVADIS:-} ]]; then
	echo "== microNOVA stack, MUL/DIV and TRAP encodings vs novadis"
	"$NOVADIS" -s -x all.bin >nd_all.txt
	python3 "$HERE/novadis_check.py" g_all.txt nd_all.txt | sed 's/^/   /'
fi

echo "== assembler corpus (dga)"
if [[ -n ${DGA:-} ]]; then
	python3 "$HERE/gen_asm.py" asm.sr 40
	"$DGA" -l asm.sr >/dev/null
	python3 "$HERE/asm_check.py" asm.lst g_all.txt | sed 's/^/   /'
	printf '\tpsha 2\n\tmsko 1\n\t.end\n' >dga_bug.sr
	"$DGA" -l dga_bug.sr >/dev/null
	echo "   dga operand bug: $(sed -n "s/^[0-9]* *[0-7]*'\\([0-7]*\\) *\\t\\(.*\\)$/\\1 \\2/p" dga_bug.lst | paste -sd ';') (correct: 071401 psha 2; 066077 msko 1)"
else
	echo "   skipped (set DGA; test/build-dga.sh builds it)"
fi

echo "== p-code emulator tests"
python3 "$HERE/emu_tests.py" . >/dev/null
gs emu.bin EmuCheck.java "$W/emu.txt" "$W/emu_res.txt"
echo "   $(tail -1 emu_res.txt)"
grep FAIL emu_res.txt | sed 's/^/   /' || true
python3 "$HERE/emu_tests.py" . --break 20 >/dev/null
gs emu.bin EmuCheck.java "$W/emu.txt" "$W/emu_res_break.txt"
echo "   with test 20's expectation made wrong: $(tail -1 emu_res_break.txt); $(grep FAIL emu_res_break.txt)"
python3 "$HERE/emu_tests.py" . >/dev/null
