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

from . import st_base
from . import pyarduino


class MenuFile(pyarduino.base.json_file.JSONFile):
    def __init__(self, file_path):
        super(MenuFile, self).__init__(file_path)
        self.menus = [Menu(d) for d in self.data]

    def get_menus(self):
        return self.menus


class ArduinoMenuFile(MenuFile):
    def __init__(self, preset_menu_name):
        self.preset_menu_name = preset_menu_name
        preset_path = st_base.get_preset_path()
        preset_file_name = 'menu_' + preset_menu_name + '.txt'
        preset_file_path = os.path.join(preset_path, preset_file_name)
        super(ArduinoMenuFile, self).__init__(preset_file_path)
        self.menu = self.menus[0]
        self.sub_menu = self.menu.get_sub_menus()[0]

    def add_sub_menu(self, sub_menu):
        self.sub_menu.sub_menus.append(sub_menu)

    def add_sub_menus(self, sub_menus):
        self.sub_menu.sub_menus += sub_menus

    def write(self):
        menu_data = [self.menu.get_menu_dict()]
        user_menu_path = st_base.get_user_menu_path()
        target_menu_path = os.path.join(user_menu_path, self.preset_menu_name)
        if not os.path.isdir(target_menu_path):
            os.makedirs(target_menu_path)
        target_file_path = os.path.join(target_menu_path, 'Main.sublime-menu')
        target_file = pyarduino.base.json_file.JSONFile(target_file_path)
        target_file.set_data(menu_data)


class Menu(object):
    def __init__(self, menu_dict=None):
        self.i18n = st_base.get_i18n()

        self.params = menu_dict
        if not self.params:
            self.params = {'caption': '-'}

        self.sub_menus = []
        menu_dicts = self.params.get('children', [])
        for menu_dict in menu_dicts:
            sub_menu = Menu(menu_dict)
            self.sub_menus.append(sub_menu)

    def set(self, key, value):
        self.parmas[key] = value

    def get(self, key, default_value=None):
        return self.params.get(key, default_value)

    def get_sub_menus(self):
        return self.sub_menus

    def set_sub_menus(self, sub_menus):
        self.sub_menus = sub_menus

    def add_sub_menu(self, sub_menu):
        self.sub_menus.append(sub_menu)

    def get_menu_dict(self):
        self.translate()
        if self.sub_menus:
            self.params['children'] = []
            for sub_menu in self.sub_menus:
                sub_menu_dict = sub_menu.get_menu_dict()
                self.params['children'].append(sub_menu_dict)
        else:
            if 'children' in self.params:
                self.params.pop('children')
        return self.params

    def has_sub_menus(self):
        return bool(self.sub_menus)

    def translate(self):
        caption = self.params.get('caption', '')
        caption = self.i18n.translate(caption)
        self.params['caption'] = caption

        for sub_menu in self.sub_menus:
            sub_menu.translate()


def load_sketchbook_menu(sketch):
    menu_dict = {}
    sketch_name = sketch.get_name()
    sketch_path = sketch.get_path()
    sub_sketches = sketch.get_sub_sketches()

    menu_dict['caption'] = sketch_name
    if not sub_sketches:
        menu_dict['command'] = 'open_sketch'
        menu_dict['args'] = {'sketch_path': sketch_path}
    menu = Menu(menu_dict)

    if sub_sketches:
        for sub_sketch in sub_sketches:
            sub_menu = load_sketchbook_menu(sub_sketch)
            menu.add_sub_menu(sub_menu)
    return menu


def write_menu(preset_menu_name, sub_menus):
    if not sub_menus:
        menu_dict = {}
        menu_dict['caption'] = 'None'
        menu_dict['command'] = 'none_command'
        menu = Menu(menu_dict)
        sub_menus.append(menu)
    menu = ArduinoMenuFile(preset_menu_name)
    menu.add_sub_menus(sub_menus)
    menu.write()


def create_main_menu():
    preset_path = st_base.get_preset_path()
    preset_file_name = 'menu_main.txt'
    preset_file_path = os.path.join(preset_path, preset_file_name)
    menu_file = MenuFile(preset_file_path)
    menus = menu_file.get_menus()
    for menu in menus:
        menu.translate()
    menu_dicts = [menu.get_menu_dict() for menu in menus]
    user_menu_path = st_base.get_stino_user_path()
    if not os.path.isdir(user_menu_path):
        os.makedirs(user_menu_path)
    target_file_path = os.path.join(user_menu_path, 'Main.sublime-menu')
    target_file = pyarduino.base.json_file.JSONFile(target_file_path)
    target_file.set_data(menu_dicts)


def create_arduino_menu():
    preset_path = st_base.get_preset_path()
    preset_file_name = 'menu_arduino.txt'
    preset_file_path = os.path.join(preset_path, preset_file_name)
    menu_file = MenuFile(preset_file_path)
    menus = menu_file.get_menus()
    for menu in menus:
        menu.translate()
    menu_dicts = [menu.get_menu_dict() for menu in menus]
    user_menu_path = st_base.get_user_menu_path()
    menu_path = os.path.join(user_menu_path, 'arduino')
    if not os.path.isdir(menu_path):
        os.makedirs(menu_path)
    target_file_path = os.path.join(menu_path, 'Main.sublime-menu')
    target_file = pyarduino.base.json_file.JSONFile(target_file_path)
    target_file.set_data(menu_dicts)


def create_sketchbook_menu(arduino_info):
    sketchbook = arduino_info.get_sketchbook_dir().get_sketchbook()
    sub_menus = load_sketchbook_menu(sketchbook).get_sub_menus()
    write_menu('sketchbook', sub_menus)


def create_examples_menu(arduino_info):
    sub_menus = []
    for root_dir in arduino_info.get_root_dirs():
        examples = root_dir.get_examples()
        examples_menu = load_sketchbook_menu(examples)
        sub_menus += examples_menu.get_sub_menus()
        sub_menus.append(Menu())

        libraries = root_dir.get_libraries()
        for library in libraries:
            lib_arch = library.get_arch()
            caption = '%s (%s)' % (library.get_name(), lib_arch)
            examples = library.get_examples()
            examples.set_name(caption)
            menu = load_sketchbook_menu(examples)
            if menu.has_sub_menus():
                sub_menus.append(menu)
        sub_menus.append(Menu())
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                libraries = platform.get_libraries()
                if libraries:
                    menu_dict = {}
                    menu_dict['caption'] = platform.get_caption()
                    menu_dict['command'] = 'none_command'
                    menu = Menu(menu_dict)
                    sub_menus.append(menu)
                for library in libraries:
                    examples = library.get_examples()
                    menu = load_sketchbook_menu(examples)
                    if menu.has_sub_menus():
                        sub_menus.append(menu)
                sub_menus.append(Menu())
    write_menu('examples', sub_menus)


def create_libraries_menu(arduino_info):
    sub_menus = []
    for root_dir in arduino_info.get_root_dirs():
        libraries = root_dir.get_libraries()
        for library in libraries:
            lib_arch = library.get_arch()
            caption = '%s (%s)' % (library.get_name(), lib_arch)
            menu_dict = {}
            menu_dict['caption'] = caption
            menu_dict['command'] = 'import_library'
            menu_dict['args'] = {'library_path': library.get_path()}
            menu = Menu(menu_dict)
            sub_menus.append(menu)
        sub_menus.append(Menu())
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                libraries = platform.get_libraries()
                if libraries:
                    menu_dict = {}
                    menu_dict['caption'] = platform.get_caption()
                    menu_dict['command'] = 'none_command'
                    menu = Menu(menu_dict)
                    sub_menus.append(menu)
                for library in libraries:
                    menu_dict = {}
                    menu_dict['caption'] = library.get_name()
                    menu_dict['command'] = 'import_library'
                    menu_dict['args'] = {'library_path': library.get_path()}
                    menu = Menu(menu_dict)
                    sub_menus.append(menu)
                sub_menus.append(Menu())
    write_menu('libraries', sub_menus)


def create_boards_menu(arduino_info):
    sub_menus = []
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                menu_dict = {}
                menu_dict['caption'] = platform.get_caption()
                menu_dict['command'] = 'none_command'
                menu = Menu(menu_dict)
                sub_menus.append(menu)
                boards = platform.get_boards()
                for board in boards:
                    menu_dict = {}
                    menu_dict['caption'] = board.get_caption()
                    menu_dict['command'] = 'select_board'
                    menu_dict['args'] = {'board_id': board.get_id()}
                    menu_dict['checkbox'] = True
                    menu = Menu(menu_dict)
                    sub_menus.append(menu)
                sub_menus.append(Menu())
    write_menu('boards', sub_menus)


def create_board_options_menu(arduino_info):
    sub_menus = []
    target_board = arduino_info.get_target_board_info().get_target_board()
    if target_board:
        board_options = target_board.get_options()
        for option_index, option in enumerate(board_options):
            menu_dict = {}
            menu_dict['caption'] = option.get_caption()
            menu_dict['command'] = 'none_command'
            menu = Menu(menu_dict)
            sub_menus.append(menu)
            sub_boards = option.get_items()
            for sub_board in sub_boards:
                menu_dict = {}
                menu_dict['caption'] = sub_board.get_caption()
                menu_dict['command'] = 'select_sub_board'
                menu_dict['args'] = {'option_index': option_index,
                                     'sub_board_id': sub_board.get_id()}
                menu_dict['checkbox'] = True
                menu = Menu(menu_dict)
                sub_menus.append(menu)
            sub_menus.append(Menu())
    write_menu('board_options', sub_menus)


def create_programmers_menu(arduino_info):
    sub_menus = []
    for root_dir in arduino_info.get_root_dirs():
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                platform_menus = []
                menu_dict = {}
                menu_dict['caption'] = platform.get_caption()
                menu_dict['command'] = 'none_command'
                caption_menu = Menu(menu_dict)

                programmers = platform.get_programmers()
                for programmer in programmers:
                    menu_dict = {}
                    menu_dict['caption'] = programmer.get_params().get('name')
                    menu_dict['command'] = 'select_programmer'
                    menu_dict['args'] = {'programmer_id': programmer.get_id()}
                    menu_dict['checkbox'] = True
                    menu = Menu(menu_dict)
                    platform_menus.append(menu)
                if platform_menus:
                    platform_menus.insert(0, caption_menu)
                    sub_menus += platform_menus
                    sub_menus.append(Menu())
    write_menu('programmers', sub_menus)


def create_serials_menu():
    sub_menus = []
    serial_ports = pyarduino.base.serial_port.list_serial_ports()
    for serial_port in serial_ports:
        menu_dict = {}
        menu_dict['caption'] = serial_port
        menu_dict['command'] = 'select_serial_port'
        menu_dict['args'] = {'serial_port': serial_port}
        menu_dict['checkbox'] = True
        menu = Menu(menu_dict)
        sub_menus.append(menu)
    write_menu('serials', sub_menus)


def create_languages_menu():
    sub_menus = []
    i18n = st_base.get_i18n()
    lang_ids = i18n.get_lang_ids()
    for lang_id in lang_ids:
        lang_names = i18n.get_lang_names(lang_id)
        caption = '%s (%s)' % (lang_names[0], lang_names[1])
        menu_dict = {}
        menu_dict['caption'] = caption
        menu_dict['command'] = 'select_language'
        menu_dict['args'] = {'lang_id': lang_id}
        menu_dict['checkbox'] = True
        menu = Menu(menu_dict)
        sub_menus.append(menu)
    write_menu('languages', sub_menus)
