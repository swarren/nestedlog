#!/usr/bin/env python3

# echo -n 0 | ./nestedlog-helper ./examples/py-buffer-test.py | hexdump -C

import sys

print('line 1')
print('line 2')
print('line 3', file=sys.stderr)
print('line 4')
print('line 5', file=sys.stderr)
print('line 6')
