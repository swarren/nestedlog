# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import html
import nestedlog.data as nld
import nestedlog.emitter_base as nlebase

_stream_class = {
    nld.STREAM_STDERR: 'stderr',
    nld.STREAM_STDOUT: 'stdout',
}

class _EmitterHTML(object):
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name

    def emit_start_log(self):
        self.first_block = True
        self.blocks = []
        self.log_file = open(self.log_file_name, 'wt')
        self.log_file.write('''\
<html><head><style>
body {
    margin: 0;
    border: 0;
    padding: 1em;
}
.base-colors {
    background-color: black;
    color: #fff;
}
pre {
    margin: 0;
    border: 0;
}
.block {
}
.pad {
    min-height: 1em;
}
.block {
    border-left: 0.5em solid #333;
}
.block-header {
    background-color: #333;
}
.block-content {
    border-left: 0.5em solid #000;
}
.block-footer {
    background-color: #333;
}
.block-status-ok {
    color: #4f4;
    border-color: #333;
}
.block-status-warning {
    color: #ff0;
    border-color: #dd0;
}
.block-status-error {
    color: #f00;
    border-color: #f00;
}
.stream-stdout {
    color: #fff;
}
.stream-stderr {
    color: #ff0;
}
</style></head><body class="base-colors"><div class="base-colors"><samp>''')

    def emit_end_log(self):
        self.log_file.write('</samp></div></body></html>')
        self.log_file.close()

    def _emit_pad(self):
        self.log_file.write('<div class="pad">&nbsp;</div>')

    def emit_start_block(self, block_id, block_name):
        if self.first_block:
            self.first_block = False
        else:
            self._emit_pad()
        block_name_html = html.escape(block_name)
        self.log_file.write('<div class="block block-status-')
        patcher_class = nlebase.Patcher(self.log_file, nld.status_max_len)
        self.log_file.write(f'"><div class="block-header">&nbsp;{block_name_html} (')
        patcher_text = nlebase.Patcher(self.log_file, nld.status_max_len + 1)
        self.log_file.write('</div><div class="block-content">')
        block_context = {'patcher_class': patcher_class, 'patcher_text': patcher_text}
        self.blocks.append(block_context)

    def emit_end_block(self, status):
        block_context = self.blocks.pop()
        status_class = nld.status_to_text[status]
        status_text = status_class.capitalize()
        self._emit_pad()
        self.log_file.write(f'</div><div class="block-footer">&nbsp;({status_text})</div></div>')
        block_context['patcher_class'].patch(status_class)
        block_context['patcher_text'].patch(status_text + ')')

    def emit_start_stream(self, stream, switching):
        stream_class = _stream_class[stream]
        if not switching:
            self._emit_pad()
            self.log_file.write('<pre>')
        self.log_file.write(f'<span class="stream-{stream_class}">')

    def emit_end_stream(self, switching):
        self.log_file.write('</span>')
        if not switching:
            self.log_file.write('</pre>')

    def emit_stream_data(self, data):
        self.log_file.write(html.escape(data))

Emitter = _EmitterHTML
