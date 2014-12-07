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
import re
import time

from . import base
from . import arduino_platform
from . import arduino_info


class TargetParamsInfo(object):
    def __init__(self):
        self.target_params = {}
        self.arduino_info = arduino_info.get_arduino_info()
        self.load()

    def load(self):
        self.load_params()
        if self.target_params:
            self.load_paths()

    def load_params(self):
        self.target_platform_file = get_platform_file(self.arduino_info)
        if not self.target_platform_file:
            return
        target_platform_params = self.target_platform_file.get_params()

        target_board_info = self.arduino_info.get_target_board_info()
        target_board_params = target_board_info.get_params()

        target_programmer_info = self.arduino_info.get_target_programmer_info()
        target_programmer_params = target_programmer_info.get_params()

        self.target_params.update(target_platform_params)
        self.target_params.update(target_board_params)
        self.target_params.update(target_programmer_params)

        target_upload_tool = self.target_params.get(
            'upload.tool', '')
        target_upload_params = get_tool_params(
            self.arduino_info, self.target_platform_file,
            target_upload_tool, 'upload')
        self.target_params.update(target_upload_params)

        target_program_tool = self.target_params.get(
            'program.tool', '')
        target_program_params = get_tool_params(
            self.arduino_info, self.target_platform_file,
            target_program_tool, 'program')
        self.target_params.update(target_program_params)

        target_bootloader_tool = self.target_params.get(
            'bootloader.tool', '')
        target_bootloader_params = get_tool_params(
            self.arduino_info, self.target_platform_file,
            target_bootloader_tool, 'bootloader')
        self.target_params.update(target_bootloader_params)

        # For Teensy
        target_post_compile_params = get_tool_params(
            self.arduino_info, self.target_platform_file,
            'teensy', 'post_compile')
        self.target_params.update(target_post_compile_params)

        add_extra_params(self.arduino_info, self.target_params)

        for key in self.target_params:
            value = self.target_params.get(key)
            if '-P{serial.port}' in value:
                value = value.replace('-P{serial.port}', '"-P{serial.port}"')
            if '--port={serial.port.file}' in value:
                value = value.replace('--port={serial.port.file}',
                                      '"--port={serial.port.file}"')
            if ' {serial.port} ' in value:
                value = value.replace(' {serial.port} ', ' "{serial.port}" ')
            self.target_params[key] = value

    def load_paths(self):
        target_board_info = self.arduino_info.get_target_board_info()
        target_board_params = target_board_info.get_params()
        target_build_core_dir_name = target_board_params.get(
            'build.core', 'arduino:arduino')
        target_build_var_dir_name = target_board_params.get(
            'build.variant', 'arduino:standard')
        target_build_core_path = get_target_path(
            self.arduino_info, 'cores', target_build_core_dir_name)
        target_build_var_path = get_target_path(
            self.arduino_info, 'variants', target_build_var_dir_name)
        self.target_params['build.core.path'] = target_build_core_path
        self.target_params['build.variant.path'] = target_build_var_path

    def replace_values(self):
        self.target_params = replace_param_values(self.target_params)

    def get_params(self):
        return self.target_params


def get_target_path(arduino_info, dirs_name, target_build_dir_name):
    ide_path = arduino_info.get_ide_dir().get_path()
    parent_path = os.path.join(ide_path, dirs_name)
    sub_name = target_build_dir_name
    if ':' in sub_name:
        sub_name = sub_name.split(':')[1]
    target_build_dir_path = os.path.join(parent_path, sub_name)

    id_platform_dict = {}
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                id_platform_dict[platform.get_id()] = platform

    target_platform = None
    target_arch = arduino_info.get_target_board_info().get_target_arch()
    target_package_id, target_build_dir_name = get_target_package_id(
        arduino_info, target_build_dir_name)

    if target_package_id:
        target_platform_id = target_package_id + '.' + target_arch
    else:
        target_board = arduino_info.get_target_board_info().get_target_board()
        target_board_id = target_board.get_id()
        ids = target_board_id.split('.')[:-1]
        target_platform_id = '.'.join(ids)
    target_platform = id_platform_dict.get(target_platform_id, None)
    if target_platform:
        target_platform_path = target_platform.get_path()
        dirs_path = os.path.join(target_platform_path, dirs_name)
        dir_path = os.path.join(dirs_path, target_build_dir_name)
        if os.path.isdir(dir_path):
            target_build_dir_path = dir_path
    else:
        target_package_id = 'ide.arduino'
        target_platform_id = target_package_id + '.' + target_arch
        target_platform = id_platform_dict.get(target_platform_id, None)
        if target_platform:
            target_platform_path = target_platform.get_path()
            dirs_path = os.path.join(target_platform_path, dirs_name)
            dir_path = os.path.join(dirs_path, target_build_dir_name)
            if os.path.isdir(dir_path):
                target_build_dir_path = dir_path
    return target_build_dir_path


def get_target_package_id(arduino_info, target_value):
    target_package_id = ''
    if ':' in target_value:
        target_package_name, target_value = target_value.split(':')

        package_ids = []
        for root_dir in arduino_info.get_root_dirs():
            for package in root_dir.get_packages():
                package_ids.append(package.get_id())
        for root_id in ['ide', 'sketchbook']:
            package_id = root_id + '.' + target_package_name
            if package_id in package_ids:
                target_package_id = package_id
                break
    return target_package_id, target_value


def get_platform_file(arduino_info):
    id_platform_dict = {}
    target_platform_file = None
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                id_platform_dict[platform.get_id()] = platform

    target_board_info = arduino_info.get_target_board_info()
    target_board = target_board_info.get_target_board()
    if target_board:
        target_board_id = target_board.get_id()
        ids = target_board_id.split('.')[:-1]
        target_platform_id = '.'.join(ids)
        target_platform = id_platform_dict.get(target_platform_id)
        target_platform_file = target_platform.get_platform_file()

        target_board_name = target_board.get_params().get('name', '')
    else:
        target_board_name = 'No Board'

    board_platform_settings = base.settings.get_user_settings(
        'platform.settings')
    platform_file_name = board_platform_settings.get(target_board_name, '')

    if platform_file_name:
        preset_path = base.settings.get_preset_path()
        user_preset_path = base.settings.get_user_preset_path()
        platform_file_path = os.path.join(user_preset_path,
                                          platform_file_name)
        if not os.path.isfile(platform_file_path):
            platform_file_path = os.path.join(preset_path,
                                              platform_file_name)
        if os.path.isfile(platform_file_path):
            target_platform_file = arduino_platform.PlatformFile(
                platform_file_path)
    return target_platform_file


def get_tool_params(arduino_info, target_platform_file,
                    target_tool_value, sub_id):
    target_tool_params = {}

    tool = None
    id_platform_dict = {}
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                id_platform_dict[platform.get_id()] = platform

    if target_tool_value:
        target_platform = None
        target_arch = arduino_info.get_target_board_info().get_target_arch()

        target_package_id, target_tool_value = get_target_package_id(
            arduino_info, target_tool_value)

        if target_package_id:
            target_platform_id = target_package_id + '.' + target_arch
            target_platform = id_platform_dict.get(target_platform_id, None)
            if target_platform:
                tool = target_platform.get_tool(target_tool_value)
        if not tool:
            tool = target_platform_file.get_tool(target_tool_value)
    else:
        tool = target_platform_file.get_default_tool()

    if tool:
        params = tool.get_params()
        params = std_tool_param_values(params)
        params = replace_param_values(params)

        for key in params:
            if key.startswith(sub_id + '.'):
                value = params[key]
                target_tool_params[key] = value
            if sub_id == 'bootloader' and key.startswith('erase.'):
                value = params[key]
                target_tool_params[key] = value
    return target_tool_params


def gen_replaced_text_list(text):
    pattern_text = r'\{\S+?}'
    pattern = re.compile(pattern_text)
    replaced_text_list = pattern.findall(text)
    return replaced_text_list


def replace_param_value(value, params):
    replaced_text_list = gen_replaced_text_list(value)
    for text in replaced_text_list:
        key = text[1:-1]
        if key in params:
            param_value = params[key]
            param_value = replace_param_value(param_value, params)
            value = value.replace(text, param_value)
    return value


def replace_param_values(params):
    new_params = {}
    for key in params:
        value = params.get(key)
        if '{' in value:
            value = replace_param_value(value, params)
        new_params[key] = value
    return new_params


def std_tool_param_values(params):
    new_params = {}
    os_name = base.sys_info.get_os_name()
    for key in params:
        value = params.get(key)
        if key.endswith('.' + os_name):
            ids = key.split('.')[:-1]
            key = '.'.join(ids)
        new_params[key] = value
    return new_params


def get_target_platform(arduino_info):
    id_platform_dict = {}
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                id_platform_dict[platform.get_id()] = platform

    target_board = arduino_info.get_target_board_info().get_target_board()
    target_board_id = target_board.get_id()
    ids = target_board_id.split('.')[:-1]
    target_platform_id = '.'.join(ids)

    target_platform = id_platform_dict.get(target_platform_id)
    return target_platform


def add_extra_params(arduino_info, params):
    ide_version = arduino_info.get_ide_dir().get_version()
    ide_path = arduino_info.get_ide_dir().get_path()
    sketchbook_path = arduino_info.get_sketchbook_dir().get_path()
    target_arch = arduino_info.get_target_board_info().get_target_arch()
    target_platform = get_target_platform(arduino_info)
    target_platform_path = target_platform.get_path()
    target_system_path = os.path.join(target_platform_path, 'system')

    params['software'] = 'ARDUINO'
    params['build.arch'] = target_arch.upper()
    params['runtime.ide.version'] = ide_version
    params['runtime.sketchbook.path'] = sketchbook_path
    params['runtime.ide.path'] = ide_path
    params['runtime.platform.path'] = target_platform_path
    params['build.system.path'] = target_system_path

    # For Arduino
    if not 'build.board' in params:
        target_board = arduino_info.get_target_board_info().get_target_board()
        target_board_id = target_board.get_id()
        board_name = target_board_id.split('.')[-1]
        build_board = (target_arch + '_' + board_name).upper()
        params['build.board'] = build_board

    if 'build.vid' in params and not params['build.extra_flags']:
        params['build.extra_flags'] = \
            '-DUSB_VID={build.vid} -DUSB_PID={build.pid}'

    if not 'upload.maximum_data_size' in params:
        params['upload.maximum_data_size'] = '0'
        build_mcu = params.get('build.mcu', 'unkonwn_mcu')
        if build_mcu != 'unkonwn_mcu':
            ram_size_settings = base.settings.get_user_settings(
                'ram_size.settings')
            ram_size = ram_size_settings.get(build_mcu, '0')
            params['upload.maximum_data_size'] = ram_size

    if 'bootloader.path' in params and 'bootloader.file' in params:
        bootloader_path = params['bootloader.path']
        bootloader_file = params['bootloader.file']
        bootloader_file = bootloader_path + '/' + bootloader_file
        params['bootloader.file'] = bootloader_file

    if not 'program.extra_params' in params:
        program_extra_params = ''
        target_programmer = \
            arduino_info.get_target_programmer_info().get_target_programmer()
        if target_programmer:
            target_programmer_id = target_programmer.get_id()
            programmer_name = target_programmer_id.split('.')[-1]
            if programmer_name == 'avrisp':
                program_extra_params = '-P{serial.port}'
            elif programmer_name == 'avrispmkii':
                program_extra_params = '-Pusb'
            elif programmer_name == 'usbasp':
                program_extra_params = '-Pusb'
            elif programmer_name == 'parallel':
                program_extra_params = '-F'
            elif programmer_name == 'arduinoasisp':
                program_extra_params = '-P{serial.port} -b{program.speed}'
            params['program.extra_params'] = program_extra_params

    params['build.usb_manufacturer'] = '"Unknown"'

    settings = base.settings.get_arduino_settings()
    show_upload_output = settings.get('upload_verbose', False)
    for key in params:
        value = params.get(key)
        if '.verbose}' in value:
            if show_upload_output:
                value = value.replace('.verbose}', '.params.verbose}')
            else:
                value = value.replace('.verbose}', '.params.quiet}')
            params[key] = value

    # For Teensy
    build_elide_constructors = params.get('build.elide_constructors', '')
    if build_elide_constructors:
        build_elide_constructors = '-felide-constructors'
    params['build.elide_constructors'] = build_elide_constructors

    build_gnu0x = params.get('build.gnu0x', '')
    if build_gnu0x:
        build_gnu0x = '-std=gnu++0x'
    params['build.gnu0x'] = build_gnu0x

    build_cpp0x = params.get('build.cpp0x', '')
    if build_cpp0x:
        build_cpp0x = '-std=c++0x'
    params['build.cpp0x'] = build_cpp0x

    build_time_t = params.get('build.time_t', '')
    if build_time_t:
        build_time_t = '-DTIME_T=%d' % int(time.time())
    params['build.time_t'] = build_time_t

    build_serial_number = params.get('build.serial_number', '')
    if build_serial_number:
        build_serial_number = '-DSERIALNUM=%d' % int(time.time())
    params['build.serial_number'] = build_serial_number

    if 'upload.maximum_ram_size' in params:
        params['upload.maximum_data_size'] = params['upload.maximum_ram_size']

    if 'upload.ram.maximum_size'  in params:
        params['upload.maximum_data_size'] = params['upload.ram.maximum_size']
