#!/usr/bin/env bash
# Real code: the Nova SOC mini monitor (test/fetch-real-samples.sh). Imported headless as a raw
# image with its start address (word 400 octal, the contents of location 3) as entry point,
# auto-analysed and decompiled; every instruction is compared with MAME's Nova disassembly at
# the same address, and the source lines Ghidra did not disassemble are listed.
#   test/real-binaries.sh [samples-dir] [workdir]
# Environment: GHIDRA_INSTALL_DIR, UNIDASM (default unidasm), TMPDIR, DECOMP_TIMEOUT
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
SAMPLES=$(cd "${1:-real-samples}" && pwd)
W=$(mkdir -p "${2:-real-work}" && cd "${2:-real-work}" && pwd)
n=minimon
P=$(mktemp -d "${TMPDIR:-/tmp}/micronova-real.XXXXXX")
"$GHIDRA_INSTALL_DIR/support/analyzeHeadless" "$P" p -import "$SAMPLES/$n.bin" \
	-loader BinaryLoader -processor micronova:BE:16:default \
	-scriptPath "$HERE" -preScript SeedEntries.java 0400 \
	-postScript RealCheck.java "$W/$n.sum" "$W/$n.lst" "$W/$n.c" "${DECOMP_TIMEOUT:-60}" \
	-deleteProject >"$W/$n.log" 2>&1 || { tail -20 "$W/$n.log" >&2; }
rm -rf "$P"
echo "-- $n (raw, entry 400 octal)"
grep -E "^(language|functions|instructions|bad-instruction|error bookmarks|decompile|functions whose)" \
	"$W/$n.sum" | sed 's/^/   /'
"${UNIDASM:-unidasm}" "$SAMPLES/$n.bin" -arch nova >"$W/$n.mame"
python3 "$HERE/listing_check.py" "$W/$n.lst" "$W/$n.mame" "$SAMPLES/$n.words" | sed 's/^/   /'
