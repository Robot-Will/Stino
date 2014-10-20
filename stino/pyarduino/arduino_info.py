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

from . import base
from . import arduino_root
from . import arduino_target_board
from . import arduino_target_programmer


@base.deco.singleton
class ArduinoInfo(object):
    def __init__(self):
        self.settings = base.settings.get_arduino_settings()
        ide_path = arduino_root.get_arduino_ide_path()
        sketchbook_path = arduino_root.get_sketchbook_path()
        self.ide_dir = arduino_root.ArduinoIdeDir(
            arduino_root.update_ide_path(ide_path))
        self.sketchbook_dir = arduino_root.SketchbookDir(sketchbook_path)

        root_dirs = [self.ide_dir, self.sketchbook_dir]
        self.target_board_info = arduino_target_board.TargetBoardInfo(
            root_dirs)
        self.target_programmer_info = \
            arduino_target_programmer.TargetProgrammerInfo(root_dirs)
        self.load_libraries()

    def update(self):
        self.target_board_info.update([self.ide_dir, self.sketchbook_dir])
        self.target_programmer_info.update([self.ide_dir, self.sketchbook_dir])
        self.load_libraries()

    def update_h_lib_dict(self, library):
        h_files = library.list_h_files()
        h_file_names = [f.get_name() for f in h_files]
        for h_file_name in h_file_names:
            self.h_lib_dict[h_file_name] = library

    def load_libraries(self):
        self.h_lib_dict = {}
        target_arch = self.target_board_info.get_target_arch()
        for root in [self.ide_dir, self.sketchbook_dir]:
            libraries = root.get_libraries()
            for library in libraries:
                arch = library.get_arch()
                if arch == '*' or arch == target_arch:
                    self.update_h_lib_dict(library)
            for package in root.get_packages():
                for platform in package.get_platforms():
                    if platform.get_arch() == target_arch:
                        libraries = platform.get_libraries()
                        for library in libraries:
                            self.update_h_lib_dict(library)

    def get_ide_dir(self):
        return self.ide_dir

    def get_sketchbook_dir(self):
        return self.sketchbook_dir

    def get_root_dirs(self):
        return [self.ide_dir, self.sketchbook_dir]

    def get_target_board_info(self):
        return self.target_board_info

    def get_target_programmer_info(self):
        return self.target_programmer_info

    def get_h_lib_dict(self):
        return self.h_lib_dict

    def change_board(self, board_id):
        self.target_board_info.change_target_board(board_id)
        self.load_libraries()

    def change_sub_board(self, option_index, board_id):
        self.target_board_info.change_target_sub_board(option_index, board_id)

    def change_programmer(self, programmer_id):
        self.target_programmer_info.change_target_programmer(programmer_id)

    def change_ide_path(self, ide_path):
        path = arduino_root.update_ide_path(ide_path)
        if path != self.ide_dir.get_path():
            if arduino_root.is_arduino_ide_path(path):
                self.settings.set('arduino_ide_path', ide_path)
                self.ide_dir = arduino_root.ArduinoIdeDir(path)
                self.update()

    def change_sketchbook_path(self, sketchbook_path):
        if sketchbook_path != self.sketchbook_dir.get_path():
            self.settings.set('sketchbook_path', sketchbook_path)
            self.sketchbook_dir = arduino_root.SketchbookDir(sketchbook_path)
            self.update()


def get_arduino_info():
    arduino_info = ArduinoInfo()
    return arduino_info
