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

import os

from . import sys_info

ROOT_PATH = 'System Root(/)'

def list_win_volume():
    vol_list = []
    for label in range(67, 90):
        vol = chr(label) + ':\\'
        if os.path.isdir(vol):
            vol_list.append(vol)
    return vol_list


def list_os_root_path():
    root_list = []
    home_path = os.getenv('HOME')
    os_name = sys_info.get_os_name()
    if os_name == 'windows':
        root_list = list_win_volume()
    elif os_name == 'osx':
        root_list = [home_path, '/Applications', ROOT_PATH]
    else:
        root_list = [home_path, '/usr', '/opt', ROOT_PATH]
    return root_list


def list_user_root_path():
    root_list = []
    os_name = sys_info.get_os_name()
    if os_name == 'windows':
        root_list = list_win_volume()
    else:
        home_path = os.getenv('HOME')
        root_list = [home_path, ROOT_PATH]
    return root_list


def get_document_path():
    os_name = sys_info.get_os_name()
    if os_name == 'windows':
        python_version = sys_info.get_python_version()
        if python_version < 3:
            import _winreg as winreg
        else:
            import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows' +
            r'\CurrentVersion\Explorer\Shell Folders',)
        document_path = winreg.QueryValueEx(key, 'Personal')[0]
    elif os_name == 'osx':
        home_path = os.getenv('HOME')
        document_path = os.path.join(home_path, 'Documents')
    else:
        document_path = os.getenv('HOME')
    return document_path


def get_tmp_path():
    tmp_path = '/tmp'
    os_name = sys_info.get_os_name()
    if os_name == 'windows':
        tmp_path = os.environ['tmp']
    return tmp_path
