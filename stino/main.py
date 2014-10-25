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
import shutil
import sublime
import re
import zipfile
import time

from . import pyarduino
from . import st_base
from . import st_menu
from . import st_console


def set_pyarduino():
    user_path = st_base.get_stino_user_path()
    package_path = st_base.get_plugin_path()
    stino_path = os.path.join(package_path, 'stino')
    pyarduino_path = os.path.join(stino_path, 'pyarduino')
    settings_path = os.path.join(pyarduino_path, 'pyarduino.settings')
    settings = pyarduino.base.settings.Settings(settings_path)
    settings.set('package_path', package_path)
    settings.set('user_path', user_path)


def create_completions():
    user_path = st_base.get_stino_user_path()
    file_path = os.path.join(user_path, 'Stino.sublime-completions')
    completions_file = pyarduino.base.json_file.JSONFile(file_path)

    arduino_info = st_base.get_arduino_info()
    ide_dir = arduino_info.get_ide_dir()
    keyword_ids = ide_dir.get_keyword_ids()

    for root in arduino_info.get_root_dirs():
        libraries = root.get_libraries()
        for library in libraries:
            keyword_ids += library.get_keyword_ids()
        for package in root.get_packages():
            for platform in package.get_platforms():
                libraries = platform.get_libraries()
                for library in libraries:
                    keyword_ids += library.get_keyword_ids()

    completions_dict = {'scope': 'source.arduino'}
    completions_dict['completions'] = keyword_ids
    completions_file.set_data(completions_dict)


def create_sub_menus():
    arduino_info = st_base.get_arduino_info()
    st_menu.create_sketchbook_menu(arduino_info)
    st_menu.create_examples_menu(arduino_info)
    st_menu.create_libraries_menu(arduino_info)
    st_menu.create_boards_menu(arduino_info)
    st_menu.create_board_options_menu(arduino_info)
    st_menu.create_programmers_menu(arduino_info)
    st_menu.create_serials_menu()
    st_menu.create_languages_menu()


def create_menus():
    st_menu.create_main_menu()
    settings = st_base.get_settings()
    show_arduino_menu = settings.get('show_arduino_menu', True)
    if show_arduino_menu:
        st_menu.create_arduino_menu()
        create_sub_menus()
    else:
        user_menu_path = st_base.get_user_menu_path()
        if os.path.isdir(user_menu_path):
            shutil.rmtree(user_menu_path)


def update_menu():
    arduino_info = st_base.get_arduino_info()
    arduino_info.reload()
    arduino_info.update()
    i18n = st_base.get_i18n()
    i18n.load()
    create_menus()
    create_completions()


def create_sketch(sketch_name):
    arduino_info = st_base.get_arduino_info()
    sketchbook_dir = arduino_info.get_sketchbook_dir()
    sketchbook_path = sketchbook_dir.get_path()
    sketch_path = os.path.join(sketchbook_path, sketch_name)

    index = 0
    org_name = sketch_name
    while os.path.exists(sketch_path):
        sketch_name = '%s_%d' % (org_name, index)
        sketch_path = os.path.join(sketchbook_path, sketch_name)
        index += 1
    os.makedirs(sketch_path)

    preset_path = st_base.get_preset_path()
    template_file_path = os.path.join(preset_path, 'template.ino')
    template_file = pyarduino.file_base.File(template_file_path)
    src_code = template_file.read()

    ino_file_name = sketch_name + '.ino'
    ino_file_path = os.path.join(sketch_path, ino_file_name)
    ino_file = pyarduino.file_base.File(ino_file_path)

    src_code = src_code.replace('${ino_file_name}', ino_file_name)
    ino_file.write(src_code)

    arduino_info.reload()
    arduino_info.update()
    st_menu.create_sketchbook_menu(arduino_info)
    return sketch_path


def new_sketch(window, sketch_name):
    sketch_path = create_sketch(sketch_name)
    open_sketch(window, sketch_path)


def open_sketch(window, sketch_path):
    project = pyarduino.arduino_project.Project(sketch_path)
    ino_files = project.list_ino_files()
    cpp_files = project.list_cpp_files()
    h_files = project.list_h_files()
    files = ino_files + cpp_files + h_files

    views = []
    for f in files:
        view = window.open_file(f.get_path())
        views.append(view)
    if views:
        window.focus_view(views[0])


def import_library(view, edit, library_path):
    arduino_info = st_base.get_arduino_info()
    target_arch = arduino_info.get_target_board_info().get_target_arch()
    library = pyarduino.arduino_library.Library(library_path)
    h_files = library.list_h_files(target_arch)
    text = ''
    for h_file in h_files:
        text += '#include <%s>\n' % h_file.get_name()
    text += '\n'
    view.insert(edit, 0, text)


def build_sketch(window, sketch_path):
    console_name = 'build.' + str(time.time())
    console = st_console.Console(window, name=console_name)
    compiler = pyarduino.arduino_compiler.Compiler(sketch_path, console)
    compiler.build()


def upload_sketch(window, sketch_path, using_programmer=False):
    console_name = 'upload.' + str(time.time())
    console = st_console.Console(window, name=console_name)
    uploader = pyarduino.arduino_uploader.Uploader(sketch_path, console)
    uploader.upload(using_programmer)


def burn_bootloader(window):
    console_name = 'bootloader.' + str(time.time())
    console = st_console.Console(window, name=console_name)
    bootloader = pyarduino.arduino_bootloader.Bootloader(console)
    bootloader.burn()


def change_board(window, board_id):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_board(board_id)
    st_menu.create_board_options_menu(arduino_info)
    view = window.active_view()
    set_status(view)


def change_sub_board(option_index, sub_board_id):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_sub_board(option_index, sub_board_id)


def change_programmer(programmer_id):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_programmer(programmer_id)


def archive_sketch(window, sketch_path):
    console = st_console.Console(window, str(time.time()))
    message_queue = pyarduino.base.message_queue.MessageQueue(console)
    message_queue.put('Archive {0}\n', sketch_path)

    sketch_name = os.path.basename(sketch_path)
    zip_file_name = sketch_name + '.zip'
    document_path = pyarduino.base.sys_path.get_document_path()
    zip_file_path = os.path.join(document_path, zip_file_name)
    os.chdir(sketch_path)
    sketch_dir = pyarduino.base.abs_file.Dir(sketch_path)
    files = sketch_dir.list_files()
    file_names = [f.get_name() for f in files]
    try:
        opened_zipfile = zipfile.ZipFile(zip_file_path,
                                         'w', zipfile.ZIP_DEFLATED)
    except IOError:
        message_queue.put('Error occured while writing {0}.\n', zip_file_path)
    else:
        for file_name in file_names:
            opened_zipfile.write(file_name)
        opened_zipfile.close()
        message_queue.put('Done writing {0}.\n', zip_file_path)
    message_queue.print_screen(one_time=True)


def get_url(url):
    arduino_info = st_base.get_arduino_info()
    ide_dir = arduino_info.get_ide_dir()
    ide_path = ide_dir.get_path()

    file_name = url + '.html'
    reference_folder = os.path.join(ide_path, 'reference')
    reference_file = os.path.join(reference_folder, file_name)
    if os.path.isfile(reference_file):
        reference_file = reference_file.replace(os.path.sep, '/')
        url = 'file://' + reference_file
    else:
        url = 'http://arduino.cc'
    return url


def find_in_ref(view):
    arduino_info = st_base.get_arduino_info()
    ide_dir = arduino_info.get_ide_dir()
    id_keyword_dict = ide_dir.get_id_keyword_dict()

    ref_list = []
    selected_text = get_selected_text_from_view(view)
    words = get_word_list_from_text(selected_text)
    for word in words:
        if word in id_keyword_dict:
            keyword = id_keyword_dict.get(word)
            ref = keyword.get_ref()
            if ref and not ref in ref_list:
                ref_list.append(ref)
    for ref in ref_list:
        url = get_url(ref)
        sublime.run_command('open_url', {'url': url})


def get_selected_text_from_view(view):
    selected_text = ''
    region_list = view.sel()
    for region in region_list:
        selected_region = view.word(region)
        selected_text += view.substr(selected_region)
        selected_text += '\n'
    return selected_text


def get_word_list_from_text(text):
    pattern_text = r'\b\w+\b'
    word_list = re.findall(pattern_text, text)
    return word_list


def is_arduino_ide_path(dir_path):
    path = pyarduino.arduino_root.update_ide_path(dir_path)
    return pyarduino.arduino_root.is_arduino_ide_path(path)


def set_arduino_ide_path(window, dir_path):
    if is_arduino_ide_path(dir_path):
        arduino_info = st_base.get_arduino_info()
        arduino_info.change_ide_path(dir_path)

        ide_dir = arduino_info.get_ide_dir()
        version_name = ide_dir.get_version_name()
        text = 'Arduino {0} is found!\n'

        console = st_console.Console(window, str(time.time()))
        message_queue = pyarduino.base.message_queue.MessageQueue(console)
        message_queue.put(text, version_name)
        message_queue.print_screen(one_time=True)

        create_menus()
        view = window.active_view()
        set_status(view)
        return 0
    else:
        return 1


def set_sketchbook_path(window, dir_path):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_sketchbook_path(dir_path)

    text = 'Sketchbook is set to {0}!\n'
    console = st_console.Console(window, str(time.time()))
    message_queue = pyarduino.base.message_queue.MessageQueue(console)
    message_queue.put(text, dir_path)
    message_queue.print_screen(one_time=True)

    create_menus()
    return 0


def set_build_path(window, dir_path):
    settings = st_base.get_settings()
    settings.set('build_path', dir_path)
    text = 'Build Folder is set to {0}!\n'
    console = st_console.Console(window, str(time.time()))
    message_queue = pyarduino.base.message_queue.MessageQueue(console)
    message_queue.put(text, dir_path)
    message_queue.print_screen(one_time=True)
    return 0


def select_arduino_dir(window):
    select_dir(window, func=set_arduino_ide_path,
               condition_func=is_arduino_ide_path)


def change_sketchbook_dir(window):
    select_dir(window, func=set_sketchbook_path, is_user=True)


def change_build_dir(window):
    select_dir(window, func=set_build_path, is_user=True)


def select_dir(window, index=-2, level=0, paths=None,
               func=None, condition_func=None, is_user=False):
    if index == -1:
        return ''

    if level > 0 and index == 0:
        sel_path = paths[0].split('(')[1][:-1]
        if func:
            return_code = func(window, sel_path)
            if return_code == 0:
                return
        else:
            return
    else:
        if index == 1:
            level -= 1
        elif index > 1:
            level += 1

        if level <= 0:
            level = 0
            dir_path = '.'
            parent_path = '..'
            if is_user:
                paths = pyarduino.base.sys_path.list_user_root_path()
            else:
                paths = pyarduino.base.sys_path.list_os_root_path()
        else:
            dir_path = os.path.abspath(paths[index])
            if condition_func and condition_func(dir_path):
                func(window, dir_path)
                return
            parent_path = os.path.join(dir_path, '..')

            cur_dir = pyarduino.base.abs_file.Dir(dir_path)
            sub_dirs = cur_dir.list_dirs()
            paths = [d.get_path() for d in sub_dirs]
        paths.insert(0, parent_path)
        paths.insert(0, 'Select current dir (%s)' % dir_path)

    sublime.set_timeout(lambda: window.show_quick_panel(
        paths, lambda index: select_dir(window, index, level, paths,
                                        func, condition_func, is_user)), 5)


def update_serial_info():
    st_menu.create_serials_menu()
    window = sublime.active_window()
    view = window.active_view()
    set_status(view)


def get_serial_listener():
    serial_listener = pyarduino.base.serial_listener.SerialListener(
        func=update_serial_info)
    return serial_listener


def toggle_serial_monitor(window):
    monitor_module = pyarduino.base.serial_monitor
    serial_monitor = None

    settings = st_base.get_settings()
    serial_port = settings.get('serial_port', '')
    serial_ports = pyarduino.base.serial_port.list_serial_ports()
    if serial_port in serial_ports:
        if serial_port in monitor_module.serials_in_use:
            serial_monitor = monitor_module.serial_monitor_dict.get(
                serial_port, None)
        if not serial_monitor:
            monitor_view = st_console.MonitorView(window, serial_port)
            serial_monitor = pyarduino.base.serial_monitor.SerialMonitor(
                serial_port, monitor_view)

        if not serial_monitor.is_running():
            serial_monitor.start()
            if not serial_port in monitor_module.serials_in_use:
                monitor_module.serials_in_use.append(serial_port)
            monitor_module.serial_monitor_dict[serial_port] = serial_monitor
        else:
            serial_monitor.stop()
            monitor_module.serials_in_use.remove(serial_port)


def send_serial_message(text):
    monitor_module = pyarduino.base.serial_monitor

    settings = st_base.get_settings()
    serial_port = settings.get('serial_port', '')
    if serial_port in monitor_module.serials_in_use:
        serial_monitor = monitor_module.serial_monitor_dict.get(
            serial_port, None)
        if serial_monitor and serial_monitor.is_running():
            serial_monitor.send(text)


def set_status(view):
    exts = ['ino', 'pde', 'cpp', 'c', '.S']
    file_name = view.file_name()
    if file_name and file_name.split('.')[-1] in exts:
        arduino_info = st_base.get_arduino_info()
        version_name = arduino_info.get_ide_dir().get_version_name()
        target_board = arduino_info.get_target_board_info().get_target_board()
        if target_board:
            target_board_caption = target_board.get_caption()
        else:
            target_board_caption = 'No board'

        settings = st_base.get_settings()
        target_serial_port = settings.get('serial_port', 'No serial port')
        serial_ports = pyarduino.base.serial_port.list_serial_ports()
        if not target_serial_port in serial_ports:
            target_serial_port = 'No serial port'

        text = 'Arduino %s, %s on %s' % (
            version_name, target_board_caption, target_serial_port)
        view.set_status('Arduino', text)
