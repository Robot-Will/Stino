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
from . import arduino_package
from . import arduino_sketchbook
from . import arduino_library
from . import arduino_keyword


class ArduinoRootDir(base.abs_file.Dir):
    def __init__(self, path, dir_id='root_dir'):
        super(ArduinoRootDir, self).__init__(path)
        self.id = dir_id
        self.load()

    def load(self):
        self.load_packages()
        self.load_examples()
        self.load_libraries()

    def load_packages(self):
        self.packages = []
        hardware_path = os.path.join(self.path, 'hardware')
        hardware_dir = base.abs_file.Dir(hardware_path)
        dirs = hardware_dir.list_dirs()
        for cur_dir in dirs:
            if cur_dir.name.lower() == 'tools':
                continue
            package = arduino_package.Package(self.id, cur_dir.path)
            if package.is_package():
                self.packages.append(package)

    def load_examples(self):
        examples_path = os.path.join(self.path, 'examples')
        self.example_set = arduino_sketchbook.Sketchbook(examples_path)

    def load_libraries(self):
        libraries_path = os.path.join(self.path, 'libraries')
        self.library_set = arduino_library.LibrarySet(self.id, libraries_path)

    def get_id(self):
        return self.id

    def get_packages(self):
        return self.packages

    def get_libraries(self):
        return self.library_set.get_libraries()

    def get_examples(self):
        return self.example_set

    def get_library(self, library_id):
        return self.library_set.get_library(library_id)


class ArduinoIdeDir(ArduinoRootDir):
    def __init__(self, path):
        super(ArduinoIdeDir, self).__init__(path, 'ide')
        self.load_version()
        self.load_keywords()

    def reload(self):
        self.load()
        self.load_version()
        self.load_keywords()

    def load_version(self):
        lib_path = os.path.join(self.path, 'lib')
        version_file_path = os.path.join(lib_path, 'version.txt')
        version_file = base.abs_file.File(version_file_path)
        self.version_name = version_file.read().strip()
        if not self.version_name:
            self.version_name = 'Unknown'

        self.version = ''
        version_txt = self.version_name.replace('.', '')
        for char in version_txt:
            if not char in '0123456789':
                break
            self.version += char
        if not self.version:
            self.version = '000'

    def load_keywords(self):
        lib_path = os.path.join(self.path, 'lib')
        keywords_file_path = os.path.join(lib_path, 'keywords.txt')
        self.keywords_file = arduino_keyword.KeywordsFile(keywords_file_path)

    def get_version(self):
        return self.version

    def get_version_name(self):
        return self.version_name

    def get_keywords(self):
        return self.keywords_file.get_keywords()

    def get_keyword_ids(self):
        return self.keywords_file.get_keyword_ids()

    def get_id_keyword_dict(self):
        return self.keywords_file.get_id_keyword_dict()


class SketchbookDir(ArduinoRootDir):
    def __init__(self, path):
        super(SketchbookDir, self).__init__(path, 'sketchbook')
        self.ensure_existence()
        self.load_sketch()

    def reload(self):
        self.load()
        self.load_sketch()

    def load_sketch(self):
        self.sketch = arduino_sketchbook.Sketchbook(self.path)
        self.sketch.name = 'Sketchbook'

    def get_sketchbook(self):
        return self.sketch


def update_ide_path(path):
    if path and base.sys_info.get_os_name() == 'osx':
        path = os.path.join(path, 'Contents/Resources/Java')
        if not os.path.isdir(path):
            path = os.path.join(path, 'Contents/Java')
    return path


def is_arduino_ide_path(path):
    state = False
    hardware_path = os.path.join(path, 'hardware')
    lib_path = os.path.join(path, 'lib')
    version_file_path = os.path.join(lib_path, 'version.txt')
    if os.path.isdir(hardware_path) and os.path.isfile(version_file_path):
        state = True
    return state


def get_default_sketchbook_path():
    document_path = base.sys_path.get_document_path()
    sketchbook_path = os.path.join(document_path, 'Arduino')
    return sketchbook_path


def get_default_arduino_ide_path():
    path = ''
    os_name = base.sys_info.get_os_name()
    if os_name == 'linux':
        path = '/usr/share/arduino'
    elif os_name == 'osx':
        path = '/Applications/arduino.app'
    elif os_name == 'windows':
        path = r'c:\program files (x86)\arduino'
        if not os.path.isdir(path):
            path = r'c:\program files\arduino'
    if not is_arduino_ide_path(update_ide_path(path)):
        path = ''
    return path


def get_sketchbook_path():
    settings = base.settings.get_arduino_settings()
    sketchbook_path = settings.get('sketchbook_path', '')
    if not sketchbook_path:
        sketchbook_path = get_default_sketchbook_path()
        settings.set('sketchbook_path', sketchbook_path)
    return sketchbook_path


def get_arduino_ide_path():
    settings = base.settings.get_arduino_settings()
    arduino_ide_path = settings.get('arduino_ide_path', '')
    if not is_arduino_ide_path(update_ide_path(arduino_ide_path)):
        arduino_ide_path = get_default_arduino_ide_path()
        if arduino_ide_path:
            settings.set('arduino_ide_path', arduino_ide_path)
    return arduino_ide_path
