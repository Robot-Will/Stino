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
from . import file
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


def combine_ino_files(ino_file_paths, target_file_path):
    """."""
    need_combine = False

    build_path = os.path.dirname(target_file_path)
    last_inos_path = os.path.join(build_path,
                                  'last_inos.stino-settings')
    last_inos_info = file.SettingsFile(last_inos_path)
    f_paths = [p.replace('\\', '/') for p in ino_file_paths]

    if f_paths:
        if not os.path.isfile(target_file_path):
            need_combine = True
        else:
            for ino_file_path in f_paths:
                mtime = os.path.getmtime(ino_file_path)
                last_mtime = last_inos_info.get(ino_file_path)
                if mtime and mtime != last_mtime:
                    last_inos_info.set(ino_file_path, mtime)
                    need_combine = True

        if need_combine:
            func_prototypes = []
            for ino_file_path in f_paths:
                ino_file = c_file.CFile(ino_file_path)
                prototypes = ino_file.get_undeclar_func_defs()
                for prototype in prototypes:
                    if prototype not in func_prototypes:
                        func_prototypes.append(prototype)

            with codecs.open(f_paths[0], 'r', 'utf-8') as source_f:
                src_text = source_f.read()
                index = c_file.get_index_of_first_statement(src_text)
                header_text = src_text[:index]
                footer_text = src_text[index:]

            with codecs.open(target_file_path, 'w', 'utf-8') as target_f:
                cur_path = f_paths[0]
                footer_start_line = len(header_text.split('\n'))
                text = '#line 1 "%s"\n' % cur_path
                text += header_text
                text += '\n#include <Arduino.h>\n'
                if func_prototypes:
                    text += ';\n'.join(func_prototypes)
                    text += ';\n\n'
                text += '#line %d "%s"\n' % (footer_start_line, cur_path)
                text += footer_text
                target_f.write(text)

                for ino_file_path in f_paths[1:]:
                    first_line = '#line 1 "%s"\n' % ino_file_path
                    target_f.write(first_line)
                    with codecs.open(target_file_path,
                                     'r', 'utf-8') as source_f:
                        target_f.write(source_f.read())
    else:
        with codecs.open(target_file_path, 'w', 'utf-8') as target_f:
            text = '#include <Arduino.h>\n'
            target_f.write(text)


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
            break
    return has_main_file


class CProject(object):
    """."""

    def __init__(self, project_path, build_dir_path):
        """."""
        self._path = project_path
        self._name = os.path.basename(project_path)
        self.set_build_path(build_dir_path)

        self._ino_file_paths = list_files_of_extensions(self._path,
                                                        c_file.INO_EXTS)
        self._cpp_file_paths = list_files_of_extensions(self._path,
                                                        c_file.CC_EXTS)
        self._src_file_paths = self._ino_file_paths + self._cpp_file_paths

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

    def get_build_path(self):
        """."""
        return self._build_path

    def get_cpp_files(self):
        """."""
        return self._cpp_file_paths

    def set_build_path(self, build_dir_path):
        """."""
        self._build_path = os.path.join(build_dir_path, self._name)
        if not os.path.isdir(self._build_path):
            os.makedirs(self._build_path)

    def check_is_arduino_project(self):
        """."""
        has_main_file = check_main_file(self._src_file_paths)
        return has_main_file

    def check_is_c_project(self):
        """."""
        has_main_file = check_main_file(self._src_file_paths, 'cpp')
        return has_main_file

    def is_arduino_project(self):
        """."""
        return self._is_arduino_project

    def is_cpp_project(self):
        """."""
        return self._is_cpp_project

    def gen_arduino_tmp_file(self):
        """."""
        tmp_cpp_name = self._name + '.ino.cpp'
        tmp_file_path = os.path.join(self._build_path, tmp_cpp_name)
        combine_ino_files(self._ino_file_paths, tmp_file_path)
