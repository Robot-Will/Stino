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
import threading
import subprocess
import re
import time

from . import base
from . import arduino_info
from . import arduino_target_params
from . import arduino_project
from . import arduino_src


class Compiler(object):
    def __init__(self, path, console=None):
        self.need_to_build = True
        self.message_queue = base.message_queue.MessageQueue(console)

        target_params_info = arduino_target_params.TargetParamsInfo()
        self.params = target_params_info.get_params()
        self.arduino_info = arduino_info.get_arduino_info()

        self.project = arduino_project.Project(path)
        project_name = self.project.get_name()

        build_path = get_build_path()
        build_path = os.path.join(build_path, project_name)
        self.set_build_path(build_path)

        self.done_build = False
        self.error_occured = False

        self.settings = base.settings.get_arduino_settings()
        self.bare_gcc = self.settings.get('bare_gcc', False)
        self.is_big_project = self.settings.get('big_project', False)

    def set_build_path(self, build_path):
        self.build_path = build_path
        if not os.path.isdir(self.build_path):
            os.makedirs(self.build_path)

    def build(self):
        self.message_queue.start_print()
        build_thread = threading.Thread(target=self.start_build)
        build_thread.start()

    def start_build(self):
        start_time = time.time()
        self.check_new_build()
        self.prepare_project_src_files()
        if self.need_to_build:
            project_name = self.project.get_name()
            self.message_queue.put('[Start building "{0}"...]\n', project_name)
            self.prepare_core_src_files()
            self.prepare_params()
            self.prepare_cmds()
            self.exec_build_cmds()
            if not self.error_occured:
                self.show_size_info()
                end_time = time.time()
                diff_time = end_time - start_time
                diff_time = '%.1f' % diff_time
                self.message_queue.put('[Done build "{0}" in {1}s.]\n',
                                       project_name, diff_time)
        else:
            self.error_occured = True
        self.done_build = True
        time.sleep(20)
        self.message_queue.stop_print()

    def check_new_build(self):
        self.is_new_build = False
        ide_path = self.arduino_info.get_ide_dir().get_path()
        sketchbook_path = self.arduino_info.get_sketchbook_dir().get_path()
        target_board = \
            self.arduino_info.get_target_board_info().get_target_board()
        target_board_id = target_board.get_id()
        target_sub_boards = \
            self.arduino_info.get_target_board_info().get_target_sub_boards()
        target_sub_board_ids = [sb.get_id() for sb in target_sub_boards]

        last_build_path = os.path.join(self.build_path, 'last_build.txt')
        last_build_file = base.settings.Settings(last_build_path)
        last_bare_gcc = last_build_file.get('bare_gcc')
        last_big_project = last_build_file.get('big_project')
        last_ide_path = last_build_file.get('ide_path')
        last_sketchbook_path = last_build_file.get('sketchbook_path')
        last_board_id = last_build_file.get('board_id')
        last_sub_board_ids = last_build_file.get('sub_board_ids')

        full_compilation = self.settings.get('full_compilation', False)
        bare_gcc = self.settings.get('bare_gcc', False)
        big_project = self.settings.get('big_project', False)

        if full_compilation or ide_path != last_ide_path or \
                sketchbook_path != last_sketchbook_path or \
                target_board_id != last_board_id or \
                target_sub_board_ids != last_sub_board_ids or \
                bare_gcc != last_bare_gcc or big_project != last_big_project:
            last_build_file.set('ide_path', ide_path)
            last_build_file.set('sketchbook_path', sketchbook_path)
            last_build_file.set('board_id', target_board_id)
            last_build_file.set('sub_board_ids', target_sub_board_ids)
            last_build_file.set('bare_gcc', bare_gcc)
            last_build_file.set('big_project', big_project)
            self.is_new_build = True

    def prepare_project_src_files(self):
        self.project_src_changed = False
        self.project_cpp_obj_pairs = []
        self.project_obj_paths = []

        ino_files = self.project.list_ino_files()
        if ino_files and not self.bare_gcc:
            combined_file_name = self.project.get_name() + '.ino.cpp'
            combined_file_path = os.path.join(
                self.build_path, combined_file_name)
            combined_file = base.abs_file.File(combined_file_path)
            combined_obj_path = combined_file_path + '.o'
            self.project_obj_paths.append(combined_obj_path)

            ino_changed = check_ino_change(ino_files, combined_file)
            if self.is_new_build or ino_changed:
                combined_src = arduino_src.combine_ino_files(ino_files)
                combined_file.write(combined_src)
                cpp_obj_pair = (combined_file_path, combined_obj_path)

                self.project_cpp_obj_pairs.append(cpp_obj_pair)

        sub_dir_name = self.project.get_name()
        cpp_files = self.project.list_cpp_files(self.is_big_project)
        self.project_obj_paths += gen_obj_paths(
            self.project.get_path(), self.build_path, sub_dir_name, cpp_files)
        cpp_obj_pairs = gen_cpp_obj_pairs(self.project.get_path(),
                                          self.build_path, sub_dir_name,
                                          cpp_files, self.is_new_build)
        self.project_cpp_obj_pairs += cpp_obj_pairs

        if self.project_cpp_obj_pairs:
            self.project_src_changed = True
        self.need_to_build = bool(self.project_obj_paths)

    def prepare_lib_src_files(self):
        ino_files = []
        if not self.bare_gcc:
            ino_files = self.project.list_ino_files()
        cpp_files = self.project.list_cpp_files(self.is_big_project)
        h_files = self.project.list_h_files(self.is_big_project)
        src_files = ino_files + cpp_files + h_files
        self.libraries = arduino_src.list_libraries(
            src_files, self.arduino_info)

    def prepare_core_src_files(self):
        self.core_obj_paths = []
        self.core_cpp_obj_pairs = []
        self.core_src_changed = False

        self.prepare_lib_src_files()
        target_arch = \
            self.arduino_info.get_target_board_info().get_target_arch()
        for library in self.libraries:
            library_path = library.get_path()
            library_name = library.get_name()
            sub_dir_name = 'lib_' + library_name
            lib_cpp_files = library.list_cpp_files(target_arch)
            lib_obj_paths = gen_obj_paths(library_path, self.build_path,
                                          sub_dir_name, lib_cpp_files)
            lib_cpp_obj_pairs = gen_cpp_obj_pairs(
                library_path, self.build_path, sub_dir_name, lib_cpp_files,
                self.is_new_build)
            self.core_obj_paths += lib_obj_paths
            self.core_cpp_obj_pairs += lib_cpp_obj_pairs

        if not self.bare_gcc:
            core_path = self.params.get('build_core_path')
            core_dir = base.abs_file.Dir(core_path)
            core_cpp_files = core_dir.recursive_list_files(
                arduino_src.CPP_EXTS)
            sub_dir_name = 'core_' + core_dir.get_name()
            core_obj_paths = gen_obj_paths(core_path, self.build_path,
                                           sub_dir_name, core_cpp_files)
            core_cpp_obj_pairs = gen_cpp_obj_pairs(
                core_path, self.build_path, sub_dir_name, core_cpp_files,
                self.is_new_build)
            self.core_obj_paths += core_obj_paths
            self.core_cpp_obj_pairs += core_cpp_obj_pairs

            varient_path = self.params.get('build_variant_path')
            varient_dir = base.abs_file.Dir(varient_path)
            varient_cpp_files = varient_dir.recursive_list_files(
                arduino_src.CPP_EXTS)
            sub_dir_name = 'varient_' + varient_dir.get_name()
            varient_obj_paths = gen_obj_paths(varient_path, self.build_path,
                                              sub_dir_name, varient_cpp_files)
            varient_cpp_obj_pairs = gen_cpp_obj_pairs(
                varient_path, self.build_path, sub_dir_name,
                varient_cpp_files, self.is_new_build)
            self.core_obj_paths += varient_obj_paths
            self.core_cpp_obj_pairs += varient_cpp_obj_pairs

        if self.core_cpp_obj_pairs:
            self.core_src_changed = True

    def prepare_params(self):
        self.archive_file_name = 'core.a'
        self.params['build.path'] = self.build_path
        self.params['build.project_name'] = self.project.get_name()
        self.params['archive_file'] = self.archive_file_name

        extra_flag = ' ' + self.settings.get('extra_flag', '')
        c_flags = self.params.get('compiler.c.flags', '') + extra_flag
        cpp_flags = self.params.get('compiler.cpp.flags', '') + extra_flag
        S_flags = self.params.get('compiler.S.flags', '') + extra_flag
        self.params['compiler.c.flags'] = c_flags
        self.params['compiler.cpp.flags'] = cpp_flags
        self.params['compiler.S.flags'] = S_flags

        project_path = self.project.get_path()
        core_path = self.params.get('build_core_path')
        varient_path = self.params.get('build_variant_path')
        include_paths = [project_path, core_path, varient_path]

        target_arch = \
            self.arduino_info.get_target_board_info().get_target_arch()
        for lib in self.libraries:
            src_dirs = lib.list_src_dirs(target_arch)
            include_paths += [d.get_path() for d in src_dirs]

        includes = ['"-I%s"' % path for path in include_paths]
        self.params['includes'] = ' '.join(includes)

        ide_path = self.arduino_info.get_ide_dir().get_path()
        if not 'compiler.path' in self.params:
            compiler_path = '{runtime.ide.path}/hardware/tools/avr/bin/'
            self.params['compiler.path'] = compiler_path
        compiler_path = self.params.get('compiler.path')
        compiler_path = compiler_path.replace('{runtime.ide.path}', ide_path)
        if not os.path.isdir(compiler_path):
            self.params['compiler.path'] = ''

        self.params = arduino_target_params.replace_param_values(self.params)

    def prepare_cmds(self):
        compile_c_cmd = self.params.get('recipe.c.o.pattern', '')
        compile_cpp_cmd = self.params.get('recipe.cpp.o.pattern', '')
        compile_asm_cmd = self.params.get('recipe.S.o.pattern', '')
        ar_cmd = self.params.get('recipe.ar.pattern', '')
        combine_cmd = self.params.get('recipe.c.combine.pattern', '')
        eep_cmd = self.params.get('recipe.objcopy.eep.pattern', '')
        hex_cmd = self.params.get('recipe.objcopy.hex.pattern', '')

        self.build_files = []
        self.file_cmds_dict = {}
        for cpp_path, obj_path in (self.project_cpp_obj_pairs +
                                   self.core_cpp_obj_pairs):
            cmd = compile_cpp_cmd
            ext = os.path.splitext(cpp_path)[1]
            if ext == '.c':
                cmd = compile_c_cmd
            elif ext == '.S':
                cmd = compile_asm_cmd
            cmd = cmd.replace('{source_file}', cpp_path)
            cmd = cmd.replace('{object_file}', obj_path)
            self.build_files.append(obj_path)
            self.file_cmds_dict[obj_path] = [cmd]

        core_changed = False
        core_archive_path = os.path.join(self.build_path,
                                         self.archive_file_name)
        if self.core_src_changed and os.path.isfile(core_archive_path):
            os.remove(core_archive_path)
        if not os.path.isfile(core_archive_path):
            core_changed = True
            cmds = []
            for obj_path in self.core_obj_paths:
                cmd = ar_cmd.replace('{object_file}', obj_path)
                cmds.append(cmd)
            self.build_files.append(core_archive_path)
            self.file_cmds_dict[core_archive_path] = cmds

        if self.project_src_changed or core_changed:
            obj_paths = ' '.join(self.project_obj_paths)
            cmd = combine_cmd.replace('{object_files}', obj_paths)
            if not self.core_obj_paths:
                core_archive_path = \
                    self.build_path + '/' + self.archive_file_name
                text = '"' + core_archive_path + '"'
                cmd = cmd.replace(text, '')
            elf_file_path = self.project.get_name() + '.elf'
            self.build_files.append(elf_file_path)
            self.file_cmds_dict[elf_file_path] = [cmd]

            if eep_cmd:
                eep_file_path = self.project.get_name() + '.eep'
                self.build_files.append(eep_file_path)
                self.file_cmds_dict[eep_file_path] = [eep_cmd]

            hex_file_path = self.project.get_name() + '.hex'
            self.build_files.append(hex_file_path)
            self.file_cmds_dict[hex_file_path] = [hex_cmd]

    def exec_build_cmds(self):
        show_compilation_output = self.settings.get('build_verbose', False)

        self.working_dir = self.arduino_info.get_ide_dir().get_path()
        error_occured = False
        for build_file in self.build_files:
            self.message_queue.put('Creating {0}...\n', build_file)
            cmds = self.file_cmds_dict.get(build_file)
            error_occured = exec_cmds(self.working_dir, cmds,
                                      self.message_queue,
                                      show_compilation_output)
            if error_occured:
                self.error_occured = True
                break

    def show_size_info(self):
        size_cmd = self.params.get('recipe.size.pattern', '')
        return_code, stdout, stderr = exec_cmd(self.working_dir, size_cmd)
        if stderr:
            self.message_queue.put(stderr + '\n')
        self.print_size(stdout)

    def print_size(self, text):
        size_total = int(self.params.get('upload.maximum_size'))
        size_data_total = int(self.params.get('upload.maximum_data_size'))

        size_regex = self.params.get('recipe.size.regex')
        pattern = re.compile(size_regex, re.M)
        size = sum(int(n) for n in pattern.findall(text))
        size_percent = size / size_total * 100

        size = regular_numner(size)
        size_total = regular_numner(size_total)
        size_percent = '%.1f' % size_percent
        txt = 'Sketch uses {0} bytes ({1}%) '
        txt += 'of program storage space. Maximum is {2} bytes.\n'
        self.message_queue.put(txt, size, size_percent, size_total)

        size_regex_data = self.params.get('recipe.size.regex.data', '')
        if size_regex_data and size_data_total:
            pattern = re.compile(size_regex_data, re.M)
            size_data = sum(int(n) for n in pattern.findall(text))
            size_data_percent = size_data / size_data_total * 100
            size_data_remain = size_data_total - size_data

            size_data = regular_numner(size_data)
            size_data_remain = regular_numner(size_data_remain)
            size_data_total = regular_numner(size_data_total)
            size_data_percent = '%.1f' % size_data_percent
            txt = 'Global variables use {0} bytes ({1}%) of dynamic memory, '
            txt += 'leaving {2} bytes for local variables. '
            txt += 'Maximum is {3} bytes.\n'
            self.message_queue.put(txt, size_data, size_data_percent,
                                   size_data_remain, size_data_total)

    def is_finished(self):
        return self.done_build

    def has_error(self):
        return self.error_occured

    def get_params(self):
        return self.params

    def get_ide_path(self):
        return self.arduino_info.get_ide_dir().get_path()


def get_build_path():
    settings = base.settings.get_arduino_settings()
    build_path = settings.get('build_path', '')
    if not build_path:
        doc_path = base.sys_path.get_document_path()
        build_path = os.path.join(doc_path, 'Arduino_build')
    if not os.path.isdir(build_path):
        os.makedirs(build_path)
    return build_path


def check_ino_change(ino_files, combined_file):
    ino_changed = False
    combined_file_path = combined_file.get_path()
    obj_path = combined_file_path + '.o'
    obj_file = base.abs_file.File(obj_path)
    for ino_file in ino_files:
        if ino_file.get_mtime() > obj_file.get_mtime():
            ino_changed = True
            break
    return ino_changed


def gen_cpp_obj_pairs(src_path, build_path, sub_dir,
                      cpp_files, new_build=False):
    obj_paths = gen_obj_paths(src_path, build_path, sub_dir, cpp_files)
    obj_files = [base.abs_file.File(path) for path in obj_paths]

    path_pairs = []
    for cpp_file, obj_file in zip(cpp_files, obj_files):
        if new_build or cpp_file.get_mtime() > obj_file.get_mtime():
            path_pair = (cpp_file.get_path(), obj_file.get_path())
            path_pairs.append(path_pair)
    return path_pairs


def gen_obj_paths(src_path, build_path, sub_dir, cpp_files):
    obj_paths = []
    build_path = os.path.join(build_path, sub_dir)
    for cpp_file in cpp_files:
        cpp_file_path = cpp_file.get_path()
        sub_path = cpp_file_path.replace(src_path, '')[1:] + '.o'
        obj_path = os.path.join(build_path, sub_path)
        obj_paths.append(obj_path)

        obj_dir_name = os.path.dirname(obj_path)
        if not os.path.isdir(obj_dir_name):
            os.makedirs(obj_dir_name)
    return obj_paths


def exec_cmds(working_dir, cmds, message_queue, is_verbose=False):
    error_occured = False
    for cmd in cmds:
        return_code, stdout, stderr = exec_cmd(working_dir, cmd)
        if is_verbose:
            message_queue.put(cmd + '\n')
            if stdout:
                message_queue.put(stdout + '\n')
        if stderr:
            message_queue.put(stderr + '\n')
        if return_code != 0:
            message_queue.put('[Exit with error code {0}]\n', return_code)
            error_occured = True
            break
    return error_occured


def exec_cmd(working_dir, cmd):
    if cmd:
        os.chdir(working_dir)
        cmd = formatCommand(cmd)
        compile_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=True)
        result = compile_proc.communicate()
        return_code = compile_proc.returncode
        stdout = result[0].decode(base.sys_info.get_sys_encoding())
        stderr = result[1].decode(base.sys_info.get_sys_encoding())
    else:
        return_code = -1
        stdout = ''
        stderr = ''
    return (return_code, stdout, stderr)


def formatCommand(cmd):
    cmd = cmd.replace('\\', '/')
    os_name = base.sys_info.get_os_name()
    python_version = base.sys_info.get_python_version()
    if python_version < 3 and os_name == 'windows':
        cmd = '"%s"' % cmd
    return cmd


def regular_numner(num):
    txt = str(num)
    regular_num = ''
    for index, char in enumerate(txt[::-1]):
        regular_num += char
        if (index + 1) % 3 == 0 and index + 1 != len(txt):
            regular_num += ','
    regular_num = regular_num[::-1]
    return regular_num
