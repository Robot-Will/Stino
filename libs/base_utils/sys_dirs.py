#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
from . import sys_info


def get_document_path():
    """Function Docs."""
    _os_name = sys_info.get_os_name()
    if _os_name == 'windows':
        if sys_info.get_python_version() < 3:
            import _winreg as winreg
        else:
            import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows' +
            r'\CurrentVersion\Explorer\Shell Folders',)
        document_path = winreg.QueryValueEx(key, 'Personal')[0]
    elif _os_name == 'osx':
        home_path = os.getenv('HOME')
        document_path = os.path.join(home_path, 'Documents')
    else:
        document_path = os.getenv('HOME')
    return document_path


def get_tmp_path():
    """Function Docs."""
    tmp_path = '/tmp'
    if sys_info.get_os_name() == 'windows':
        tmp_path = os.environ['tmp']
    return tmp_path


def get_user_config_path():
    """Function Docs."""
    _os_name = sys_info.get_os_name()
    home = os.getenv('HOME')
    if _os_name == 'windows':
        user_config_path = os.getenv('LOCALAPPDATA')
        if not user_config_path:
            user_config_path = os.getenv('APPDATA')
    elif _os_name == 'linux':
        user_config_path = os.path.join(home, '.config')
    elif _os_name == 'osx':
        user_config_path = os.path.join(home, 'Library')
    return user_config_path
