# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

DESTDIR ?=
PREFIX ?= /usr

nestedlog-helper: LDLIBS+=-lfuse
nestedlog-helper: nestedlog-helper.cpp

.PHONY: clean
clean:
	rm -f nestedlog-helper

# FIXME: This skips installing Python modules, docs, and example scripts,
# because we don't need to do that when building via Debian packaging. This
# rule should be enhanced to install all those things for people not building
# Debian packages.
.PHONY: install
install: nestedlog-helper
	install -D -o 0 -g 0 -m 0755 -t "$(DESTDIR)$(PREFIX)/bin" nestedlog
	install -D -o 0 -g 0 -m 0755 -t "$(DESTDIR)$(PREFIX)/bin" nestedlog-email
	install -D -o 0 -g 0 -m 04755 -t "$(DESTDIR)$(PREFIX)/bin" nestedlog-helper
