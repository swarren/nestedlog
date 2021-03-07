# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import os
import socket
import subprocess
import sys
import nestedlog.data as nld

SOCK_ENV_VAR = 'NESTED_LOG_CONTROL'

CMD_START_BLOCK = 'start-block'
CMD_END_BLOCK = 'end-block'

def start_block(block_name):
    sys.stdout.flush()
    sys.stderr.flush()
    _send_cmd(f'{CMD_START_BLOCK} {block_name}\n')

def end_block(status):
    _send_cmd(f'{CMD_END_BLOCK} {status}\n')

def run_as_block(block_name, cmd):
    _send_cmd(f'{CMD_START_BLOCK} {block_name}\n')
    cpe = subprocess.run(cmd)
    if cpe.returncode == 0:
        status = nld.status_to_text[nld.STATUS_OK]
    else:
        status = nld.status_to_text[nld.STATUS_ERROR]
    _send_cmd(f'{CMD_END_BLOCK} {status}\n')

def _send_cmd(cmd):
    sock_path = os.environ[SOCK_ENV_VAR]
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(sock_path)
    client_sock.sendall(cmd.encode('utf-8'))
    client_sock.close()
