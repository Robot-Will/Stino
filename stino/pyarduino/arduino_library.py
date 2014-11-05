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
from . import arduino_sketchbook
from . import arduino_params_file
from . import arduino_keyword
from . import arduino_src


class LibrarySet(base.abs_file.Dir):
    def __init__(self, parent_id, path):
        super(LibrarySet, self).__init__(path)
        self.id = parent_id
        self.library_ids = []
        self.libraries = []
        self.id_library_dict = {}
        self.load_libraries()

    def get_library_ids(self):
        return self.library_ids

    def get_libraries(self):
        return self.libraries

    def get_library(self, library_id):
        return self.id_library_dict.get(library_id, None)

    def load_libraries(self):
        sub_dirs = self.list_dirs()
        self.libraries = [Library(d.path) for d in sub_dirs]
        self.libraries = [lib for lib in self.libraries if lib.is_library()]
        self.library_ids = [lib.name for lib in self.libraries]
        self.id_library_dict = dict(zip(self.library_ids, self.libraries))


class Library(base.abs_file.Dir):
    def __init__(self, path):
        super(Library, self).__init__(path)
        self.src_path = os.path.join(self.path, 'src')
        if not os.path.isdir(self.src_path):
            self.src_path = self.path
        self.src_dir = base.abs_file.Dir(self.src_path)

        examples_path = os.path.join(self.path, 'examples')
        self.example_set = arduino_sketchbook.Sketchbook(examples_path)
        self.example_set.name = self.name

        self.property_dict = {}
        self.load_properties()
        self.load_keywords()

        self.arch = self.property_dict.get('architectures', '')
        if ',' in self.arch:
            self.arch = '*'
        if not self.arch:
            self.arch = '*'

    def get_arch(self):
        return self.arch

    def get_examples(self):
        return self.example_set

    def get_property_dict(self):
        return self.property_dict

    def get_property(self, property_id):
        return self.property_dict.get(property_id, None)

    def get_keywords(self):
        return self.keywords_file.get_keywords()

    def get_keyword_ids(self):
        return self.keywords_file.get_keyword_ids()

    def get_id_keyword_dict(self):
        return self.keywords_file.get_id_keyword_dict()

    def load_keywords(self):
        keywords_file_path = os.path.join(self.path, 'keywords.txt')
        self.keywords_file = arduino_keyword.KeywordsFile(keywords_file_path)

    def load_properties(self):
        properties_file_path = os.path.join(self.path, 'library.properties')
        properties_file = arduino_params_file.ParamsFile(properties_file_path)
        self.property_dict = properties_file.get_params()

    def list_src_dirs(self, target_arch='avr'):
        src_dirs = [self.src_dir]
        arch_path = os.path.join(self.src_path, target_arch)
        if os.path.isdir(arch_path):
            arch_dir = base.abs_file.Dir(arch_path)
            src_dirs.append(arch_dir)

        utility_dirs = []
        for src_dir in src_dirs:
            utility_path = os.path.join(src_dir.get_path(), 'utility')
            if os.path.isdir(utility_path):
                utility_dir = base.abs_file.Dir(utility_path)
                utility_dirs.append(utility_dir)
        src_dirs += utility_dirs
        return src_dirs

    def list_files(self, EXTS, target_arch='avr'):
        files = []
        src_dirs = self.list_src_dirs(target_arch)
        for src_dir in src_dirs:
            files += src_dir.list_files_of_extensions(EXTS)
        return files

    def list_h_files(self, target_arch='avr'):
        return self.list_files(arduino_src.H_EXTS, target_arch)

    def list_cpp_files(self, target_arch='avr'):
        return self.list_files(arduino_src.CPP_EXTS, target_arch)

    def is_library(self):
        h_files = self.list_h_files()
        return bool(h_files)
