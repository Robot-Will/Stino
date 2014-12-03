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


def load_keywords():
    arduino_info = st_base.get_arduino_info()
    ide_dir = arduino_info.get_ide_dir()
    keywords = ide_dir.get_keywords()

    for root in arduino_info.get_root_dirs():
        libraries = root.get_libraries()
        for library in libraries:
            keywords += library.get_keywords()
        for package in root.get_packages():
            for platform in package.get_platforms():
                libraries = platform.get_libraries()
                for library in libraries:
                    keywords += library.get_keywords()
    return keywords


def create_completions():
    user_path = st_base.get_stino_user_path()
    file_path = os.path.join(user_path, 'Stino.sublime-completions')
    completions_file = pyarduino.base.json_file.JSONFile(file_path)

    cpp_keywords = ['define', 'error', 'include', 'elif', 'endif']
    cpp_keywords += ['ifdef', 'ifndef', 'undef', 'line', 'pragma']

    keywords = load_keywords()
    keyword_ids = [k.get_id() for k in keywords]
    keyword_ids += cpp_keywords

    completions_dict = {'scope': 'source.arduino'}
    completions_dict['completions'] = keyword_ids
    completions_file.set_data(completions_dict)


def create_syntax_file():
    keywords = load_keywords()
    LITERAL1s = [k.get_id() for k in keywords if k.get_type() == 'LITERAL1']
    KEYWORD1s = [k.get_id() for k in keywords if k.get_type() == 'KEYWORD1']
    KEYWORD2s = [k.get_id() for k in keywords if k.get_type() == 'KEYWORD2']
    KEYWORD3s = [k.get_id() for k in keywords if k.get_type() == 'KEYWORD3']
    LITERAL1_text = '|'.join(LITERAL1s)
    KEYWORD1_text = '|'.join(KEYWORD1s)
    KEYWORD2_text = '|'.join(KEYWORD2s)
    KEYWORD3_text = '|'.join(KEYWORD3s)

    preset_path = st_base.get_preset_path()
    file_path = os.path.join(preset_path, 'Arduino.syntax')
    template_file = pyarduino.base.abs_file.File(file_path)
    text = template_file.read()
    text = text.replace('${LITERAL1}', LITERAL1_text)
    text = text.replace('${KEYWORD1}', KEYWORD1_text)
    text = text.replace('${KEYWORD2}', KEYWORD2_text)
    text = text.replace('${KEYWORD3}', KEYWORD3_text)

    user_path = st_base.get_stino_user_path()
    file_path = os.path.join(user_path, 'Arduino.tmLanguage')
    syntax_file = pyarduino.base.abs_file.File(file_path)
    syntax_file.write(text)


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
    create_syntax_file()


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

    settings = st_base.get_settings()
    bare_gcc = settings.get('bare_gcc', False)

    if bare_gcc:
        ext = '.cpp'
    else:
        ext = '.ino'

    template_file_name = 'template' + ext
    preset_path = st_base.get_preset_path()
    template_file_path = os.path.join(preset_path, template_file_name)
    template_file = pyarduino.base.abs_file.File(template_file_path)
    src_code = template_file.read()

    src_file_name = sketch_name + ext
    src_file_path = os.path.join(sketch_path, src_file_name)
    src_file = pyarduino.base.abs_file.File(src_file_path)

    src_code = src_code.replace('${src_file_name}', src_file_name)
    src_file.write(src_code)

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

    project_params = window.project_data()
    if project_params is None:
        project_params = {}
    folders = project_params.setdefault('folders', [])
    folders.append({'follow_symlinks': True, 'path': sketch_path})
    project_params['folders'] = folders
    window.set_project_data(project_params)


def import_library(view, edit, library_path):
    arduino_info = st_base.get_arduino_info()
    target_arch = arduino_info.get_target_board_info().get_target_arch()
    library = pyarduino.arduino_library.Library(library_path)
    h_files = library.list_h_files(target_arch)

    region = sublime.Region(0, view.size())
    src_text = view.substr(region)
    headers = pyarduino.arduino_src.list_headers_from_src(src_text)
    h_files = [f for f in h_files if not f.get_name() in headers]

    includes = ['#include <%s>' % f.get_name() for f in h_files]
    text = '\n'.join(includes)
    if text:
        text += '\n'
    view.insert(edit, 0, text)


def handle_sketch(view, func, using_programmer=False):
    window = view.window()
    views = window.views()
    if view not in views:
        view = window.active_view()
    if view.file_name() is None:
        tmp_path = pyarduino.base.sys_path.get_tmp_path()
        tmp_path = os.path.join(tmp_path, 'Arduino')
        name = str(time.time()).split('.')[1]
        sketch_path = os.path.join(tmp_path, name)
        os.makedirs(sketch_path)

        settings = st_base.get_settings()
        bare_gcc = settings.get('bare_gcc', False)
        if bare_gcc:
            ext = '.cpp'
        else:
            ext = '.ino'
        src_file_name = name + ext
        src_file_path = os.path.join(sketch_path, src_file_name)

        region = sublime.Region(0, view.size())
        text = view.substr(region)
        src_file = pyarduino.base.abs_file.File(src_file_path)
        src_file.write(text)

        view.set_scratch(True)
        window = view.window()
        window.run_command('close')
        view = window.open_file(src_file_path)

    if view.is_dirty():
        view.run_command('save')
    file_path = view.file_name()
    sketch_path = os.path.dirname(file_path)
    func(view, sketch_path, using_programmer)


def build_sketch(view, sketch_path, using_programmer=False):
    window = view.window()
    console_name = 'build|' + sketch_path + '|' + str(time.time())
    console = st_console.Console(window, name=console_name)
    compiler = pyarduino.arduino_compiler.Compiler(sketch_path, console)
    compiler.build()


def upload_sketch(view, sketch_path, using_programmer):
    window = view.window()
    console_name = 'upload|' + sketch_path + '|' + str(time.time())
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


def change_sub_board(window, option_index, sub_board_id):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_sub_board(option_index, sub_board_id)
    view = window.active_view()
    set_status(view)


def change_programmer(programmer_id):
    arduino_info = st_base.get_arduino_info()
    arduino_info.change_programmer(programmer_id)


def archive_sketch(window, sketch_path):
    sketch_name = os.path.basename(sketch_path)
    console = st_console.Console(window, str(time.time()))
    message_queue = pyarduino.base.message_queue.MessageQueue(console)
    message_queue.put('Archive Sketch {0}...\\n', sketch_name)

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
        text = 'Archiving the sketch has been canceled because '
        text += "the sketch couldn't save properly.\\n"
        message_queue.put(text)
    else:
        for file_name in file_names:
            opened_zipfile.write(file_name)
        opened_zipfile.close()
        message_queue.put('Archive sketch as: {0}.\\n', zip_file_path)
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
        text = 'Arduino {0} is found at {1}.\\n'

        console = st_console.Console(window, str(time.time()))
        message_queue = pyarduino.base.message_queue.MessageQueue(console)
        message_queue.put(text, version_name, dir_path)
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

    text = 'Sketchbook is changed to {0}.\\n'
    console = st_console.Console(window, str(time.time()))
    message_queue = pyarduino.base.message_queue.MessageQueue(console)
    message_queue.put(text, dir_path)
    message_queue.print_screen(one_time=True)

    create_menus()
    return 0


def set_build_path(window, dir_path):
    settings = st_base.get_settings()
    settings.set('build_path', dir_path)
    text = 'Build folder is changed to {0}.\\n'
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
            sel_path = paths[index]
            if self_path == pyarduino.base.sys_path.ROOT_PATH:
                self_path = '/'
            dir_path = os.path.abspath(self_path)
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
    infos = []
    exts = ['ino', 'pde', 'cpp', 'c', '.S']
    file_name = view.file_name()
    if file_name and file_name.split('.')[-1] in exts:
        arduino_info = st_base.get_arduino_info()
        version_name = arduino_info.get_ide_dir().get_version_name()
        version_text = 'Arduino %s' % version_name
        infos.append(version_text)

        target_board_info = arduino_info.get_target_board_info()
        target_board = target_board_info.get_target_board()
        if target_board:
            target_board_caption = target_board.get_caption()
            infos.append(target_board_caption)

            if target_board.has_options():
                target_sub_boards = target_board_info.get_target_sub_boards()
                for index, target_sub_board in enumerate(target_sub_boards):
                    caption_text = target_sub_board.get_caption()
                    if index == 0:
                        caption_text = '[' + caption_text
                    if index == len(target_sub_boards) - 1:
                        caption_text += ']'
                    infos.append(caption_text)
        else:
            target_board_caption = 'No board'
            infos.append(target_board_caption)

        settings = st_base.get_settings()
        target_serial_port = settings.get('serial_port', 'No serial port')
        serial_ports = pyarduino.base.serial_port.list_serial_ports()
        if not target_serial_port in serial_ports:
            target_serial_port = 'No serial port'
        serial_text = 'on %s' % target_serial_port
        infos.append(serial_text)

        text = ', '.join(infos)
        view.set_status('Arduino', text)


def show_items_panel(window, item_type):
    sublime.set_timeout(lambda: window.show_quick_panel(['1', '2'], ppp))


def ppp(index):
    print(index)
