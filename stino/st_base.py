#!/usr/bin/env python
#-*- coding: utf-8 -*-

#
# Documents
#

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import inspect

from . import pyarduino


this_file_path = os.path.abspath(inspect.getfile(inspect.currentframe()))


def get_plugin_path():
    this_folder_path = os.path.dirname(this_file_path)
    plugin_path = os.path.dirname(this_folder_path)
    return plugin_path


def get_packages_path():
    plugin_path = get_plugin_path()
    packages_path = os.path.dirname(plugin_path)
    return packages_path


def get_stino_user_path():
    packages_path = get_packages_path()
    user_path = os.path.join(packages_path, 'User')
    stino_user_path = os.path.join(user_path, 'Stino')
    return stino_user_path


def get_preset_path():
    plugin_path = get_plugin_path()
    preset_path = os.path.join(plugin_path, 'preset')
    return preset_path


def get_user_preset_path():
    stino_user_path = get_stino_user_path()
    preset_path = os.path.join(stino_user_path, 'preset')
    return preset_path


def get_user_menu_path():
    stino_user_path = get_stino_user_path()
    preset_path = os.path.join(stino_user_path, 'menu')
    return preset_path


def get_settings():
    settings = pyarduino.base.settings.get_arduino_settings()
    return settings


def get_arduino_info():
    arduino_info = pyarduino.arduino_info.get_arduino_info()
    return arduino_info


def get_i18n():
    i18n = pyarduino.base.i18n.I18N()
    return i18n
