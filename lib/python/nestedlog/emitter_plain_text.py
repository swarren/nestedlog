# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import nestedlog.data as nld
import nestedlog.emitter_base as nlebase

class _Emitter_Plain_Text(object):
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name

    def emit_start_log(self):
        self.blocks = []
        self.log_file = open(self.log_file_name, 'wt')

    def emit_end_log(self):
        self.log_file.close()

    def emit_start_block(self, block_id, block_name):
        if len(self.blocks):
            self.log_file.write('| ' * len(self.blocks))
            self.log_file.write('\n')
        self.log_file.write('| ' * len(self.blocks))
        self.log_file.write(f'/-- {block_name} (')
        patcher = nlebase.Patcher(self.log_file, nld.status_max_len + 1)
        self.log_file.write('\n')
        block_context = {'last_nl': True, 'patcher': patcher}
        self.blocks.append(block_context)

    def emit_end_block(self, status):
        block_context = self.blocks.pop()
        self.log_file.write('| ' * (len(self.blocks) + 1))
        self.log_file.write('\n')
        status_text = nld.status_to_text[status].capitalize()
        self.log_file.write('| ' * len(self.blocks))
        self.log_file.write(f'\\-- ({status_text})\n')
        block_context['patcher'].patch(status_text + ')')

    def emit_start_stream(self, stream, switching):
        if not switching:
            self.log_file.write('| ' * len(self.blocks))
            self.log_file.write('\n')

    def emit_end_stream(self, switching):
        if not switching and not self.blocks[-1]['last_nl']:
            self.log_file.write('\n')

    def emit_stream_data(self, data):
        last_nl = self.blocks[-1]['last_nl']
        lines = data.splitlines(True)
        for line in lines:
            if last_nl:
                self.log_file.write('| ' * len(self.blocks))
            last_nl = True
            self.log_file.write(line)
        self.blocks[-1]['last_nl'] = data[-1] == '\n'

Emitter = _Emitter_Plain_Text
