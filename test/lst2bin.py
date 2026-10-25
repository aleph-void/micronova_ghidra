#!/usr/bin/env python3
"""dga listing (as in Nova-SOC's minimon.lst) -> raw big-endian image (word address = file word
index) and a list of "<word-address-octal> <word-octal> <source>" for listing_check.py.
  lst2bin.py <listing> <out.bin> <out.words>
"""
import re
import struct
import sys

words = {}
src = {}
last = None
for line in open(sys.argv[1]):
    m = re.match(r'^\d+ +([0-7]{5}) ([0-7]{6}) ?(.*)$', line.rstrip('\n'))
    if m:
        a = int(m.group(1), 8)
        words[a] = int(m.group(2), 8)
        src[a] = m.group(3)
        last = a
        continue
    m = re.match(r'^\d+ +([0-7]{6})\s*$', line.rstrip('\n'))
    if m and last is not None:          # continuation word of .txt
        last += 1
        words[last] = int(m.group(1), 8)
        src[last] = ''
img = bytearray(2 * (max(words) + 1))
for a, w in words.items():
    struct.pack_into('>H', img, 2 * a, w)
open(sys.argv[2], 'wb').write(img)
with open(sys.argv[3], 'w') as f:
    for a in sorted(words):
        f.write(f'{a:o} {words[a]:o} {src[a]}\n')
print(f'{len(words)} words, up to {max(words):o}')
