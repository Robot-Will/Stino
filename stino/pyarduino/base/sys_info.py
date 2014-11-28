#!/usr/bin/env python
#-*- coding: utf-8 -*-

# 1. Copyright
# 2. Lisence
# 3. Author

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys
import codecs
import locale


def get_python_version():
    python_version = sys.version_info[0]
    return python_version


def get_os_name():
    name = sys.platform
    if name == 'win32':
        os_name = 'windows'
    elif name == 'darwin':
        os_name = 'osx'
    elif 'linux' in name:
        os_name = 'linux'
    else:
        os_name = 'other'
    return os_name


def get_sys_encoding():
    if get_os_name() == 'osx':
        sys_encoding = 'utf-8'
    else:
        sys_encoding = codecs.lookup(locale.getpreferredencoding()).name
    return sys_encoding


def get_sys_language():
    sys_language = locale.getdefaultlocale()[0]
    if not sys_language:
        sys_language = 'en'
    else:
        sys_language = sys_language.lower()
    return sys_language
