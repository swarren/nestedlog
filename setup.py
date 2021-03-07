# Copyright 2021 Stephen Warren <swarren@wwwdotorg.org>
# SPDX-License-Identifier: MIT

from setuptools import setup

classifiers = [
    'Development Status :: 5 - Production/Stable',
    'Environment :: Console',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python :: 3',
    'Programming Language :: C++',
    'Topic :: Communications :: Email',
    'Topic :: System :: Logging',
    'Topic :: System :: Systems Administration',
    'Topic :: Utilities',
]

setup(
    name             = 'nestedlog',
    version          = '1',
    author           = 'Stephen Warren',
    author_email     = 'swarren@wwwdotorg.org',
    description      = 'A block-based log capture utility with formatted output',
    long_description = '''Executes a logged command. Captures stdout and stderr separately. Generates
 a log file that shows which stream the data came from and how it was
 interleaved. Can break the log into separate blocks to highlight which
 actions passed or failed.''',
    license          = 'MIT',
    classifiers      = classifiers,
    package_dir      = {'': 'lib/python/'},
    packages         = ['nestedlog',],
)
