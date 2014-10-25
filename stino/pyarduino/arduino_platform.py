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
import platform as os_platform

from . import base
from . import arduino_item
from . import arduino_library
from . import arduino_params_file


class Platform(base.abs_file.Dir):
    def __init__(self, package_id, path):
        super(Platform, self).__init__(path)
        self.load_arch(package_id)
        self.load_platform_params()
        self.load_boards()
        self.load_programmers()
        self.load_libraries()

    def load_arch(self, package_id):
        self.arch = self.name.lower()
        package_name = package_id.split('.')[-1]
        if self.name.lower() == package_name.lower():
            self.arch = 'avr'
        self.id = package_id + '.' + self.arch
        self.caption = '%s %s Boards' % (package_name.upper(),
                                         self.arch.upper())

    def load_platform_params(self):
        is_default_platform = False
        platform_file_path = os.path.join(self.path, 'platform.txt')
        if not os.path.isfile(platform_file_path):
            os_name = base.sys_info.get_os_name()
            if os_name == 'windows':
                os_name = 'win'
            bit = os_platform.architecture()[0][:2]
            file_name = 'platform.' + os_name + bit + '.txt'
            platform_file_path = os.path.join(self.path, file_name)
        if not os.path.isfile(platform_file_path):
            file_name = 'platform.' + os_name + '.txt'
            platform_file_path = os.path.join(self.path, file_name)
        if not os.path.isfile(platform_file_path):
            file_name = 'platform_' + self.arch + '.txt'
            user_preset_path = base.settings.get_user_preset_path()
            platform_file_path = os.path.join(user_preset_path, file_name)
            is_default_platform = True
        if not os.path.isfile(platform_file_path):
            preset_path = base.settings.get_preset_path()
            platform_file_path = os.path.join(preset_path, file_name)
            is_default_platform = True
        self.platform_file = PlatformFile(platform_file_path)
        self.platform_params = self.platform_file.get_params()
        self.tool_set = self.platform_file.get_tool_set()

        if not is_default_platform:
            self.caption = self.platform_params.get('name', self.caption)

    def load_boards(self):
        file_path = os.path.join(self.path, 'boards.txt')
        boards_file = arduino_item.ItemsFile(self.id, file_path)
        self.board_set = boards_file.get_item_set()

    def load_programmers(self):
        file_path = os.path.join(self.path, 'programmers.txt')
        programmers_file = arduino_item.ItemsFile(self.id, file_path)
        self.programmer_set = programmers_file.get_item_set()

    def load_libraries(self):
        libraries_path = os.path.join(self.path, 'libraries')
        self.library_set = arduino_library.LibrarySet(self.id, libraries_path)

    def get_id(self):
        return self.id

    def get_caption(self):
        return self.caption

    def get_arch(self):
        return self.arch

    def get_params(self):
        return self.platform_params

    def get_boards(self):
        return self.board_set.get_items()

    def get_board(self, board_id):
        return self.board_set.get_item(board_id)

    def get_default_board(self):
        return self.board_set.get_default_item()

    def get_programmers(self):
        return self.programmer_set.get_items()

    def get_programmer(self, programmer_id):
        return self.programmer_set.get_item(programmer_id)

    def get_libraries(self):
        return self.library_set.get_libraries()

    def get_library(self, library_id):
        return self.library_set.get_library(library_id)

    def get_tools(self):
        return self.tool_set.get_items()

    def get_tool(self, tool_id):
        return self.tool_set.get_item(tool_id)

    def get_platform_file(self):
        return self.platform_file

    def is_platform(self):
        return bool(self.get_boards())


class PlatformFile(arduino_params_file.ParamsFile):
    def __init__(self, path):
        super(PlatformFile, self).__init__(path)
        self.load()

    def load(self):
        param_pairs = []
        tools_param_pairs = []
        for key, value in self.param_pairs:
            if key.startswith('tools.'):
                index = key.index('.')
                key = key[index + 1:]
                pair = (key, value)
                tools_param_pairs.append(pair)
            else:
                pair = (key, value)
                param_pairs.append(pair)
        self.param_pairs = param_pairs
        self.tools_param_pairs = tools_param_pairs
        self.tool_set = arduino_item.ItemSet(
            '', tools_param_pairs, top_level=False)

    def get_tool_set(self):
        return self.tool_set

    def get_tool(self, tool_id):
        return self.tool_set.get_item(tool_id)

    def get_default_tool(self):
        tool = None
        if self.tool_set.get_items():
            tool = self.tool_set.get_items()[0]
        return tool

    def get_tools(self):
        return self.tool_set.get_items()



# def std_platform_params(platform_params):
#     os_name = sys_base.get_os_name()
#     std_params = {}
#     for key in platform_params:
#         value = platform_params[key]
#         if key.startswith('tools.'):
#             key = key.replace('tools.', '')
#             index = key.index('.')
#             key = key[index + 1:]
#         std_params[key] = value
#     for key in std_params:
#         if key.endswith(os_name):
#             value = std_params[key]
#             key = key.replace('.' + os_name, '')
#             std_params[key] = value
#     return std_params
