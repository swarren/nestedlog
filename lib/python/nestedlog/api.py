# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

from contextlib import contextmanager
import nestedlog.data as nld
import os
import socket
import subprocess
import sys
import termios

SOCK_ENV_VAR = 'NESTED_LOG_CONTROL'

CMD_START_BLOCK = 'start-block'
CMD_END_BLOCK = 'end-block'

def start_block(block_name):
    _send_cmd(f'{CMD_START_BLOCK} {block_name}\n')

def end_block(status):
    _send_cmd(f'{CMD_END_BLOCK} {status}\n')

class MarkBlockAsFailedException(Exception):
    pass

class BlockFailedException(Exception):
    pass

@contextmanager
def run_python_as_block(block_name, exit_on_fail=False):
    start_block(block_name)
    status = nld.STATUS_AUTO
    try:
        try:
            yield None
        finally:
            sys.stdout.flush()
    except MarkBlockAsFailedException:
        status = nld.STATUS_ERROR
    except:
        print('ERROR: Exception thrown:', file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        status = nld.STATUS_ERROR
    end_block(nld.status_to_text[status])
    if status != nld.STATUS_AUTO:
        raise BlockFailedException()

def run_as_block(block_name, cmd):
    with run_python_as_block(block_name):
        cpe = subprocess.run(cmd)
        if cpe.returncode != 0:
            print('ERROR: Process exit code ' + str(cpe.returncode), file=sys.stderr)
            raise MarkBlockAsFailedException()

def _send_cmd(cmd):
    # Flush data path all the way to nestedlog server.
    #
    # These should be no-ops, since stdout/stderr are a character device
    # rather than pipes.
    sys.stdout.flush()
    sys.stderr.flush()
    # Synchronously flush to nestedlog-helper CUSE server, which will
    # synchronously flush to main nestedlog server.
    termios.tcdrain(1)

    sock_path = os.environ[SOCK_ENV_VAR]
    client_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_sock.connect(sock_path)
    client_sock.sendall(cmd.encode('utf-8'))
    response = client_sock.recv(1)
    client_sock.close()
    if response != b'0':
        raise Exception('nestedlog server command failed')
