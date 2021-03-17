#!/bin/bash

# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

script_dir=$(dirname "$0")

echo stdout
echo stderr >&2
echo stdout

nestedlog start-block "someblock"
echo stdout
echo stderr >&2
echo stdout
nestedlog start-block "inner block"
echo stdout
echo stderr >&2
echo stdout
nestedlog end-block
echo stdout
echo stderr >&2
echo stdout
nestedlog end-block

nestedlog start-block "warning child"
nestedlog start-block "inner block 1"
nestedlog end-block warning
nestedlog start-block "inner block 2"
nestedlog end-block warning
nestedlog end-block

nestedlog start-block "error child"
echo stdout
nestedlog start-block "inner & < > block"
echo stdout
nestedlog end-block error
echo stdout
nestedlog end-block

nestedlog start-block "many child"
echo stdout
nestedlog start-block "ok block"
echo stdout
nestedlog end-block
nestedlog start-block "warning block"
echo stdout
nestedlog end-block warning
nestedlog start-block "error block"
echo stdout
nestedlog end-block error
echo stdout
nestedlog end-block

nestedlog start-block "run-as child good"
echo stdout
nestedlog run-as-block "inner block" ls -l /
echo stdout
nestedlog end-block

nestedlog start-block "run-as child bad"
echo stdout
nestedlog run-as-block "inner block" ls -l /xxx
echo stdout
nestedlog end-block

nestedlog run-as-block "Python example" "${script_dir}/python-demo.py"

echo stdout
echo stderr >&2
echo stdout
