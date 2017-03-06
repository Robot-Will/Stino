#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import glob
from . import c_file


def list_files_of_extension(dir_path, ext='', mode='recursion'):
    """."""
    paths = []
    if mode == 'recursion':
        sub_file_paths = glob.glob(dir_path + '/*')
        sub_dir_paths = [p for p in sub_file_paths if os.path.isdir(p)]
        for sub_dir_path in sub_dir_paths:
            paths += list_files_of_extension(sub_dir_path, ext, 'recursion')
    paths += glob.glob(dir_path + '/*' + ext)
    return paths


def list_files_of_extensions(dir_path, exts, mode='recursion'):
    """."""
    paths = []
    for ext in exts:
        paths += list_files_of_extension(dir_path, ext, mode)
    return paths


def get_file_info_of_extension(dir_path, ext='', mode='recursion'):
    """."""
    info = {}
    if mode == 'recursion':
        sub_file_paths = glob.glob(dir_path + '/*')
        sub_dir_paths = [p for p in sub_file_paths if os.path.isdir(p)]
        for sub_dir_path in sub_dir_paths:
            sub_info = get_file_info_of_extension(sub_dir_path, ext,
                                                  'recursion')
            info.update(sub_info)

    paths = glob.glob(dir_path + '/*' + ext)
    for path in paths:
        name = os.path.basename(path)
        info[name] = dir_path
    return info


def get_file_info_of_extensions(dir_path, exts, mode='recursion'):
    """."""
    info = {}
    for ext in exts:
        info.update(get_file_info_of_extension(dir_path, ext, mode))
    return info


def combine_ino_files(ino_file_paths, build_dir_path):
    """."""
    main_file_path = ino_file_paths[0]
    main_file_name = os.path.basename(main_file_path)
    prj_path = os.path.dirname(main_file_path)
    prj_name = os.path.basename(prj_path)
    target_file_name = main_file_name + '.cpp'
    target_dir_path = os.path.join(build_dir_path, prj_name)
    if not os.path.isdir(target_dir_path):
        os.makedirs(target_dir_path)
    target_file_path = os.path.join(target_dir_path, target_file_name)
    return target_file_path


class CProject(object):
    """."""

    def __init__(self, project_path):
        """."""
        self._path = project_path
        self._name = os.path.basename(project_path)

        self._is_cpp_project = False
        self._is_arduino_project = self.check_if_arduino_project()
        if not self._is_arduino_project:
            self._is_cpp_project = self.check_if_c_project()

    def check_if_arduino_project(self):
        """."""
        has_main_file = False
        self._ino_file_paths = list_files_of_extensions(self._path,
                                                        c_file.INO_EXTS)
        for ext in c_file.INO_EXTS:
            main_file_name = self._name + ext
            main_file_path = os.path.join(self._path, main_file_name)
            if os.path.isfile(main_file_path):
                if c_file.is_main_ino_file(main_file_path):
                    has_main_file = True
                    self._ino_file_paths.remove(main_file_path)
                    break
        if not has_main_file:
            for ino_file_path in self._ino_file_paths:
                if c_file.is_main_ino_file(ino_file_path):
                    has_main_file = True
                    main_file_path = ino_file_path
                    self._ino_file_paths.remove(main_file_path)
                    break
        if has_main_file:
            self._ino_file_paths = [main_file_path] + self._ino_file_paths
        return has_main_file

    def check_if_c_project(self):
        """."""
        has_main_file = False
        self._cpp_file_paths = list_files_of_extensions(self._path,
                                                        c_file.INOC_EXTS)
        for ext in c_file.CPP_EXTS:
            main_file_name = self._name + ext
            main_file_path = os.path.join(self._path, main_file_name)
            if os.path.isfile(main_file_path):
                if c_file.is_main_cpp_file(main_file_path):
                    has_main_file = True
                    self._cpp_file_paths.remove(main_file_path)
                    break
        if not has_main_file:
            for cpp_file_path in self._cpp_file_paths:
                if c_file.is_main_cpp_file(cpp_file_path):
                    main_file_path = cpp_file_path
                    self._cpp_file_paths.remove(main_file_path)
                    break
        if has_main_file:
            self._cpp_file_paths = [main_file_path] + self._cpp_file_paths
        return has_main_file

    def is_arduino_project(self):
        """."""
        return self._is_arduino_project

    def is_cpp_project(self):
        """."""
        return self._is_cpp_project

    def get_main_file(self, build_dir_path):
        """."""
        main_file_path = ''
        if self.is_arduino_project():
            path = combine_ino_files(self._ino_file_paths, build_dir_path)
            main_file_path = path
        elif self.is_c_project():
            main_file_path = self._cpp_file_paths[0]
        return main_file_path
