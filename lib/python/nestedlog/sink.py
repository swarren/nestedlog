# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import html
import nestedlog.data as nld

class Sink(object):
    def __init__(self, emitters):
        self.emitters = emitters

        self.blocks = []
        self.block_id = 0
        self.cur_stream = None

    def start_log(self):
        for emitter in self.emitters:
            emitter.emit_start_log()

    def end_log(self):
        while self.blocks:
            self.stream_data(nld.STREAM_STDERR, 'nestedlog: Unclosed block')
            self.end_block(nld.STATUS_ERROR)
        for emitter in self.emitters:
            emitter.emit_end_log()

    def start_block(self, block_name):
        if self.cur_stream is not None:
            self.end_stream(False)
        self.block_id += 1
        block_context = {'status': nld.STATUS_OK}
        self.blocks.append(block_context)
        for emitter in self.emitters:
            emitter.emit_start_block(self.block_id, block_name)

    def end_block(self, status):
        if status == nld.STATUS_AUTO:
            status = self.blocks[-1]['status']
        if self.cur_stream is not None:
            self.end_stream(False)
        block_context = self.blocks.pop()
        for emitter in self.emitters:
            emitter.emit_end_block(status)
        if self.blocks:
            cur_status = self.blocks[-1]['status']
            if status > cur_status:
                self.blocks[-1]['status'] = status
        return status

    def start_stream(self, stream, switching):
        block_context = self.blocks[-1]
        for emitter in self.emitters:
            emitter.emit_start_stream(stream, switching)
        self.cur_stream = stream

    def end_stream(self, switching):
        block_context = self.blocks[-1]
        for emitter in self.emitters:
            emitter.emit_end_stream(switching)
        self.cur_stream = None

    def stream_data(self, stream, data):
        block_context = self.blocks[-1]
        if stream != self.cur_stream:
            if self.cur_stream is not None:
                self.end_stream(True)
                switching = True
            else:
                switching = False
            self.start_stream(stream, switching)
        for emitter in self.emitters:
            emitter.emit_stream_data(data)
