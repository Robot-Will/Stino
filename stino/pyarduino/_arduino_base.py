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

from . import base
from . import arduino_root_dir
from . import arduino_root_path
from . import platform_file


def get_parent_id(child_id):
    parent_id = ''
    ids = child_id.split('.')[:-1]
    parent_id = '.'.join(ids)
    return parent_id


@base.deco.singleton
class ArduinoInfo:
    def __init__(self):
        ide_path = arduino_root_path.get_arduino_ide_path()
        sketchbook_path = arduino_root_path.get_sketchbook_path()
        self.ide_dir = arduino_root_dir.ArduinoIdeDir(
            arduino_root_path.update_ide_path(ide_path))
        self.sketchbook_dir = arduino_root_dir.SketchbookDir(sketchbook_path)
        self.load_root_dirs()

    def sketchbook_update(self):
        self.sketchbook_dir.reload()
        self.load_root_dirs()

    def update(self):
        self.ide_dir.reload()
        self.sketchbook_dir.reload()
        self.load_root_dirs()

    def load_root_dirs(self):
        self.id_item_dict = {}
        self.h_lib_dict = {}
        self.target_platform_id = ''
        self.target_board_id = ''
        self.target_sub_board_ids = []
        self.target_programmer_id = ''
        self.target_arch = ''

        self.load_root_dir(self.ide_dir)
        self.load_root_dir(self.sketchbook_dir)
        self.check_target_board_id()
        self.check_target_programmer_id()

    def update_h_lib_dict(self, library):
        h_files = library.list_h_files()
        h_file_names = [f.get_name() for f in h_files]
        for h_file_name in h_file_names:
            self.h_lib_dict[h_file_name] = library

    def load_root_dir(self, root_dir):
        for package in root_dir.get_packages():
            self.id_item_dict[package.get_id()] = package
            for platform in package.get_platforms():
                self.id_item_dict[platform.get_id()] = platform
                for board in platform.get_boards():
                    self.id_item_dict[board.get_id()] = board
                    for board_option in board.get_options():
                        sub_boards = board_option.get_items()
                        for sub_board in sub_boards:
                            self.id_item_dict[sub_board.get_id()] = sub_board
                for programmer in platform.get_programmers():
                    self.id_item_dict[programmer.get_id()] = programmer

    def check_target_board_id(self):
        settings = base.settings.get_arduino_settings()
        self.target_board_id = settings.get('target_board_id', '')
        if not self.target_board_id in self.id_item_dict:
            self.target_board_id = self.get_default_board_id()
            settings.set('target_board_id', self.target_board_id)
        self.check_target_sub_board_ids()
        self.check_target_platform_id()

    def check_target_sub_board_ids(self):
        if not self.target_board_id:
            return
        settings = base.settings.get_arduino_settings()
        target_sub_board_ids = settings.get(self.target_board_id, [])
        target_board = self.id_item_dict.get(self.target_board_id)
        board_options = target_board.get_options()
        if len(target_sub_board_ids) != len(board_options):
            sub_boards = target_board.get_default_sub_items()
            target_sub_board_ids = [sb.get_id() for sb in sub_boards]
        else:
            for index, option in enumerate(board_options):
                target_sub_board_id = target_sub_board_ids[index]
                if not option.get_item(target_sub_board_id):
                    target_sub_board_id = option.get_default_item()
                    target_sub_board_ids[index] = target_sub_board_id
        if target_sub_board_ids:
            self.target_sub_board_ids = target_sub_board_ids
            settings.set(self.target_board_id, self.target_sub_board_ids)

    def check_target_platform_id(self):
        if not self.target_board_id:
            return
        self.target_platform_id = get_parent_id(self.target_board_id)
        self.target_arch = self.target_platform_id.split('.')[-1]
        self.load_libraries()

    def check_target_programmer_id(self):
        settings = base.settings.get_arduino_settings()
        self.target_programmer_id = settings.get('target_programmer_id', '')
        if not self.target_programmer_id in self.id_item_dict:
            self.target_programmer_id = ''
            for root in [self.ide_dir, self.sketchbook_dir]:
                for package in root.get_packages():
                    for platform in package.get_platforms():
                        programmers = platform.get_programmers()
                        if programmers:
                            self.target_programmer_id = programmers[0].get_id()
                            break
                    if self.target_programmer_id:
                        break
                if self.target_programmer_id:
                    break
            if self.target_programmer_id:
                settings.set('target_programmer_id', self.target_programmer_id)

    def load_libraries(self):
        self.h_lib_dict = {}
        for root in [self.ide_dir, self.sketchbook_dir]:
            libraries = root.get_libraries()
            for library in libraries:
                arch = library.get_arch()
                if arch == '*' or arch == self.target_arch:
                    self.update_h_lib_dict(library)
            for package in root.get_packages():
                for platform in package.get_platforms():
                    if platform.get_arch() == self.target_arch:
                        libraries = platform.get_libraries()
                        for library in libraries:
                            self.update_h_lib_dict(library)

    def get_default_board_id(self):
        board_id = ''
        for root in (self.ide_dir, self.sketchbook_dir):
            if root.get_packages():
                package = root.get_packages()[0]
                platform = package.get_platforms()[0]
                board = platform.get_boards()[0]
                board_id = board.get_id()
                break
        return board_id

    def set_default_platform_id(self):
        target_package_id = 'ide.arduino'
        self.target_platform_id = target_package_id + '.' + self.target_arch

    def change_ide_path(self, ide_path):
        settings = base.settings.get_arduino_settings()
        ide_path = os.path.abspath(ide_path)
        ide_path = arduino_root_path.update_ide_path(ide_path)
        if ide_path != self.ide_dir.get_path():
            if arduino_root_path.is_arduino_ide_path(ide_path):
                settings.set('arduino_ide_path', ide_path)
                self.ide_dir = arduino_root_dir.ArduinoIdeDir(ide_path)
                self.load_root_dirs()

    def change_sketchbook_path(self, sketchbook_path):
        settings = base.settings.get_arduino_settings()
        sketchbook_path = os.path.abspath(sketchbook_path)
        if sketchbook_path != self.sketchbook_dir.get_path():
            settings.set('sketchbook_path', sketchbook_path)
            self.sketchbook_dir = arduino_root_dir.SketchbookDir(
                sketchbook_path)
            self.load_root_dirs()

    def change_board(self, board_id):
        settings = base.settings.get_arduino_settings()
        if board_id != self.target_board_id and board_id in self.id_item_dict:
            self.target_board_id = board_id
            settings.set('target_board_id', board_id)
            self.check_target_sub_board_ids()
            self.check_target_platform_id()

    def change_sub_board(self, sub_board_id):
        settings = base.settings.get_arduino_settings()
        if sub_board_id in self.id_item_dict:
            target_sub_board_ids = settings.get(self.target_board_id, [])
            target_board = self.id_item_dict.get(self.target_board_id)
            index = target_board.get_option_index(sub_board_id)
            if index >= 0:
                target_sub_board_ids[index] = sub_board_id
                settings.set(self.target_board_id, target_sub_board_ids)

    def change_programmer(self, programmer_id):
        settings = base.settings.get_arduino_settings()
        if programmer_id in self.id_item_dict:
            settings.set('target_programmer_id', programmer_id)
            self.check_target_programmer_id()

    def ide_is_valid(self):
        state = False
        if arduino_root_path.is_arduino_ide_path(self.ide_dir.get_path()):
            state = True
        return state

    def get_root_dirs(self):
        return [self.ide_dir, self.sketchbook_dir]

    def get_ide_dir(self):
        return self.ide_dir

    def get_sketchbook_dir(self):
        return self.sketchbook_dir

    def get_h_lib_dict(self):
        return self.h_lib_dict

    def get_library_dir(self, header):
        return self.h_lib_dict(header)

    def get_target_platform(self):
        target_platform = self.id_item_dict.get(self.target_platform_id)
        return target_platform

    def get_target_board_params(self):
        params = {}
        if not self.target_board_id:
            return params
        target_board = self.id_item_dict.get(self.target_board_id)
        params = target_board.get_params()

        options = target_board.get_options()
        for index, option in enumerate(options):
            sub_board_id = self.target_sub_board_ids[index]
            sub_board = option.get_item(sub_board_id)
            sub_board_params = sub_board.get_params()
            params.update(sub_board_params)

        if 'build.cpu' in params:
            params['build.mcu'] = params['build.cpu']

        if not 'build.board' in params:
            arch = self.target_board_id.split('.')[-2]
            board_name = self.target_board_id.split('.')[-1]
            build_board = (arch + '_' + board_name).upper()
            params['build.board'] = build_board

        if not 'upload.maximum_data_size' in params:
            params['upload.maximum_data_size'] = '0'
            build_mcu = params.get('build.mcu', 'unkonwn_mcu')
            if build_mcu:
                ram_size_settings = base.settings.get_user_settings(
                    'ram_size.settings')
                ram_size = ram_size_settings.get(build_mcu, '0')
                params['upload.maximum_data_size'] = ram_size

        if 'build.vid' in params:
            if not 'build.extra_flags' in params:
                params['build.extra_flags'] = '{build.usb_flags}'
        if 'bootloader.path' in params and 'bootloader.file' in params:
            bootloader_path = params['bootloader.path']
            bootloader_file = params['bootloader.file']
            bootloader_file = bootloader_path + '/' + bootloader_file
            params['bootloader.file'] = bootloader_file
        return params

    def get_target_programmer_params(self):
        params = {}
        if not self.target_programmer_id:
            return params
        target_programmer = self.id_item_dict[self.target_programmer_id]
        params = target_programmer.get_params()
        if not 'program.extra_params' in params:
            program_extra_params = ''
            short_id = self.target_programmer_id.split('.')[-1]
            if short_id == 'avrisp':
                program_extra_params = '-P{serial.port}'
            elif short_id == 'avrispmkii':
                program_extra_params = '-Pusb'
            elif short_id == 'usbasp':
                program_extra_params = '-Pusb'
            elif short_id == 'parallel':
                program_extra_params = '-F'
            elif short_id == 'arduinoasisp':
                program_extra_params = '-P{serial.port} -b{program.speed}'
            params['program.extra_params'] = program_extra_params
        return params

    def get_target_params(self):
        target_params = {}
        self.target_platform_file = None
        if self.target_board_id:
            target_platform = self.id_item_dict[self.target_platform_id]
            self.target_platform_file = target_platform.get_platform_file()
            target_platform_params = target_platform.get_params()

            board_id = self.target_board_id.split('.')[-1]
            borad_platform_settings = base.settings.get_user_settings(
                'platform.settings')
            platform_file_name = borad_platform_settings.get(board_id, '')
            if platform_file_name:
                preset_path = base.settings.get_preset_path()
                user_preset_path = base.settings.get_user_preset_path()
                platform_file_path = os.path.join(user_preset_path,
                                                  platform_file_name)
                if not os.path.isfile(platform_file_path):
                    platform_file_path = os.path.join(preset_path,
                                                      platform_file_name)
                self.target_platform_file = platform_file.PlatformFile(
                    platform_file_path)
            params = self.target_platform_file.get_params()
            if params:
                target_platform_params = params

            target_programmer_params = self.get_target_programmer_params()
            target_board_params = self.get_target_board_params()

            target_params.update(target_platform_params)
            target_params.update(target_programmer_params)
            target_params.update(target_board_params)
        return target_params

    def get_target_arch(self):
        return self.target_arch

    def get_version(self):
        return self.ide_dir.get_version()

    def get_target_board_id(self):
        return self.target_board_id

    def get_target_sub_board_ids(self):
        return self.target_sub_board_ids

    def get_target_board(self):
        target_board = None
        if self.target_board_id:
            target_board = self.id_item_dict[self.target_board_id]
        return target_board

    def get_id_item_dict(self):
        return self.id_item_dict

    def get_tool_params(self, tool_name):
        tool_params = {}
        target_platform_file = None
        if ':' in tool_name:
            package_name, tool_name = tool_name.split(':')
            package_name = package_name.strip()
            tool_name = tool_name.strip()

            for root_id in ['ide', 'sketchbook']:
                package_id = root_id + '.' + package_name
                if package_id in self.id_item_dict:
                    platform_id = package_id + '.' + self.arch
                    if platform_id in self.id_item_dict:
                        platform = self.id_item_dict[platform_id]
                        target_platform_file = platform.get_platform_file()
                        break
        if not target_platform_file:
            target_platform_file = self.target_platform_file

        if target_platform_file:
            tool = target_platform_file.get_tool(tool_name)
            if tool:
                tool_params = tool.get_params()

        os_name = base.sys_info.get_os_name()
        for key in tool_params:
            if key.endswith(os_name):
                value = tool_params[key]
                key_words = key.split('.')[:-1]
                key = '.'.join(key_words)
                tool_params[key] = value
        return tool_params
