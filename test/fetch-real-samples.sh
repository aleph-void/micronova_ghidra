#!/usr/bin/env bash
# Download the freely licensed Nova/microNOVA program used by test/real-binaries.sh. Nothing is
# committed; files land in <dest> (default ./real-samples), checked against a pinned SHA-256.
#
#   test/fetch-real-samples.sh [dest]
#
# scottlbaker/Nova-SOC (pinned commit c105e0ed, GPL-3.0): minimon.lst, the dga listing of the
# Nova SOC mini monitor, a third-party program that uses the microNOVA stack instructions
# (MTSP, MTFP, SAV, RET). test/lst2bin.py turns the listing into a raw image (word address =
# listing address) and a word/source list.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
DEST=${1:-real-samples}
mkdir -p "$DEST"
cd "$DEST"
URL=https://raw.githubusercontent.com/scottlbaker/Nova-SOC/c105e0ed439e3cceb3250af1f540a82766cb082a/bitmaps/monitor/minimon.lst
[[ -s minimon.lst ]] || { curl -fsSL --retry 3 -o minimon.lst.part "$URL"; mv minimon.lst.part minimon.lst; }
echo "c1bc28c95b42b6cbe60618404843a16978073297a9287134f29b0d4cd3d46032  minimon.lst" | sha256sum -c --quiet -
python3 -I "$HERE/lst2bin.py" minimon.lst minimon.bin minimon.words
echo "samples in $(pwd)"
