# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import html
import nestedlog.data as nld
import nestedlog.emitter_base as nlebase

_status_to_color = {
    nld.STATUS_OK: '4f4',
    nld.STATUS_WARNING: 'ff0',
    nld.STATUS_ERROR: 'f00',
}

_status_to_border_color = {
    nld.STATUS_OK: '4f4',
    nld.STATUS_WARNING: 'dd0',
    nld.STATUS_ERROR: 'f00',
}

class _EmitterHTML(object):
    def __init__(self, log_file_name):
        self.log_file_name = log_file_name

    def emit_start_log(self):
        self.first_block = True
        self.blocks = []
        self.log_file = open(self.log_file_name, 'wt')
        self.log_file.write(
            '<html><head></head>' +
            '<body style="margin:0;border:0;padding:1em;background-color:black;color:#fff">' +
            '<div style="background-color:black;color:#fff"><samp>'
       )

    def emit_end_log(self):
        self.log_file.write('</samp></div></body></html>')
        self.log_file.close()

    def _emit_pad(self):
        self.log_file.write('<div>&nbsp;</div>\n')

    def emit_start_block(self, block_id, block_name):
        if self.first_block:
            self.first_block = False
        else:
            self._emit_pad()
        block_name_html = html.escape(block_name)
        self.log_file.write('<div style="border-left:0.5em solid #')
        patcher_lborder_color = nlebase.Patcher(self.log_file, 3)
        self.log_file.write('">')
        self.log_file.write('<div style="background-color:#333;color:#')
        patcher_header_text_color = nlebase.Patcher(self.log_file, 3)
        self.log_file.write(f'">&nbsp;{block_name_html} (')
        patcher_header_text = nlebase.Patcher(self.log_file, nld.status_max_len + 1)
        self.log_file.write('</div>')
        self.log_file.write('<div style="border-left:0.5em solid #000">\n')
        block_context = {
            'patcher_lborder_color': patcher_lborder_color,
            'patcher_header_text_color': patcher_header_text_color,
            'patcher_header_text': patcher_header_text
        }
        self.blocks.append(block_context)

    def emit_end_block(self, status):
        block_context = self.blocks.pop()
        header_text_color = _status_to_color[status]
        lborder_color = _status_to_border_color[status]
        if status == nld.STATUS_OK:
            lborder_color = '333'
        header_text = nld.status_to_text[status].capitalize()
        self._emit_pad()
        self.log_file.write('</div>')
        self.log_file.write(f'<div style="background-color:#333;color:#{header_text_color}">&nbsp;({header_text})</div>')
        self.log_file.write('</div>\n')
        block_context['patcher_lborder_color'].patch(lborder_color)
        block_context['patcher_header_text_color'].patch(header_text_color)
        block_context['patcher_header_text'].patch(header_text + ')')

    def emit_start_stream(self, stream, switching):
        if not switching:
            self._emit_pad()
            self.log_file.write('<pre style="margin:0;border:0">')
        self.log_file.write('<span')
        if stream == nld.STREAM_STDERR:
            self.log_file.write(' style="color:#ff0"')
        self.log_file.write('>')

    def emit_end_stream(self, switching):
        self.log_file.write('</span>')
        if not switching:
            self.log_file.write('</pre>')

    def emit_stream_data(self, data):
        self.log_file.write(html.escape(data))

Emitter = _EmitterHTML
