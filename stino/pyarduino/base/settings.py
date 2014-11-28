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

from . import deco
from . import json_file


class Settings(json_file.JSONFile):
    def __init__(self, path):
        super(Settings, self).__init__(path)

    def get(self, key, default_value=None):
        value = self.data.get(key, default_value)
        return value

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def change_dir_path(self, new_dir_path):
        if os.path.isdir(new_dir_path):
            new_path = os.path.join(new_dir_path, self.name)
            self.set_path(new_path)
        if self.isfile():
            self.load()
        else:
            self.save()


@deco.singleton
class GlobalSettings(Settings):
    pass


this_file_path = os.path.abspath(inspect.getfile(inspect.currentframe()))


def get_package_path():
    dir_path = os.path.dirname(this_file_path)
    package_path = os.path.dirname(dir_path)
    return package_path


def get_package_settings():
    settings_path = os.path.join(get_package_path(), 'pyarduino.settings')
    settings = Settings(settings_path)
    return settings


def get_preset_path():
    settings = get_package_settings()
    package_path = settings.get('package_path', '')
    if not package_path:
        package_path = get_package_path()
    preset_path = os.path.join(package_path, 'preset')
    return preset_path


def get_user_path():
    settings = get_package_settings()
    user_path = settings.get('user_path', '')
    if not user_path:
        user_path = get_package_path()
    return user_path


def get_user_preset_path():
    preset_path = os.path.join(get_user_path(), 'preset')
    return preset_path


def get_arduino_settings():
    settings_file_name = 'Preferences.stino-settings'
    settings_file_path = os.path.join(get_user_path(), settings_file_name)
    settings = GlobalSettings(settings_file_path)
    return settings


def get_user_settings(file_name):
    data_dict = {}
    for path in [get_preset_path(), get_user_preset_path()]:
        settings_path = os.path.join(path, file_name)
        settings = Settings(settings_path)
        data_dict.update(settings.get_data())
    return data_dict
