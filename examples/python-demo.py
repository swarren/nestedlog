#!/usr/bin/env python

import nestedlog.api as nlapi
import sys

failed = False

try:
    with nlapi.run_python_as_block("passing block"):
        pass
except nlapi.BlockFailedException:
    # In this example, we always want to run all the blocks,
    # so squash any block failures
    failed = True

try:
    with nlapi.run_python_as_block("failing block"):
        raise Exception("Test exception")
except nlapi.BlockFailedException:
    # In this example, we always want to run all the blocks,
    # so squash any block failures
    failed = True

# This isn't strictly necessary, since the parent block likely requests
# STATUS_AUTO, which causes child block failures to fail the surrounding
# block. However, we may as well explicitly report the failure anyway.
if failed:
    sys.exit(1)
