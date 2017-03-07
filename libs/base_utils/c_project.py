#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import glob
import codecs
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


def get_file_info_of_extension(dir_path, ext='',
                               mode='recursion', excludes=[]):
    """."""
    info = {}
    if mode == 'recursion':
        sub_file_paths = glob.glob(dir_path + '/*')
        sub_dir_paths = [p for p in sub_file_paths if os.path.isdir(p)]
        for sub_dir_path in sub_dir_paths:
            dir_name = os.path.basename(sub_dir_path)
            if dir_name not in excludes:
                sub_info = get_file_info_of_extension(sub_dir_path, ext,
                                                      'recursion', excludes)
                info.update(sub_info)

    paths = glob.glob(dir_path + '/*' + ext)
    for path in paths:
        name = os.path.basename(path)
        info[name] = dir_path
    return info


def get_file_info_of_extensions(dir_path, exts, mode='recursion', excludes=[]):
    """."""
    info = {}
    for ext in exts:
        info.update(get_file_info_of_extension(dir_path, ext, mode, excludes))
    return info


def combine_ino_files(ino_file_paths, build_path):
    """."""
    main_file_path = ino_file_paths[0]
    main_file_name = os.path.basename(main_file_path)
    target_file_name = main_file_name + '.cpp'
    target_file_path = os.path.join(build_path, target_file_name)

    func_prototypes = []
    for ino_file_path in ino_file_paths:
        ino_file = c_file.CFile(ino_file_path)
        prototypes = ino_file.get_undeclar_func_defs()
        for prototype in prototypes:
            if prototype not in func_prototypes:
                func_prototypes.append(prototype)

    with codecs.open(main_file_path, 'r', 'utf-8') as source_f:
        src_text = source_f.read()
        index = c_file.get_index_of_first_statement(src_text)
        header_text = src_text[:index]
        footer_text = src_text[index:]

    with codecs.open(target_file_path, 'w', 'utf-8') as target_f:
        cur_path = main_file_path.replace('\\', '/')
        footer_start_line = len(header_text.split('\n')) + 1
        text = '#line 1 "%s"\n' % cur_path
        text += header_text
        text += '\n#include <Arduino.h>\n'
        if func_prototypes:
            text += ';\n'.join(func_prototypes)
            text += ';\n\n'
        text += '#line %d "%s"\n' % (footer_start_line, cur_path)
        text += footer_text
        target_f.write(text)

        for ino_file_path in ino_file_paths[1:]:
            first_line = '#line 1 "%s"\n' % ino_file_path.replace('\\', '/')
            target_f.write(first_line)
            with codecs.open(target_file_path, 'r', 'utf-8') as source_f:
                target_f.write(source_f.read())
    return target_file_path


def check_main_file(file_paths, prj_type='arduino'):
    """."""
    has_main_file = False

    if prj_type == 'arduino':
        is_main_file = c_file.is_main_ino_file
    else:
        is_main_file = c_file.is_main_cpp_file

    for file_path in file_paths:
        if is_main_file(file_path):
            has_main_file = True
            main_file_path = file_path
            file_paths.remove(main_file_path)
            break
    if has_main_file:
        file_paths = [main_file_path] + file_paths
    return has_main_file, file_paths


class CProject(object):
    """."""

    def __init__(self, project_path, build_dir_path):
        """."""
        self._path = project_path
        self._name = os.path.basename(project_path)
        self.set_build_path(build_dir_path)

        self._src_file_paths = list_files_of_extensions(self._path,
                                                        c_file.INOC_EXTS)

        self._is_cpp_project = False
        self._is_arduino_project = self.check_is_arduino_project()
        if not self._is_arduino_project:
            self._is_cpp_project = self.check_is_c_project()

    def get_name(self):
        """."""
        return self._name

    def get_path(self):
        """."""
        return self._path

    def set_build_path(self, build_dir_path):
        """."""
        self._build_path = os.path.join(build_dir_path, self._name)
        if not os.path.isdir(self._build_path):
            os.makedirs(self._build_path)

    def check_is_arduino_project(self):
        """."""
        has_main_file, self._src_file_paths = \
            check_main_file(self._src_file_paths)
        return has_main_file

    def check_is_c_project(self):
        """."""
        has_main_file, self._src_file_paths = \
            check_main_file(self._src_file_paths, 'cpp')
        return has_main_file

    def is_arduino_project(self):
        """."""
        return self._is_arduino_project

    def is_cpp_project(self):
        """."""
        return self._is_cpp_project

    def get_main_file(self):
        """."""
        main_file_path = ''
        if self.is_arduino_project() or self.is_cpp_project():
            main_file_path = self._src_file_paths[0]
            if self.is_arduino_project():
                ext = os.path.splitext(main_file_path)[1]
                if ext in c_file.INO_EXTS:
                    ino_file_paths = \
                        list_files_of_extensions(self._path, c_file.INO_EXTS)
                    ino_file_paths.remove(main_file_path)
                    ino_file_paths = [main_file_path] + ino_file_paths
                    path = combine_ino_files(ino_file_paths, self._build_path)
                    main_file_path = path
        return main_file_path
