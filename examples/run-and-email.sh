#!/bin/bash

# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

exec nestedlog-email \
    -f cron@example.com \
    -t sysadmin@example.com \
    -s "Nested log demo" \
    "$(dirname "$0")/logged-command.sh"
