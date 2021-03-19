// Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
// SPDX-License-Identifier: MIT

#define FUSE_USE_VERSION 29
#define _FILE_OFFSET_BITS 64

#include <cerrno>
#include <cstdio>
#include <fuse/cuse_lowlevel.h>
#include <fuse/fuse.h>
#include <fuse/fuse_lowlevel.h>
#include <fuse/fuse_opt.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <string>
#include <asm/termbits.h>
#include <unistd.h>

#define ARSIZE(x) ((sizeof (x)) / (sizeof (x)[0]))

int fd_num = 0;

static void nlhelper_open(fuse_req_t req, struct fuse_file_info *fi) {
    // 2 fds; stdout, stderr
    if (fd_num >= 2) {
        fuse_reply_err(req, EINVAL);
        return;
    }
    fi->fh = ++fd_num;
    fuse_reply_open(req, fi);
}

static void nlhelper_write(fuse_req_t req, const char *buf, size_t size,
    off_t off, struct fuse_file_info *fi
) {
    if (!fi->fh) {
        fuse_reply_err(req, EBADFD);
        return;
    }

    size_t ofs = 0;
    size_t size_left = size;
    char obuf[2];
    while (size_left) {
        size_t to_write = size_left;
        // This much body data fits into:
        // - 32767 max value that can be encoded into header
        // - nestedlog's 32768 byte read (including the 2 byte header)
        const size_t max_to_write = 32766;
        if (to_write > max_to_write)
            to_write = max_to_write;
        obuf[0] = to_write & 255;
        obuf[1] = ((to_write >> 8) & 127) | ((fi->fh - 1) << 7);
        size_t wrote;
        wrote = fwrite(obuf, 1, 2, stdout);
        if (wrote != 2)
            goto err;
        wrote = fwrite(buf + ofs, 1, to_write, stdout);
        if (wrote != to_write)
            goto err;
        int ret = fflush(stdout);
        if (ret != 0)
            goto err;
        ofs += to_write;
        size_left -= to_write;
    }

    fuse_reply_write(req, size);
    return;

err:
    perror("nlhelper: fwrite() failed");
    fi->fh = 0;
    fuse_reply_err(req, EBADFD);
}

static void nlhelper_ioctl(fuse_req_t req, int cmd, void *arg,
    struct fuse_file_info *fi, unsigned int flags, const void *in_buf,
    size_t in_bufsz, size_t out_bufsz
) {
    if (!fi->fh) {
        fuse_reply_err(req, EBADFD);
        return;
    }

    if (flags & FUSE_IOCTL_COMPAT) {
        fuse_reply_err(req, ENOSYS);
        return;
    }

    switch (cmd) {
        case TCSBRK: {
            char buf[2] = {0};
            size_t nwrote = write(1, buf, 2);
            if (nwrote != 2)
                goto err;
            size_t nread = read(0, buf, 1);
            if (nread != 1)
                goto err;
            fuse_reply_ioctl(req, 0, NULL, 0);
            break;
        }
        case TCGETS: {
            struct termios2 t{
                // These values are what tcgetattr(1) returns in gdb running
                // under xfce4-terminal!
                .c_iflag = IUTF8 | IXON | ICRNL, // 0x4500
                .c_oflag = ONLCR | OPOST, // 0x5
                .c_cflag = CREAD | CS8 | B38400, // 0xbf
                .c_lflag = IEXTEN | ECHOKE | ECHOCTL | ECHOK | ECHOE | ECHO |
                     ICANON | ISIG, // 0x8a3b
                .c_line = 0,
                .c_cc = {0x3, 0x1c, 0x7f, 0x15, 0x4, 0x0, 0x1, 0x0, 0x11, 0x13,
                    0x1a, 0x0, 0x12, 0xf, 0x17, 0x16},
                .c_ispeed = B38400,
                .c_ospeed = B38400,
            };
            // This seems to be called with out_bufsz==0 a lot!
            fuse_reply_ioctl(req, 0, &t, std::min(out_bufsz, sizeof t));
            break;
        }
        default: {
            fuse_reply_ioctl(req, EINVAL, NULL, 0);
            break;
        }
    }

    return;

err:
    perror("nlhelper: fwrite()/fread() for fsync failed");
    fi->fh = 0;
    fuse_reply_err(req, EBADFD);
}

static const struct cuse_lowlevel_ops nlhelper_clop = []{
    struct cuse_lowlevel_ops s{};
    s.open = nlhelper_open;
    s.write = nlhelper_write;
    s.ioctl = nlhelper_ioctl;
    return s;
}();

int cuse_main(std::string &dev_name) {
    const char* cuse_argv[] = {"nestedlog-helper", "-f", "-s"};
    std::string dev_info_devname("DEVNAME=" + dev_name);
    const char* dev_info_argv[] = {dev_info_devname.c_str()};
    struct cuse_info ci = [&]{
        struct cuse_info s{};
        s.dev_info_argc = ARSIZE(dev_info_argv);
        s.dev_info_argv = dev_info_argv;
        return s;
    }();
    struct fuse_session *se;
    int ret;

    // Initialize CUSE
    {
        int multithreaded;
        se = cuse_lowlevel_setup(
            ARSIZE(cuse_argv),
            const_cast<char **>(cuse_argv),
            &ci,
            &nlhelper_clop,
            &multithreaded,
            NULL);
        if (se == NULL) {
            fputs("ERROR: CUSE child: !se!", stderr);
            return 1;
        }
        if (multithreaded) {
            fputs("ERROR: CUSE child: multithreaded!", stderr);
            ret = 1;
            goto teardown;
        }
    }

    // Drop privileges
    {
        uid_t new_uid = getuid();
        uid_t old_uid = geteuid();
        if (new_uid != old_uid) {
            ret = setreuid(new_uid, new_uid);
            if (ret) {
                perror("ERROR: CUSE child: setreuid() failed");
                ret = 1;
                goto teardown;
            }
        }
    }

    // Handle CUSE protocol
    {
        ret = fuse_session_loop(se);
        if (ret) {
            fputs("ERROR: CUSE child: fuse_session_loop() failed", stderr);
            ret = 1;
            goto teardown;
        }
    }

    ret = 0;

teardown:
    cuse_lowlevel_teardown(se);

    return ret;
}

int main(int argc, char** argv) {
    int ret;
    pid_t ppid = getpid();
    std::string dev_name("nestedlog-helper-" + std::to_string(ppid));
    std::string dev_path("/dev/" + dev_name);
    pid_t cuse_pid;
    pid_t logged_pid;

    // Create FUSE helper child process
    cuse_pid = fork();
    if (cuse_pid < 0) {
        perror("ERROR: fork() failed");
        goto ret_err;
    }
    if (!cuse_pid)
        return cuse_main(dev_name);

    // stdin, stdout only used to communicate from nestedlog server to CUSE
    // implementation. Keep stderr to report errors from this process.
    close(0);
    close(1);

    // Wait until device exists
    {
        int waited = 0;
        while (true) {
            struct stat stat;
            ret = ::stat(dev_path.c_str(), &stat);
            if ((ret < 0) && (errno != ENOENT)) {
                perror("ERROR: stat() failed");
                goto kill_cuse_child;
            }
            if (!ret)
                break;
            if (waited == 100) {
                fputs("ERROR: CUSE device did not appear", stderr);
                goto kill_cuse_child;
            }
            usleep(100000);
            waited++;
        }
    }

    {
        // Current privileges
        uid_t new_uid = getuid();
        uid_t old_uid = geteuid();

        // Allow user to access device
        ret = chown(dev_path.c_str(), new_uid, -1);
        if (ret) {
            perror("ERROR: chown failed");
            goto kill_cuse_child;
        }

        // Drop privileges
        if (new_uid != old_uid) {
            ret = setreuid(new_uid, new_uid);
            if (ret) {
                perror("ERROR: setreuid() failed");
                goto kill_cuse_child;
            }
        }
    }

    // Fork and exec logged child process
    logged_pid = fork();
    if (logged_pid < 0) {
        perror("ERROR: fork() failed");
        goto kill_cuse_child;
    }
    // Logged child:
    if (!logged_pid) {
        int so = open(dev_path.c_str(), O_WRONLY);
        if (so < 0) {
            perror("ERROR: open() failed for stdout");
            goto child_ret_err;
        }
        ret = dup2(so, 1);
        if (ret < 0) {
            perror("ERROR: dup2() failed for stdout");
            goto child_ret_err;
        }
        ret = close(so);
        if (ret < 0) {
            perror("ERROR: close() failed for stdout");
            goto child_ret_err;
        }

        int se = open(dev_path.c_str(), O_WRONLY);
        if (se < 0) {
            perror("ERROR: open() failed for stderr");
            goto child_ret_err;
        }
        ret = dup2(se, 2);
        if (ret < 0) {
            perror("ERROR: dup2() failed for stderr");
            goto child_ret_err;
        }
        ret = close(se);
        if (ret < 0) {
            perror("ERROR: close() failed for stderr");
            goto child_ret_err;
        }

        ret = execvp(argv[1], argv + 1);
        perror("ERROR: execvp() failed");
            goto child_ret_err;
    }

    // Wait for child process
    {
        int logged_wstatus;
        pid_t logged_wpid = waitpid(logged_pid, &logged_wstatus, 0);
        if (logged_wpid < 0) {
            perror("ERROR: waitpid(logged) failed");
            goto kill_logged_child;
        }
        ret = kill(cuse_pid, SIGTERM);
        if (ret < 0) {
            perror("ERROR: kill(fuse) failed");
            goto ret_err;
        }
        int fuse_wstatus;
        pid_t fuse_wpid = waitpid(cuse_pid, &fuse_wstatus, 0);
        if (fuse_wpid < 0) {
            perror("ERROR: waitpid(fuse) failed");
            goto ret_err;
        }
        if (!WIFEXITED(logged_wstatus)) {
            fputs("ERROR: child process did not exit itself", stderr);
            goto ret_err;
        }
        return WEXITSTATUS(logged_wstatus);
    }

kill_logged_child:
        kill(logged_pid, SIGTERM);
kill_cuse_child:
        kill(cuse_pid, SIGTERM);
ret_err:
child_ret_err:
        return 1;
}
