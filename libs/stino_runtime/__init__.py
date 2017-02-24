#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import glob
import sublime

from base_utils import file
from base_utils import c_file
from base_utils import index_file
from base_utils import plain_params_file
from base_utils import default_st_dirs
from base_utils import default_arduino_dirs
from base_utils import serial_port
from . import const
from . import st_menu
from . import selected

plugin_name = const.PLUGIN_NAME


def get_app_dir_settings():
    """."""
    dir_path = default_st_dirs.get_plugin_config_path(plugin_name)
    file_path = os.path.join(dir_path, 'app_dir.stino-settings')
    app_dir_settings = file.SettingsFile(file_path)
    return app_dir_settings


def get_arduino_dir_path(app_dir_settings):
    """."""
    app_dir_path = app_dir_settings.get('app_dir_path')
    if not app_dir_path:
        app_dir_path = '{$default}'
        app_dir_settings.set('app_dir_path', app_dir_path)
    if app_dir_path == '{$default}':
        dir_path = default_arduino_dirs.arduino_app_path()
    elif app_dir_path == '{$sublime}':
        dir_path = default_st_dirs.get_plugin_config_path(plugin_name)
    elif os.path.isabs(app_dir_path):
        if os.path.isdir(app_dir_path):
            dir_path = app_dir_path
        else:
            try:
                os.makedirs(app_dir_path)
            except OSError:
                app_dir_path = '{$default}'
                app_dir_settings.set('app_dir_path', app_dir_path)
                dir_path = default_arduino_dirs.arduino_app_path()
            else:
                dir_path = app_dir_path
    else:
        app_dir_path = '{$default}'
        app_dir_settings.set('app_dir_path', app_dir_path)
        dir_path = default_arduino_dirs.arduino_app_path()
    return dir_path


def get_sketchbook_path(app_dir_settings):
    """."""
    sketchbook_path = app_dir_settings.get('sketchbook_path')
    if not sketchbook_path:
        sketchbook_path = '{$default}'
        app_dir_settings.set('sketchbook_path', sketchbook_path)
    if sketchbook_path == '{$default}':
        dir_path = default_arduino_dirs.arduino_sketchbook_path()
    elif sketchbook_path == '{$sublime}':
        dir_path = default_st_dirs.get_plugin_config_path(plugin_name)
        dir_path = os.path.join(dir_path, 'Arduino')
    elif os.path.isabs(sketchbook_path):
        if os.path.isdir(sketchbook_path):
            dir_path = sketchbook_path
        else:
            try:
                os.makedirs(sketchbook_path)
            except OSError:
                sketchbook_path = '{$default}'
                app_dir_settings.set('sketchbook_path', sketchbook_path)
                dir_path = default_arduino_dirs.arduino_sketchbook_path()
            else:
                dir_path = sketchbook_path
    else:
        sketchbook_path = '{$default}'
        app_dir_settings.set('sketchbook_path', sketchbook_path)
        dir_path = default_arduino_dirs.arduino_sketchbook_path()
    return dir_path


def get_index_files_info(arduino_dir_path):
    """."""
    file_paths = glob.glob(arduino_dir_path + '/package*_index.json')
    index_files = index_file.IndexFiles(file_paths)
    info = index_files.get_info()
    return info


def get_platform_name(arduino_info, pkg_name, plt_arch):
    """."""
    plt_name = ''
    pkgs_info = arduino_info.get('packages', {})
    pkg_info = pkgs_info.get(pkg_name, {})
    plts_info = pkg_info.get('platforms', {})
    plt_names = plts_info.get('names', [])
    plt_arches = plts_info.get('arches', [])
    if plt_arch in plt_arches:
        index = plt_arches.index(plt_arch)
        plt_name = plt_names[index]
    return plt_name


def get_installed_packages_info(arduino_info):
    """."""
    installed_packages_info = {'installed_packages': {}}
    arduino_dir_path = arduino_info['arduino_app_path']
    packages_path = os.path.join(arduino_dir_path, 'packages')
    package_paths = glob.glob(packages_path + '/*')
    package_names = [os.path.basename(p) for p in package_paths]
    installed_packages_info['installed_packages']['names'] = package_names

    for package_path in package_paths:
        pkg_name = os.path.basename(package_path)
        pkg_info = {'platforms': {}}
        hardware_path = os.path.join(package_path, 'hardware')
        platform_paths = glob.glob(hardware_path + '/*')

        pkg_info['platforms']['names'] = []
        for platform_path in platform_paths:
            plt_arch = os.path.basename(platform_path)
            plt_name = get_platform_name(arduino_info, pkg_name, plt_arch)
            pkg_info['platforms']['names'].append(plt_name)

            version_paths = glob.glob(platform_path + '/*')
            versions = [os.path.basename(p) for p in version_paths]
            plt_info = {'versions': versions}
            pkg_info['platforms'][plt_name] = plt_info
        installed_packages_info['installed_packages'][pkg_name] = pkg_info
    return installed_packages_info


def get_boards_info(arduino_info):
    """."""
    platform_path = selected.get_sel_platform_path(arduino_info)
    boards_file_path = os.path.join(platform_path, 'boards.txt')
    boards_file = plain_params_file.BoardsFile(boards_file_path)
    boards_info = boards_file.get_boards_info()
    return boards_info


def get_programmers_info(arduino_info):
    """."""
    platform_path = selected.get_sel_platform_path(arduino_info)
    programmers_file_path = os.path.join(platform_path, 'programmers.txt')
    programmers_file = plain_params_file.ProgrammersFile(programmers_file_path)
    programmers_info = programmers_file.get_programmers_info()
    return programmers_info


def update_serial_info(serial_ports):
    """."""
    global arduino_info
    arduino_info['serial_ports'] = serial_ports
    st_menu.update_serial_menu(arduino_info)
    check_serial_selected(arduino_info)


def check_platform_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
    sel_package = sel_settings.get('package', '')
    sel_platform = sel_settings.get('platform', '')
    sel_version = sel_settings.get('version', '')

    package_infos = arduino_info.get('installed_packages', {})
    package_names = package_infos.get('names', [])
    if package_names:
        if sel_package not in package_names:
            sel_package = package_names[0]
            sel_settings.set('package', sel_package)
    else:
        sel_package = None
        sel_settings.set('package', sel_package)

    package_info = package_infos.get(sel_package, {})
    platform_infos = package_info.get('platforms', {})
    platform_names = platform_infos.get('names', [])
    if platform_names:
        if sel_platform not in platform_names:
            sel_platform = platform_names[0]
            sel_settings.set('platform', sel_platform)
    else:
        sel_platform = None
        sel_settings.set('platform', sel_platform)

    platform_info = platform_infos.get(sel_platform, {})
    versions = platform_info.get('versions', [])
    if versions:
        if sel_version not in versions:
            sel_version = versions[-1]
            sel_settings.set('version', sel_version)
    else:
        sel_version = None
        sel_settings.set('version', sel_version)


def check_board_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
    sel_board = sel_settings.get('board', '')
    board_names = arduino_info['boards'].get('names', [])
    if board_names:
        if sel_board not in board_names:
            sel_board = board_names[0]
            sel_settings.set('board', sel_board)
    else:
        sel_board = None
        sel_settings.set('board', sel_board)


def check_board_options_selected(arduino_info):
    """."""
    sel_board = arduino_info['selected'].get('board')
    board_info = arduino_info['boards'].get(sel_board, {})
    options = board_info.get('options', [])
    for option in options:
        key = 'option_%s' % option
        sel_value = arduino_info['selected'].get(key)
        items_info = board_info.get(option, {})
        value_names = items_info.get('names', [])
        if sel_value not in value_names:
            sel_value = value_names[0]
            arduino_info['selected'].set(key, sel_value)


def check_programmer_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
    sel_programmer = sel_settings.get('programmer', '')
    programmer_names = arduino_info['programmers'].get('names', [])
    if programmer_names:
        if sel_programmer not in programmer_names:
            sel_programmer = programmer_names[0]
            sel_settings.set('programmer', sel_programmer)
    else:
        sel_programmer = None
        sel_settings.set('programmer', sel_programmer)


def check_serial_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
    sel_serial = sel_settings.get('serial_port', '')
    serial_ports = arduino_info.get('serial_ports', [])
    if serial_ports:
        if serial_port not in serial_ports:
            sel_serial = serial_ports[0]
            sel_settings.set('serial_port', sel_serial)
    else:
        sel_serial = None
        sel_settings.set('serial_port', sel_serial)


def check_language_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
    sel_language = sel_settings.get('language', '')
    language_names = arduino_info['languages'].get('names', [])
    if language_names:
        if sel_language not in language_names:
            sel_language = language_names[0]
            sel_settings.set('language', sel_language)
    else:
        sel_language = None
        sel_settings.set('language', sel_language)


def on_platform_select(package_name, platform_name):
    """."""
    global arduino_info
    arduino_info['selected'].set('package', package_name)
    arduino_info['selected'].set('platform', platform_name)
    check_platform_selected(arduino_info)
    sel_version = arduino_info['selected'].get('version')
    on_version_select(sel_version)
    st_menu.update_version_menu(arduino_info)


def on_version_select(version):
    """."""
    global arduino_info
    arduino_info['selected'].set('version', version)
    boards_info = get_boards_info(arduino_info)
    arduino_info.update(boards_info)
    check_board_selected(arduino_info)
    programmers_info = get_programmers_info(arduino_info)
    arduino_info.update(programmers_info)
    check_programmer_selected(arduino_info)
    sel_board = arduino_info['selected'].get('board')
    on_board_select(sel_board)
    st_menu.update_platform_example_menu(arduino_info)
    st_menu.update_platform_library_menu(arduino_info)
    st_menu.update_board_menu(arduino_info)
    st_menu.update_programmer_menu(arduino_info)


def on_board_select(board_name):
    """."""
    global arduino_info
    arduino_info['selected'].set('board', board_name)
    check_board_options_selected(arduino_info)
    st_menu.update_board_options_menu(arduino_info)
    check_tools_deps(arduino_info)


def on_board_option_select(option, value):
    """."""
    global arduino_info
    arduino_info['selected'].set('option_%s' % option, value)


def on_programmer_select(programmer_name):
    """."""
    global arduino_info
    arduino_info['selected'].set('programmer', programmer_name)


def on_serial_select(serial_port):
    """."""
    global arduino_info
    arduino_info['selected'].set('serial_port', serial_port)


def on_language_select(language_name):
    """."""
    global arduino_info
    arduino_info['selected'].set('language', language)


def check_tools_deps(arduino_info):
    """."""
    arduino_app_path = arduino_info['arduino_app_path']
    packages_path = os.path.join(arduino_app_path, 'packages')

    platform_info = selected.get_sel_platform_info(arduino_info)
    tools_deps = platform_info.get('toolsDependencies', [])
    for tool_info in tools_deps:
        has_tool = False
        package = tool_info.get('packager', '')
        name = tool_info.get('name', '')
        version = tool_info.get('version', '')

        package_path = os.path.join(packages_path, package)
        if package and os.path.isdir(package_path):
            tools_path = os.path.join(package_path, 'tools')
            tool_path = os.path.join(tools_path, name)
            if name and os.path.isdir(tool_path):
                version_path = os.path.join(tool_path, version)
                if version and version_path:
                    has_tool = True
        if not has_tool:
            print('Must download %s %s %s' % (package, name, version))


def open_project(project_path, win):
    """."""
    exts = ['.ino', '.pde', '.cpp', '.c', '.cxx']
    prj_name = os.path.basename(project_path)

    has_prj_file = False
    for ext in exts:
        file_name = prj_name + ext
        file_path = os.path.join(project_path, file_name)
        if os.path.isfile(file_path):
            has_prj_file = True
            break

    if not has_prj_file:
        file_name = prj_name + '.ino'
        file_path = os.path.join(project_path, file_name)
    win.open_file(file_path)


def new_sketch(sketch_name, win):
    """."""
    if not sketch_name:
        msg = 'Blank'
        sublime.error_message(msg)
        return

    if sketch_name[0].isdigit():
        sketch_name = '_' + sketch_name
    sketchbook_path = arduino_info['sketchbook_path']
    sketch_path = os.path.join(sketchbook_path, sketch_name)
    if not os.path.isdir(sketch_path):
        file.check_dir(sketch_path)
        file_name = sketch_name + '.ino'
        file_path = os.path.join(sketch_path, file_name)\

        text = 'void setup()\n'
        text += '{\n'
        text += '\t\n'
        text += '}\n\n'
        text += 'void loop()\n'
        text += '{\n'
        text += '\t\n'
        text += '}\n\n'

        with open(file_path, 'w') as f:
            f.write(text)
        win.open_file(file_path)
        st_menu.update_sketchbook_menu(arduino_info)
    else:
        msg = '%s already exists.' % sketch_name
        sublime.error_message(msg)


def import_lib(view, edit, lib_path):
    """."""
    src_path = os.path.join(lib_path, 'src')
    if not os.path.isdir(src_path):
        src_path = lib_path

    incs = []
    for ext in c_file.H_EXTS:
        paths = glob.glob(src_path + '/*' + ext)
        incs += ['#incldue <%s>' % os.path.basename(p) for p in paths]
    text = '\n'.join(incs) + '\n\n'
    view.insert(edit, 0, text)


def install_platform(package, platform, version):
    """."""
    print(package, platform, version)


def build_sketch(file_path):
    """."""
    print(file_path)


def upload_sketch(file_path):
    """."""
    print(file_path)


def upload_by_programmer(file_path):
    """."""
    print(file_path)


def beautify_src(view, edit, file_path):
    """."""
    cur_file = c_file.CFile(file_path)
    if cur_file.is_cpp_file():
        beautiful_text = cur_file.get_beautified_text()
        region = sublime.Region(0, view.size())
        view.replace(edit, region, beautiful_text)


def find_in_ref(view):
    """."""
    ref_list = []
    selected_text = get_selected_text_from_view(view)
    print(selected_text)
    for ref in ref_list:
        pass
    url = 'http://arduino.cc/en/Reference/'
    sublime.run_command('open_url', {'url': url})


def get_selected_text_from_view(view):
    """."""
    selected_text = ''
    region_list = view.sel()
    for region in region_list:
        selected_region = view.word(region)
        selected_text += view.substr(selected_region)
        selected_text += '\n'
    return selected_text


def translate(text):
    """."""
    return text


def open_platform_documents():
    """."""
    platform_info = selected.get_sel_platform_info(arduino_info)
    help_info = platform_info.get('help', {})
    url = help_info.get('online', '')
    if url.startswith('http'):
        sublime.run_command('open_url', {'url': url})


def print_packages_info(arduino_info):
    """."""
    pkgs_info = arduino_info.get('packages', {})
    pkg_names = pkgs_info.get('names')
    for pkg_name in pkg_names:
        print(pkg_name)
        pkg_info = pkgs_info[pkg_name]

        platforms_info = pkg_info.get('platforms', {})
        platform_names = platforms_info.get('names')
        for platform_name in platform_names:
            platform_info = platforms_info[platform_name]
            versions = platform_info.get('versions')
            print(platform_name, versions)

        tools_info = pkg_info.get('tools', {})
        tool_names = tools_info.get('names')
        for tool_name in tool_names:
            tool_info = tools_info[tool_name]
            versions = tool_info.get('versions')
            print(tool_name, versions)


def print_boards_info(arduino_info):
    """."""
    boards_info = arduino_info.get('boards', {})
    board_names = boards_info.get('names')
    for board_name in board_names:
        print(board_name)
        board_info = boards_info[board_name]
        # generic_info = board_info.get('generic', {})
        option_names = board_info.get('options', [])
        for option_name in option_names:
            option_info = board_info[option_name]
            value_names = option_info.get('names', [])
            print(option_name, value_names)
            # for value_name in value_names:
            #     value_info = option_info.get(value_name, {})


def init():
    """."""
    global arduino_info

    # 0. init paths and settings
    app_dir_settings = get_app_dir_settings()
    arduino_dir_path = get_arduino_dir_path(app_dir_settings)
    arduino_info['arduino_app_path'] = arduino_dir_path
    sketchbook_path = get_sketchbook_path(app_dir_settings)
    arduino_info['sketchbook_path'] = sketchbook_path

    config_file_path = os.path.join(arduino_dir_path, 'config.stino-settings')
    config_settings = file.SettingsFile(config_file_path)
    if config_settings.get('extra_build_flag') is None:
        config_settings.set('extra_build_flag', '')
    arduino_info['settings'] = config_settings

    sel_file_path = os.path.join(arduino_dir_path, 'selected.stino-settings')
    sel_settings = file.SettingsFile(sel_file_path)
    arduino_info['selected'] = sel_settings

    pkgs_file_path = os.path.join(arduino_dir_path, 'packages.stino-settings')
    pkg_index_settings = file.SettingsFile(pkgs_file_path)
    arduino_info['package_index'] = pkg_index_settings
    if not arduino_info['package_index'].get('default'):
        arduino_info['package_index'].set('default', const.PACKAGE_INDEX_URL)

    # 1. init packages info
    index_files_info = get_index_files_info(arduino_dir_path)
    arduino_info.update(index_files_info)

    installed_packages_info = get_installed_packages_info(arduino_info)
    arduino_info.update(installed_packages_info)
    check_platform_selected(arduino_info)

    # 2. init board info
    arduino_info['boards'] = {}
    arduino_info['programmers'] = {}
    boards_info = get_boards_info(arduino_info)
    arduino_info.update(boards_info)
    check_board_selected(arduino_info)
    check_board_options_selected(arduino_info)

    programmers_info = get_programmers_info(arduino_info)
    arduino_info.update(programmers_info)
    check_programmer_selected(arduino_info)

    # 3. init serial
    serial_listener = serial_port.SerialListener(update_serial_info)
    serial_listener.start()

    # 4. init menus
    st_menu.update_sketchbook_menu(arduino_info)
    st_menu.update_example_menu(arduino_info)
    st_menu.update_library_menu(arduino_info)

    st_menu.update_install_platform_menu(arduino_info)
    st_menu.update_platform_menu(arduino_info)
    st_menu.update_version_menu(arduino_info)
    st_menu.update_platform_example_menu(arduino_info)
    st_menu.update_platform_library_menu(arduino_info)

    st_menu.update_board_menu(arduino_info)
    st_menu.update_board_options_menu(arduino_info)
    st_menu.update_programmer_menu(arduino_info)

    st_menu.update_language_menu(arduino_info)

arduino_info = {}
init()
