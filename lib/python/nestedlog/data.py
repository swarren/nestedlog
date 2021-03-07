# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

STATUS_AUTO = 0
STATUS_OK = 1
STATUS_WARNING = 2
STATUS_ERROR = 3

status_to_text = {
    STATUS_AUTO: 'auto',
    STATUS_OK: 'ok',
    STATUS_WARNING: 'warning',
    STATUS_ERROR: 'error',
}
text_to_status = {t: s for (s, t) in status_to_text.items()}
status_max_len = max(map(len, text_to_status))

STREAM_STDOUT = 0
STREAM_STDERR = 1
