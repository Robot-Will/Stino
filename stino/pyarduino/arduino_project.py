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
from . import arduino_src


class Project(base.abs_file.Dir):
    def __init__(self, path):
        super(Project, self).__init__(path)
        primary_file_name = self.name + '.ino'
        primary_file_path = os.path.join(self.path, primary_file_name)
        self.primary_file = base.abs_file.File(primary_file_path)

    def list_ino_files(self):
        files = self.list_files_of_extensions(arduino_src.INO_EXTS)
        if files and self.primary_file.is_file():
            files = [f for f in files if f.name.lower() !=
                     self.primary_file.name.lower()]
            files.insert(0, self.primary_file)
        return files

    def list_cpp_files(self, is_big_project=False):
        if is_big_project:
            cpp_files = self.recursive_list_files(arduino_src.CPP_EXTS)
        else:
            cpp_files = self.list_files_of_extensions(arduino_src.CPP_EXTS)

        primary_file_path = self.primary_file.get_path()
        for cpp_file in cpp_files:
            cpp_file_path = cpp_file.get_path()
            if cpp_file_path.startswith(primary_file_path):
                cpp_files.remove(cpp_file)
                break
        return cpp_files

    def list_h_files(self, is_big_project=False):
        if is_big_project:
            files = files = self.recursive_list_files(arduino_src.H_EXTS)
        else:
            files = self.list_files_of_extensions(arduino_src.H_EXTS)
        return files
