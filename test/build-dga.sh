#!/usr/bin/env bash
# Build dga, the DG Nova assembler of "The Didactic PDP-8 and DG Nova Assembler" (Toby Thain,
# GPL-2.0, github.com/napobear/dpa), at a pinned commit.  Needs gcc, flex and bison.
#   test/build-dga.sh <dest-dir>      -> <dest-dir>/dga
set -euo pipefail
DEST=$(mkdir -p "$1" && cd "$1" && pwd)
S=$(mktemp -d)
trap 'rm -rf "$S"' EXIT
git clone -q https://github.com/napobear/dpa "$S/dpa"
git -C "$S/dpa" checkout -q 802634c68e0547a477944bc20f19857a56b1db89
make -C "$S/dpa" dga >/dev/null
cp "$S/dpa/dga" "$DEST/dga"
echo "built $DEST/dga"
