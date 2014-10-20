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
import subprocess
import threading
import time

from . import sys_base
from . import file_base
from . import serial_base
from . import arduino_src

from .. import st_console


class Project(file_base.Dir):
    def __init__(self, path):
        super(Project, self).__init__(path)
        primary_file_name = self.name + '.ino'
        primary_file_path = os.path.join(self.path, primary_file_name)
        self.primary_file = file_base.File(primary_file_path)
        self.console = st_console.Console(self.name)

        build_path = sys_base.get_build_path()
        build_path = os.path.join(build_path, self.name)
        self.set_build_path(build_path)

    def set_build_path(self, build_path):
        self.build_path = build_path
        if not os.path.isdir(self.build_path):
            os.makedirs(self.build_path)
        combined_file_name = self.name + '.ino.cpp'
        combined_file_path = os.path.join(build_path, combined_file_name)
        self.combined_file = file_base.File(combined_file_path)

    def list_ino_files(self):
        files = self.list_files_of_extensions(arduino_src.INO_EXTS)
        if files and self.primary_file.is_file():
            files = [f for f in files if f.name.lower() !=
                     self.primary_file.name.lower()]
            files.insert(0, self.primary_file)
        return files

    def list_cpp_files(self):
        return self.list_files_of_extensions(arduino_src.CPP_EXTS)

    def list_h_files(self):
        return self.list_files_of_extensions(arduino_src.H_EXTS)

    def start_build(self, arduino_info, with_upload=False,
                    using_programmer=False):
        self.with_upload = with_upload
        self.using_programmer = using_programmer
        build_thread = threading.Thread(target=lambda:
                                        self.build(arduino_info))
        build_thread.start()

    def start_upload(self, arduino_info, using_programmer=False):
        self.using_programmer = using_programmer
        upload_thread = threading.Thread(target=lambda:
                                         self.upload(arduino_info))
        upload_thread.start()

    def start_burning_bootloader(self, arduino_info):
        burn_thread = threading.Thread(target=lambda:
                                       self.burn_bootloader(arduino_info))
        burn_thread.start()

    def build(self, arduino_info):
        self.console.start_print()
        self.error_while_build = False
        self.prepare_params(arduino_info)
        self.check_new_build(arduino_info)
        self.prepare_project_src_files()

        if self.o_paths:
            self.prepare_core_src_files()
            self.prepare_build_commands()
            self.exec_build_cmds()
        else:
            self.error_while_build = True
            print('[Done] No Source Files!')
        time.sleep(0.6)
        self.console.stop_print()

    def upload(self, arduino_info):
        self.build(arduino_info)
        if not self.error_while_build:
            self.exec_upload(arduino_info)

    def prepare_params(self, arduino_info):
        self.ino_files = self.list_ino_files()
        self.libraries = arduino_src.list_libraries(
            self.ino_files, arduino_info.get_h_lib_dict())

        self.ide_path = arduino_info.get_ide_dir().get_path()
        self.target_arch = arduino_info.get_target_arch()

        target_platform_path = arduino_info.get_target_platform().get_path()
        target_params = arduino_info.get_target_params()
        build_core = target_params.get('build.core', 'arduino:arduino')
        build_variant = target_params.get('build.variant', 'arduino:standard')

        ide_version = arduino_info.get_version()
        target_platform = arduino_info.get_target_platform()
        target_platform_path = target_platform.get_path()

        core_path = get_core_path(build_core, arduino_info, 'cores')
        self.core_dir = file_base.Dir(core_path)

        varient_path = get_core_path(build_variant, arduino_info, 'variants')
        self.varient_dir = file_base.Dir(varient_path)

        self.params = {}
        self.params['software'] = 'ARDUINO'
        self.params['build.path'] = self.build_path
        self.params['build.project_name'] = self.name
        self.params['build.arch'] = self.target_arch.upper()
        self.params['archive_file'] = 'core.a'
        self.params['runtime.ide.version'] = ide_version
        self.params['runtime.ide.path'] = self.ide_path
        self.params['runtime.platform.path'] = target_platform_path

        self.params.update(target_params)
        self.params['build.usb_manufacturer'] = 'Unknown'

        settings = sys_base.get_arduino_settings()
        extra_flag = ' ' + settings.get('extra_flag', '')
        c_flags = self.params.get('compiler.c.flags', '') + extra_flag
        cpp_flags = self.params.get('compiler.cpp.flags', '') + extra_flag
        S_flags = self.params.get('compiler.S.flags', '') + extra_flag
        self.params['compiler.c.flags'] = c_flags
        self.params['compiler.cpp.flags'] = cpp_flags
        self.params['compiler.S.flags'] = S_flags

        include_paths = [self.path, core_path, varient_path]
        for lib in self.libraries:
            src_dirs = lib.list_src_dirs(self.target_arch)
            include_paths += [d.get_path() for d in src_dirs]

        includes = ['"-I%s"' % path for path in include_paths]
        self.params['includes'] = ' '.join(includes)

        if not 'compiler.path' in self.params:
            compiler_path = '{runtime.ide.path}/hardware/tools/avr/bin/'
            self.params['compiler.path'] = compiler_path
        compiler_path = self.params.get('compiler.path')
        compiler_path = compiler_path.replace('{runtime.ide.path}',
                                              self.ide_path)
        if not os.path.isdir(compiler_path):
            self.params['compiler.path'] = ''

        self.replace_param_values()

    def check_new_build(self, arduino_info):
        self.is_new_build = False
        ide_path = arduino_info.get_ide_dir().get_path()
        sketchbook_path = arduino_info.get_sketchbook_dir().get_path()
        target_board_id = arduino_info.get_target_board_id()
        target_sub_board_ids = arduino_info.get_target_sub_board_ids()

        last_build_path = os.path.join(self.build_path, 'last_build.txt')
        last_build_file = file_base.SettingsFile(last_build_path)
        last_ide_path = last_build_file.get('ide_path')
        last_sketchbook_path = last_build_file.get('sketchbook_path')
        last_board_id = last_build_file.get('board_id')
        last_sub_board_ids = last_build_file.get('sub_board_ids')

        settings = sys_base.get_arduino_settings()
        full_compilation = settings.get('full_compilation')

        if full_compilation or ide_path != last_ide_path or \
                sketchbook_path != last_sketchbook_path or \
                target_board_id != last_board_id or \
                target_sub_board_ids != last_sub_board_ids:
            last_build_file.set('ide_path', ide_path)
            last_build_file.set('sketchbook_path', sketchbook_path)
            last_build_file.set('board_id', target_board_id)
            last_build_file.set('sub_board_ids', target_sub_board_ids)
            self.is_new_build = True

    def prepare_project_src_files(self):
        self.cpp_o_pairs = []
        self.o_paths = []

        if self.ino_files:
            self.ino_changed = check_ino_change(self.ino_files,
                                                self.combined_file)
            combined_file_path = self.combined_file.get_path()
            obj_path = combined_file_path + '.o'
            self.o_paths.append(obj_path)
            if self.is_new_build or self.ino_changed:
                combined_src = arduino_src.combine_ino_files(self.ino_files)
                self.combined_file.write(combined_src)

                self.cpp_o_pairs.append((combined_file_path, obj_path))

        cpp_files = self.list_cpp_files()
        self.cpp_o_pairs += gen_src_o_pairs(self.build_path, cpp_files,
                                            self.is_new_build)

        self.projetc_src_changed = False
        if self.cpp_o_pairs:
            self.projetc_src_changed = True

        self.o_paths += gen_o_paths(self.build_path, cpp_files)

    def prepare_core_src_files(self):
        cpp_files = self.core_dir.recursive_list_files(arduino_src.CPP_EXTS)
        cpp_files += self.varient_dir.recursive_list_files(
            arduino_src.CPP_EXTS)
        for lib in self.libraries:
            cpp_files += lib.list_cpp_files(self.target_arch)
        self.core_cpp_o_pairs = gen_src_o_pairs(self.build_path, cpp_files,
                                                self.is_new_build)
        self.core_o_paths = gen_o_paths(self.build_path, cpp_files)

        self.core_src_changed = False
        if self.core_cpp_o_pairs:
            self.core_src_changed = True

    def prepare_build_commands(self):
        default_cmd = 'echo "No Command"'
        compile_c_cmd = self.params.get('recipe.c.o.pattern', default_cmd)
        compile_cpp_cmd = self.params.get('recipe.cpp.o.pattern', default_cmd)
        compile_asm_cmd = self.params.get('recipe.S.o.pattern', default_cmd)
        ar_cmd = self.params.get('recipe.ar.pattern', default_cmd)
        combine_cmd = self.params.get('recipe.c.combine.pattern', default_cmd)
        eep_cmd = self.params.get('recipe.objcopy.eep.pattern', default_cmd)
        hex_cmd = self.params.get('recipe.objcopy.hex.pattern', default_cmd)

        cmd_txts = []
        self.cmds = []
        for cpp_path, o_path in (self.cpp_o_pairs + self.core_cpp_o_pairs):
            cmd = compile_cpp_cmd
            ext = os.path.splitext(cpp_path)[1]
            if ext == '.c':
                cmd = compile_c_cmd
            elif ext == '.S':
                cmd = compile_asm_cmd
            cmd = cmd.replace('{source_file}', cpp_path)
            cmd = cmd.replace('{object_file}', o_path)
            cmd_txt = 'Creating %s...\n' % o_path
            cmd_txts.append(cmd_txt)
            self.cmds.append(cmd)

        core_changed = False
        core_a_path = os.path.join(self.build_path, 'core.a')
        if self.core_src_changed and os.path.isfile(core_a_path):
            os.remove(core_a_path)
        if not os.path.isfile(core_a_path):
            core_changed = True
            cmd_txt = 'Creating core.a...\n'
            cmd_txts.append(cmd_txt)
            for o_path in self.core_o_paths:
                cmd = ar_cmd.replace('{object_file}', o_path)
                cmd_txts.append(cmd)
                self.cmds.append(cmd)

        if self.projetc_src_changed or core_changed:
            o_paths = ''
            for o_path in self.o_paths:
                o_paths += o_path
                o_paths += ' '
            o_paths = o_paths[:-1]

            cmd_txt = 'Creating %s.elf...\n' % self.name
            cmd_txts.append(cmd_txt)
            cmd = combine_cmd.replace('{object_files}', o_paths)
            cmd_txts.append(cmd)
            self.cmds.append(cmd)

            if eep_cmd:
                cmd_txt = 'Creating %s.eep...\n' % self.name
                cmd_txts.append(cmd_txt)
                cmd_txts.append(eep_cmd)
                self.cmds.append(eep_cmd)

            cmd_txt = 'Creating %s.hex or %s.bin...\n' % (self.name, self.name)
            cmd_txts.append(cmd_txt)
            cmd_txts.append(hex_cmd)
            self.cmds.append(hex_cmd)

    def exec_build_cmds(self):
        print('Start building...')
        self.error_while_build = exec_cmds(
            self.ide_path, self.cmds, self.console)
        if not self.error_while_build:
            print('[Done build.]')
            self.exec_size_cmd()

    def exec_size_cmd(self):
        default_cmd = 'echo "No Command"'
        size_cmd = self.params.get('recipe.size.pattern', default_cmd)
        os.chdir(self.ide_path)
        return_code, stdout, stderr = exec_cmd(size_cmd)
        settings = sys_base.get_arduino_settings()
        show_compilation_output = settings.get('build_verbose', False)
        if show_compilation_output:
            print(size_cmd)
            print(stdout)
        print(stderr)
        self.print_size(stdout)

    def print_size(self, text):
        size_total = int(self.params.get('upload.maximum_size'))
        size_data_total = int(self.params.get('upload.maximum_data_size'))

        size_regex = self.params.get('recipe.size.regex')
        pattern = re.compile(size_regex, re.M)
        size = sum(int(n) for n in pattern.findall(text))
        size_percent = size / size_total * 100
        txt = 'Sketch uses %d bytes (%.1f) ' % (size, size_percent)
        txt += 'of program storage space. Maximum is %d bytes.' % size_total
        print(txt)

        size_regex_data = self.params.get('recipe.size.regex.data', '')
        if size_regex_data and size_data_total:
            pattern = re.compile(size_regex_data, re.M)
            size_data = sum(int(n) for n in pattern.findall(text))
            size_data_percent = size_data / size_data_total * 100
            size_data_remain = size_data_total - size_data
            txt = 'Global variables use %d bytes ' % size_data
            txt += '(%.1f) of dynamic memory, ' % size_data_percent
            txt += 'leaving %d bytes for local variables. ' % size_data_remain
            txt += 'Maximum is %d bytes.' % size_data_total
            print(txt)

        # size_regex_eeprom = self.params.get('recipe.size.regex.eeprom')
        # pattern = re.compile(size_regex_eeprom, re.M)
        # size_eeprom = sum(int(n) for n in pattern.findall(text))
        # print(size_eeprom)

    def replace_param_values(self):
        for key in self.params:
            value = self.params[key]
            if '{' in value:
                value = replace_param_value(value, self.params)
                self.params[key] = value

    def exec_upload(self, arduino_info):
        self.console.start_print()
        if self.using_programmer or not self.params.get('upload.protocol'):
            self.upload_using_programmer(arduino_info)
            return

        settings = sys_base.get_arduino_settings()
        upload_port = settings.get('serial_port', 'no_serial')
        self.params['serial.port'] = upload_port
        if upload_port.startswith('/dev/'):
            upload_port_file = upload_port[5:]
        else:
            upload_port_file = upload_port
        self.params['serial.port.file'] = upload_port_file

        upload_tool = self.params.get('upload.tool', '')
        tool_params = arduino_info.get_tool_params(upload_tool)
        self.params.update(tool_params)

        show_upload_output = settings.get('upload_verbose', False)
        if show_upload_output:
            self.params['upload.verbose'] = self.params[
                'upload.params.verbose']
        else:
            self.params['upload.verbose'] = self.params['upload.params.quiet']

        do_touch = False
        bootloader_file = self.params.get('bootloader.file', '')
        if 'caterina' in bootloader_file.lower():
            do_touch = True
        elif self.params.get('upload.use_1200bps_touch') == 'true':
            do_touch = True

        wait_for_upload_port = False
        if self.params.get('upload.wait_for_upload_port') == 'true':
            wait_for_upload_port = True

        if do_touch:
            before_ports = serial_base.list_serial_ports()
            if upload_port in before_ports:
                print(
                    'Forcing reset using 1200bps open/close on port %s' %
                    upload_port)
                serial_base.touch_port(upload_port, 1200)
            if wait_for_upload_port:
                if sys_base.get_os_name() != 'osx':
                    time.sleep(0.4)
                upload_port = serial_base.wait_for_port(upload_port,
                                                        before_ports)
            else:
                time.sleep(4)
            self.params['serial.port'] = upload_port

            if upload_port.startswith('/dev/'):
                upload_port_file = upload_port[5:]
            else:
                upload_port_file = upload_port
            self.params['serial.port.file'] = upload_port_file

        self.replace_param_values()
        default_cmd = 'echo "No Command"'
        cmd = self.params.get('upload.pattern', default_cmd)

        verify_code = settings.get('verify_code', False)
        if verify_code:
            cmd += ' -V'

        return_code, stdout, stderr = exec_cmd(cmd)

        settings = sys_base.get_arduino_settings()
        show_upload_output = settings.get('upload_verbose', False)
        if show_upload_output:
            print(cmd)
            print(stdout)
        print(stderr)

        # Remove the magic baud rate (1200bps) to avoid
        # future unwanted board resets
        if return_code == 0 and do_touch:
            if wait_for_upload_port:
                time.sleep(0.1)
                timeout = time.time() + 2
                while timeout > time.time():
                    ports = serial_base.list_serial_ports()
                    if upload_port in ports:
                        serial_base.touch_port(upload_port, 9600)
                        break
                    time.sleep(0.25)
            else:
                serial_base.touch_port(upload_port, 9600)

        if return_code == 0:
            print('[Done Upload.]')
        time.sleep(0.6)
        self.console.stop_print()

    def upload_using_programmer(self, arduino_info):
        settings = sys_base.get_arduino_settings()

        upload_port = settings.get('serial_port', 'no_serial')
        self.params['serial.port'] = upload_port
        if upload_port.startswith('/dev/'):
            upload_port_file = upload_port[5:]
        else:
            upload_port_file = upload_port
        self.params['serial.port.file'] = upload_port_file

        program_tool = self.params.get('program.tool', '')
        tool_params = arduino_info.get_tool_params(program_tool)
        self.params.update(tool_params)

        show_upload_output = settings.get('upload_verbose', False)
        if show_upload_output:
            self.params['program.verbose'] = self.params.get(
                'program.params.verbose', '')
        else:
            self.params['program.verbose'] = self.params.get(
                'program.params.quiet', '')

        self.replace_param_values()
        default_cmd = 'echo "No Command"'
        cmd = self.params.get('program.pattern', default_cmd)

        verify_code = settings.get('verify_code', False)
        if verify_code:
            cmd += ' -V'
        return_code, stdout, stderr = exec_cmd(cmd)

        settings = sys_base.get_arduino_settings()
        show_upload_output = settings.get('upload_verbose', False)
        if show_upload_output:
            print(cmd)
            print(stdout)
        print(stderr)
        if return_code == 0:
            print('[Done Upload.]')
        time.sleep(0.6)
        self.console.stop_print()

    def burn_bootloader(self, arduino_info):
        self.console.start_print()
        self.prepare_params(arduino_info)
        settings = sys_base.get_arduino_settings()

        upload_port = settings.get('serial_port', 'no_serial')
        self.params['serial.port'] = upload_port
        if upload_port.startswith('/dev/'):
            upload_port_file = upload_port[5:]
        else:
            upload_port_file = upload_port
        self.params['serial.port.file'] = upload_port_file

        bootloader_tool = self.params.get('bootloader.tool', '')
        tool_params = arduino_info.get_tool_params(bootloader_tool)
        self.params.update(tool_params)

        show_upload_output = settings.get('upload_verbose', False)
        if show_upload_output:
            self.params['erase.verbose'] = self.params.get(
                'erase.params.verbose', '')
            self.params['bootloader.verbose'] = self.params.get(
                'bootloader.params.verbose', '')
        else:
            self.params['erase.verbose'] = self.params.get(
                'erase.params.quiet', '')
            self.params['bootloader.verbose'] = self.params.get(
                'bootloader.params.quiet', '')

        self.replace_param_values()
        default_cmd = 'echo "No Command"'

        cmds = []
        cmds.append(self.params.get('erase.pattern', default_cmd))
        cmds.append(self.params.get('bootloader.pattern', default_cmd))
        error = exec_cmds(self.ide_path, cmds, self.console)
        if not error:
            print('[Done Burning Bootloader.]')
        time.sleep(0.6)
        self.console.stop_print()


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


def exec_cmd(cmd):
    cmd = formatCommand(cmd)
    compile_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
    result = compile_proc.communicate()
    return_code = compile_proc.returncode
    stdout = result[0].decode(sys_base.get_sys_encoding())
    stderr = result[1].decode(sys_base.get_sys_encoding())
    return (return_code, stdout, stderr)


def formatCommand(cmd):
    # cmd = cmd.replace('\\', '/')
    return cmd


def gen_src_o_pairs(build_path, src_files, new_build=False):
    obj_paths = gen_o_paths(build_path, src_files)
    obj_files = [file_base.File(path) for path in obj_paths]

    path_pairs = []
    for src_file, obj_file in zip(src_files, obj_files):
        if new_build or src_file.get_mtime() > obj_file.get_mtime():
            path_pair = (src_file.get_path(), obj_file.get_path())
            path_pairs.append(path_pair)
    return path_pairs


def gen_o_paths(build_path, src_files):
    obj_names = [f.get_name() + '.o' for f in src_files]
    obj_paths = [os.path.join(build_path, name) for name in obj_names]
    return obj_paths


def check_ino_change(ino_files, combined_file):
    ino_changed = False
    combined_file_path = combined_file.get_path()
    obj_path = combined_file_path + '.o'
    obj_file = file_base.File(obj_path)
    for ino_file in ino_files:
        if ino_file.get_mtime() > obj_file.get_mtime():
            ino_changed = True
            break
    return ino_changed


def get_core_path(param_value, arduino_info, dir_name):
    target_platform_path = arduino_info.get_target_platform().get_path()
    platform_path = target_platform_path
    param_name = param_value.strip()

    if ':' in param_value:
        package_name, param_name = param_value.split(':')
        package_name = package_name.strip()
        param_name = param_name.strip()

        package_id = ''
        ide_package_id = 'ide.' + package_name
        sketchbook_package_id = 'sketchbook.' + package_name
        arduino_id_item_dict = arduino_info.get_id_item_dict()
        for _id in [ide_package_id, sketchbook_package_id]:
            if _id in arduino_id_item_dict:
                package_id = _id
                break
        if package_id:
            target_arch = arduino_info.get_target_arch()
            plaform_id = package_id + '.' + target_arch
            platform = arduino_id_item_dict.get(plaform_id, None)
            if platform:
                platform_path = platform.get_path()

    if platform_path:
        cores_path = os.path.join(platform_path, dir_name)
        core_path = os.path.join(cores_path, param_name)
    if not os.path.isdir(core_path):
        cores_path = os.path.join(target_platform_path, dir_name)
        core_path = os.path.join(cores_path, param_name)
    if not os.path.isdir(core_path):
        default_platform_path = get_default_platform_path(arduino_info)
        cores_path = os.path.join(default_platform_path, dir_name)
        core_path = os.path.join(cores_path, param_name)
    return core_path


def get_default_platform_path(arduino_info):
    platform_path = ''
    target_arch = arduino_info.get_target_arch()
    arduino_id_item_dict = arduino_info.get_id_item_dict()
    package_id = 'ide.arduino'
    plaform_id = package_id + '.' + target_arch
    if plaform_id in arduino_id_item_dict:
        platform = arduino_id_item_dict.get(plaform_id)
        platform_path = platform.get_path()
    return platform_path


def exec_cmds(working_dir, cmds, console):
    settings = sys_base.get_arduino_settings()
    show_compilation_output = settings.get('build_verbose', False)

    error = False
    os.chdir(working_dir)
    for cmd in cmds:
        return_code, stdout, stderr = exec_cmd(cmd)
        if show_compilation_output:
            print(cmd)
            print(stdout)
        print(stderr)
        if return_code != 0:
            print('[Exit Error Code %d]' % return_code)
            error = True
            break
    return error
