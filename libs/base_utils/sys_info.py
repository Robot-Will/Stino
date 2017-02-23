#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys
import codecs
import locale


def get_python_version():
    """Function Docs."""
    python_version = sys.version_info[0]
    return python_version


def get_os_name():
    """Function Docs."""
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


def get_host():
    """Function Docs."""
    machine = 'pc'
    ext = 'x32'

    if is_x64():
        ext = 'x64'
    host = '-'.join((machine, get_os_name(), ext))
    return host


def get_sys_encoding():
    """Function Docs."""
    if get_os_name() == 'osx':
        sys_encoding = 'utf-8'
    else:
        sys_encoding = codecs.lookup(locale.getpreferredencoding()).name
    return sys_encoding


def get_sys_language():
    """Function Docs."""
    sys_language = locale.getdefaultlocale()[0]
    if not sys_language:
        sys_language = 'en'
    else:
        sys_language = sys_language.lower()
    return sys_language


def is_x64():
    """Function Docs."""
    return sys.maxsize > 2**32


def is_in_submlimetext():
    """Function Docs."""
    state = False
    try:
        import sublime
    except ImportError:
        pass
    else:
        state = True
    return state
