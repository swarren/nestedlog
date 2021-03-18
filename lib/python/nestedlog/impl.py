# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

import os
import select
import socket
import subprocess
import tempfile
import nestedlog.api as nlapi
import nestedlog.data as nld
import nestedlog.sink as nlsink

def gen_log(emitters, cmd):
    def handle_control_listen_event(fd, event):
        if event & select.POLLIN:
            ctl_client_sock, addr = ctl_listen_sock.accept()
            ctl_client_fd = ctl_client_sock.fileno()
            os.set_blocking(ctl_client_fd, False)
            handlers[ctl_client_fd] = (handle_control_client_data, ctl_client_sock)
            poller.register(ctl_client_fd, select.POLLIN | select.POLLHUP)
            event &= ~select.POLLIN
        if event:
            raise Exception(f'Unknown event(s) 0x{event:x} on fd {fd}')

    def handle_data_event(fd, event):
        if event & select.POLLIN:
            while True:
                try:
                    data = os.read(fd, 32768)
                except BlockingIOError:
                    break
                if len(data) == 0:
                    break
                handler, file_obj = handlers[fd]
                handler(fd, data)
            event &= ~select.POLLIN
        if event & select.POLLHUP:
            poller.unregister(fd)
            del handlers[fd]
            event &= ~select.POLLHUP
        if event:
            raise Exception(f'Unknown event(s) 0x{event:x} on fd {fd}')

    mbuf = b''
    def handle_multiplexed_data(fd, buf):
        nonlocal mbuf
        mbuf += buf
        while True:
            if len(mbuf) < 2:
                return
            count = ((mbuf[1] & 0x7f) << 8) | mbuf[0]
            if len(mbuf) < 2 + count:
                return
            mfd = (mbuf[1] >> 7) + 1
            data = mbuf[2:2+count].decode('utf-8')
            if mfd == 1:
                sink.stream_data(nld.STREAM_STDOUT, data)
            else:
                sink.stream_data(nld.STREAM_STDERR, data)
            mbuf = mbuf[2+count:]

    def handle_stderr_pipe_data(fd, buf):
        sink.stream_data(nld.STREAM_STDERR, buf.decode('utf-8'))

    ctl_client_bufs = {}
    def handle_control_client_data(fd, buf):
        prev_buf = ctl_client_bufs.get(fd, b'')
        buf = prev_buf + buf
        while True:
            nl_idx = buf.find(b'\n')
            if nl_idx < 0:
                break
            cmd_b = buf[:nl_idx]
            buf = buf[nl_idx+1:]
            try:
                cmd_s = cmd_b.decode('utf-8')
                if ' ' not in cmd_s:
                    raise Exception('Missing command parameters')
                cmd, args = cmd_s.split(' ', 1)
                if cmd == nlapi.CMD_START_BLOCK:
                    cmdfunc = sink.start_block
                    cmdargs = [args]
                elif cmd == nlapi.CMD_END_BLOCK:
                    cmdfunc = sink.end_block
                    cmdargs = [nld.text_to_status[args]]
                else:
                    raise Exception(f'Unknown command "{cmd}"')
            except:
                sink.stream_data(nld.STREAM_STDERR, f'nestedlog: Invalid control command "{cmd_s}"\n')
                import traceback
                sink.stream_data(nld.STREAM_STDERR, traceback.format_exc())
                os.write(fd, b'1')
                continue
            cmdfunc(*cmdargs)
            os.write(fd, b'0')
        ctl_client_bufs[fd] = buf

    sink = nlsink.Sink(emitters)
    sink.start_log()
    sink.start_block(' '.join(cmd))

    block_status = nld.STATUS_AUTO
    try:
        with tempfile.TemporaryDirectory() as ctl_dir:
            sock_path = os.path.join(ctl_dir, 'control')
            os.environ[nlapi.SOCK_ENV_VAR] = sock_path

            poller = select.epoll()
            handlers = {}

            ctl_listen_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            ctl_listen_fd = ctl_listen_sock.fileno()
            # FIXME: Close ctl_listen_sock sometime
            poller.register(ctl_listen_fd, select.POLLIN)
            ctl_listen_sock.bind(sock_path)
            ctl_listen_sock.listen(1)

            sp = subprocess.Popen(['nestedlog-helper'] + cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_f = sp.stdout
            stdout_fd = stdout_f.fileno()
            os.set_blocking(stdout_fd, False)
            handlers[stdout_fd] = (handle_multiplexed_data, stdout_f)
            poller.register(stdout_fd, select.POLLIN | select.POLLHUP)
            stderr_f = sp.stderr
            stderr_fd = stderr_f.fileno()
            os.set_blocking(stderr_fd, False)
            handlers[stderr_fd] = (handle_stderr_pipe_data, stderr_f)
            poller.register(stderr_fd, select.POLLIN | select.POLLHUP)
            # FIXME: Closer stdout/stderr sometime

            while True:
                events = poller.poll()
                # Ensure stdout/err are processed first, so that any control
                # input is processed strictly after draining any cmd output.
                for fd, event in events:
                    if fd != ctl_listen_fd:
                        handle_data_event(fd, event)
                for fd, event in events:
                    if fd == ctl_listen_fd:
                        handle_control_listen_event(fd, event)
                if len(handlers) == 0:
                    break
            
            sp.wait()
            if sp.returncode != 0:
                sink.stream_data(nld.STREAM_STDERR, 'ERROR: Process exit code ' + str(sp.returncode))
                block_status = nld.STATUS_ERROR
    except:
        import traceback
        sink.stream_data(nld.STREAM_STDERR, traceback.format_exc())
        block_status = nld.STATUS_ERROR

    status = sink.end_block(block_status)
    sink.end_log()
    return status
