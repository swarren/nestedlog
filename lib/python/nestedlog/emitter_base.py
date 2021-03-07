# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import nestedlog.data as nld
import os

class Patcher(object):
    def __init__(self, log_file, width):
        self.log_file = log_file
        self.width = width

        self.pos = self.log_file.tell()
        self.log_file.write('?' * self.width)

    def patch(self, s):
        self.log_file.seek(self.pos, os.SEEK_SET)
        self.log_file.write(s)
        self.log_file.write(' ' * (self.width - len(s)))
        self.log_file.seek(0, os.SEEK_END)
