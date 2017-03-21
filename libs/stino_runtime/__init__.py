#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
import glob
import zipfile
import tarfile
import platform
import shutil
import time
import subprocess

import sublime

from base_utils import file
from base_utils import c_file
from base_utils import c_project
from base_utils import index_file
from base_utils import plain_params_file
from base_utils import default_st_dirs
from base_utils import default_arduino_dirs
from base_utils import serial_port
from base_utils import task_queue
from base_utils import task_listener
from base_utils import downloader
from base_utils import sys_info
from . import const
from . import st_menu
from . import selected
from . import st_panel

plugin_name = const.PLUGIN_NAME
_d_pattern_text = r"'-D[\S\s]*?'"
_d_pattern = re.compile(_d_pattern_text)

EXCLUDES = ['examples', 'samples', 'test']


def get_app_dir_settings():
    """."""
    global arduino_info
    dir_path = default_st_dirs.get_plugin_config_path(plugin_name)
    file_path = os.path.join(dir_path, 'app_dir.stino-settings')
    app_dir_settings = file.SettingsFile(file_path)
    arduino_info['app_dir_settings'] = app_dir_settings
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
    file.check_dir(dir_path)
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
    file.check_dir(dir_path)
    return dir_path


def get_ext_app_path(app_dir_settings):
    """."""
    ext_app_path = app_dir_settings.get('additional_app_path')
    if not isinstance(ext_app_path, str):
        ext_app_path = ''
        app_dir_settings.set('additional_app_path', '')
    return ext_app_path


def get_index_files_info(arduino_dir_path):
    """."""
    file_paths = glob.glob(arduino_dir_path + '/package*_index.json')
    index_files = index_file.PackageIndexFiles(file_paths)
    info = index_files.get_info()
    return info


def get_lib_index_files_info(arduino_dir_path):
    """."""
    file_paths = glob.glob(arduino_dir_path + '/library*_index.json')
    lib_index_files = index_file.LibIndexFiles(file_paths)
    info = lib_index_files.get_info()
    return info


def get_ext_app_pkg_info(ext_app_hardware_path):
    """."""
    pkg_info = {'platforms': {}}
    pkg_info['platforms']['names'] = []
    pkg_dir_paths = glob.glob(ext_app_hardware_path + '/*')
    pkg_dir_paths = [p for p in pkg_dir_paths if os.path.isdir(p)]
    pkg_dir_paths = [p for p in pkg_dir_paths
                     if os.path.basename(p) != 'tools']
    for pkg_dir_path in pkg_dir_paths:
        sub_pkg_name = os.path.basename(pkg_dir_path)
        pkg_info['platforms']['names'].append(sub_pkg_name)
        arch_dir_paths = glob.glob(pkg_dir_path + '/*')
        arch_dir_paths = [p for p in arch_dir_paths
                          if os.path.isdir(p)]
        arch_names = [os.path.basename(p) for p in arch_dir_paths]
        ptfm_info = {'versions': arch_names}
        for arch_name, arch_path in zip(arch_names, arch_dir_paths):
            arch_info = {'path': arch_path}
            arch_info['package'] = sub_pkg_name
            arch_info['architecture'] = arch_name
            arch_info['version'] = ''
            ptfm_info[arch_name] = arch_info
        pkg_info['platforms'][sub_pkg_name] = ptfm_info
    return pkg_info


def get_installed_packages_info(arduino_info):
    """."""
    installed_packages_info = {'installed_packages': {}}
    arduino_dir_path = arduino_info['arduino_app_path']
    ext_app_path = arduino_info['ext_app_path']
    sketchbook_path = arduino_info['sketchbook_path']

    package_names = []
    ext_app_hardware_path = os.path.join(ext_app_path, 'hardware')
    sketchbook_hardware_path = os.path.join(sketchbook_path, 'hardware')

    pkg_name = 'Arduino IDE'
    if os.path.isdir(ext_app_hardware_path):
        if pkg_name not in package_names:
            package_names.append(pkg_name)

        pkg_info = get_ext_app_pkg_info(ext_app_hardware_path)
        installed_packages_info['installed_packages'][pkg_name] = pkg_info

    pkg_name = 'Sketchbook'
    if os.path.isdir(sketchbook_path):
        if pkg_name not in package_names:
            package_names.append(pkg_name)
        pkg_info = get_ext_app_pkg_info(sketchbook_hardware_path)
        installed_packages_info['installed_packages'][pkg_name] = pkg_info

    packages_path = os.path.join(arduino_dir_path, 'packages')
    package_paths = glob.glob(packages_path + '/*')
    package_names += [os.path.basename(p) for p in package_paths]
    installed_packages_info['installed_packages']['names'] = package_names

    for package_path in package_paths:
        pkg_name = os.path.basename(package_path)
        pkg_info = {'platforms': {}}
        hardware_path = os.path.join(package_path, 'hardware')
        platform_paths = glob.glob(hardware_path + '/*')

        pkg_info['platforms']['names'] = []
        for platform_path in platform_paths:
            ptfm_arch = os.path.basename(platform_path)
            ptfm_name = selected.get_platform_name_by_arch(arduino_info,
                                                           pkg_name,
                                                           ptfm_arch)
            pkg_info['platforms']['names'].append(ptfm_name)

            version_paths = glob.glob(platform_path + '/*')
            versions = [os.path.basename(p) for p in version_paths]
            ptfm_info = {'versions': versions}
            for version, version_path in zip(versions, version_paths):
                version_info = {'path': version_path}
                version_info['package'] = pkg_name
                version_info['architecture'] = ptfm_arch
                version_info['version'] = version
                ptfm_info[version] = version_info
            pkg_info['platforms'][ptfm_name] = ptfm_info
        installed_packages_info['installed_packages'][pkg_name] = pkg_info
    return installed_packages_info


def get_boards_info(arduino_info):
    """."""
    boards_info = {'boards': {}}
    platform_path = selected.get_sel_platform_path(arduino_info)
    if platform_path:
        boards_file_path = os.path.join(platform_path, 'boards.txt')
        boards_file = plain_params_file.BoardsFile(boards_file_path)
        boards_info = boards_file.get_boards_info()
    return boards_info


def get_programmers_info(arduino_info, src='platform'):
    """."""
    programmers_info = {'programmers': {}}
    if src == 'platform':
        platform_path = selected.get_sel_platform_path(arduino_info)
    else:
        platform_path = os.path.dirname(os.path.realpath(__file__))
    if platform_path:
        progs_file_path = os.path.join(platform_path, 'programmers.txt')
        progs_file = plain_params_file.ProgrammersFile(progs_file_path)
        programmers_info = progs_file.get_programmers_info()
    return programmers_info


def combine_programmers_info(infos):
    """."""
    all_info = {'names': []}
    for info in infos:
        names = info.get('names', [])
        for name in names:
            if name not in all_info['names']:
                all_info['names'].append(name)
            name_info = info.get(name, {})
            if name_info:
                all_info[name] = name_info
    programmers_info = {'programmers': all_info}
    return programmers_info


def get_all_programmers_info(arduino_info):
    """."""
    basic_programmers_info = arduino_info.get('basic_programmers', {})
    programmers_info = \
        get_programmers_info(arduino_info,
                             src='platform').get('programmers', {})
    programmers_info = combine_programmers_info([programmers_info,
                                                 basic_programmers_info])
    return programmers_info


def update_serial_info(serial_ports):
    """."""
    global arduino_info
    arduino_info['serial_ports'] = {'names': serial_ports}
    st_menu.update_serial_menu(arduino_info)
    check_selected(arduino_info, 'serial_port')


def check_platform_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected')
    sel_package = sel_settings.get('package', '')
    sel_platform = sel_settings.get('platform', '')
    sel_version = sel_settings.get('version', '')

    packages_info = arduino_info.get('installed_packages', {})
    package_names = packages_info.get('names', [])
    if package_names:
        if sel_package not in package_names:
            sel_package = package_names[0]
            sel_settings.set('package', sel_package)
    else:
        sel_package = None
        sel_settings.set('package', sel_package)

    package_info = packages_info.get(sel_package, {})
    platforms_info = package_info.get('platforms', {})
    platform_names = platforms_info.get('names', [])
    if platform_names:
        if sel_platform not in platform_names:
            sel_platform = platform_names[0]
            sel_settings.set('platform', sel_platform)
    else:
        sel_platform = None
        sel_settings.set('platform', sel_platform)

    platform_vers_info = platforms_info.get(sel_platform, {})
    versions = platform_vers_info.get('versions', [])
    if versions:
        if sel_version not in versions:
            sel_version = versions[-1]
            sel_settings.set('version', sel_version)
    else:
        sel_version = None
        sel_settings.set('version', sel_version)


def check_selected(arduino_info, item_type):
    """."""
    if item_type == 'serial_port'and not arduino_info['init_done']:
        return
    sel_settings = arduino_info.get('selected')
    sel_item = sel_settings.get(item_type, '')
    sel_item_info = arduino_info.get('%ss' % item_type, {})
    names = sel_item_info.get('names', [])
    if names:
        if sel_item not in names:
            sel_item = names[0]
            sel_settings.set(item_type, sel_item)
    else:
        sel_item = None
        sel_settings.set(item_type, sel_item)


def check_board_options_selected(arduino_info):
    """."""
    sel_board = arduino_info['selected'].get('board')
    board_info = arduino_info['boards'].get(sel_board, {})
    options = board_info.get('options', [])
    for option in options:
        key = 'option_%s' % option
        sel_value_name = arduino_info['selected'].get(key)
        values_info = board_info.get(option, {})
        value_names = values_info.get('names', [])
        if sel_value_name not in value_names:
            sel_value_name = value_names[0]
            arduino_info['selected'].set(key, sel_value_name)


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
    check_selected(arduino_info, 'board')
    programmers_info = get_all_programmers_info(arduino_info)
    arduino_info.update(programmers_info)
    check_selected(arduino_info, 'programmer')
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
    check_platform_dep()


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
    arduino_info['selected'].set('language', language_name)


def unzip(zip_path, target_dir_path):
    """."""
    is_ok = True
    if zip_path.endswith('.zip'):
        with zipfile.ZipFile(zip_path, 'r') as f:
            names = f.namelist()
            try:
                f.extractall(target_dir_path)
            except (IOError, zipfile.FileNotFoundError) as e:
                message_queue.put('%s' % e)
                is_ok = False
    elif zip_path.endswith('.gz') or zip_path.endswith('.bz2'):
        with tarfile.open(zip_path, 'r') as f:
            names = f.getnames()
            try:
                f.extractall(target_dir_path)
            except (IOError, tarfile.FileNotFoundError) as e:
                message_queue.put('%s' % e)
                is_ok = False
    return is_ok, names


def download_lib(url):
    """."""
    if url:
        arduino_app_path = arduino_info['arduino_app_path']
        sketchbook_path = arduino_info['sketchbook_path']
        libs_path = os.path.join(sketchbook_path, 'libraries')
        if not os.path.isdir(libs_path):
            os.makedirs(libs_path)
        staging_path = os.path.join(arduino_app_path, 'staging')
        down_path = os.path.join(staging_path, 'libraries')
        msg = '[%s] Waiting for download...' % url
        message_queue.put(msg)
        is_done = downloader.download(url, down_path, message_queue.put)
        if is_done:
            basename = os.path.basename(url)
            basename = os.path.splitext(basename)[0]
            unzip_lib_path = os.path.join(libs_path, basename)
            if '-' in basename:
                basename = basename.split('-')[0]
            lib_path = os.path.join(libs_path, basename)
            if os.path.isdir(lib_path):
                shutil.rmtree(lib_path)

            msg = 'Installation started.'
            message_queue.put(msg)

            zip_name = os.path.basename(url)
            zip_path = os.path.join(down_path, zip_name)
            is_ok, _ = unzip(zip_path, libs_path)
            if is_ok:
                if lib_path != unzip_lib_path:
                    os.rename(unzip_lib_path, lib_path)
                msg = 'Installation completed.'
            else:
                msg = 'Unzip %s failed.' % lib_path
            message_queue.put(msg)
            st_menu.update_library_menu(arduino_info)


def download_platform_tool(down_info):
    """."""
    global arduino_info
    down_type = down_info.get('type', '')
    url = down_info.get('url', '')
    package = down_info.get('package', '')
    name = down_info.get('name', '')
    version = down_info.get('version', '')

    if down_type and url and package and name and version:
        arduino_app_path = arduino_info['arduino_app_path']
        packages_path = os.path.join(arduino_app_path, 'packages')
        staging_path = os.path.join(arduino_app_path, 'staging')
        down_path = os.path.join(staging_path, 'packages')

        package_path = os.path.join(packages_path, package)
        if down_type == 'platform':
            sub_path = os.path.join(package_path, 'hardware')
            packages_info = arduino_info.get('packages', {})
            package_info = packages_info.get(package, {})
            platforms_info = package_info.get('platforms', {})
            platform_info = platforms_info.get(name, {})
            version_info = platform_info.get(version, {})
            name = version_info.get('architecture', name)
        elif down_type == 'tool':
            sub_path = os.path.join(package_path, 'tools')
        name_path = os.path.join(sub_path, name)
        version_path = os.path.join(name_path, version)

        if not os.path.isdir(version_path):
            msg = '[%s] Waiting for download...' % url
            message_queue.put(msg)
            is_done = downloader.download(url, down_path, message_queue.put)

            if is_done:
                msg = '[%s] %s %s: ' % (package, name, version)
                msg += 'Installation started.'
                message_queue.put(msg)
                if not os.path.isdir(name_path):
                    os.makedirs(name_path)

                zip_name = os.path.basename(url)
                zip_path = os.path.join(down_path, zip_name)
                is_ok, names = unzip(zip_path, name_path)

                if is_ok:
                    if names:
                        dir_name = names[0]
                        if '/' in dir_name:
                            dir_name = dir_name.split('/')[0]
                        new_path = os.path.join(name_path, dir_name)
                        if os.path.exists(version_path):
                            move_path = os.path.join(new_path, version)
                            shutil.move(version_path, move_path)
                        os.rename(new_path, version_path)

                    msg = '[%s] %s %s: ' % (package, name, version)
                    msg += 'Installation completed.'
                else:
                    msg = 'Unzip %s failed.' % zip_path
                message_queue.put(msg)

        if down_type == 'platform':
            installed_packages_info = \
                get_installed_packages_info(arduino_info)
            arduino_info.update(installed_packages_info)
            st_menu.update_platform_menu(arduino_info)
            st_menu.update_version_menu(arduino_info)

            build_platform_info = \
                selected.get_build_platform_info(arduino_info)
            check_tools_deps(build_platform_info)


def check_platform_dep():
    """."""
    is_ready = True
    build_platform_info = selected.get_build_platform_info(arduino_info)
    url = build_platform_info.get('url', '')
    platform_path = build_platform_info.get('path', '')

    if not platform_path:
        is_ready = False
        if url:
            is_ready = False
            package = build_platform_info.get('package', '')
            name = build_platform_info.get('name', '')
            version = build_platform_info.get('version', '')

            down_info = {}
            down_info['type'] = 'platform'
            down_info['package'] = package
            down_info['name'] = name
            down_info['version'] = version
            down_info['url'] = url
            platform_tool_downloader.put(down_info)

    if is_ready:
        is_ready = check_tools_deps(build_platform_info)
    return is_ready


def check_tools_deps(platform_info):
    """."""
    is_ready = True

    tools_info = selected.get_dep_tools_info(arduino_info, platform_info)
    tool_names = tools_info.get('names', [])
    for name in tool_names:
        has_tool = False
        tool_info = tools_info.get(name, {})
        if tool_info.get('path', ''):
            has_tool = True

        if not has_tool:
            is_ready = False

            package = tool_info.get('packager', '')
            version = tool_info.get('version', '')

            packages_info = arduino_info.get('packages', {})
            package_info = packages_info.get(package, {})
            down_tools_info = package_info.get('tools', {})
            down_tool_info = down_tools_info.get(name, {})
            version_info = down_tool_info.get(version, {})
            systems_info = version_info.get('systems', [])
            for system_info in systems_info:
                host = system_info.get('host', '')
                url = system_info.get('url', '')

                if sys_info.get_os_name() == 'windows':
                    id_text = '-mingw32'
                elif sys_info.get_os_name() == 'osx':
                    id_text = '-apple'
                elif sys_info.get_os_name() == 'linux':
                    id_text = '%s-' % platform.machine()

                go_down = False
                if id_text in host:
                    go_down = True
                    break

            if go_down:
                down_info = {}
                down_info['type'] = 'tool'
                down_info['package'] = package
                down_info['name'] = name
                down_info['version'] = version
                down_info['url'] = url
                platform_tool_downloader.put(down_info)
    return is_ready


def open_project(project_path, win):
    """."""
    prj_name = os.path.basename(project_path)

    has_prj_file = False
    for ext in c_file.INOC_EXTS:
        file_name = prj_name + ext
        file_path = os.path.join(project_path, file_name)
        if os.path.isfile(file_path):
            has_prj_file = True
            break

    if has_prj_file:
        win.open_file(file_path)
    else:
        paths = glob.glob(project_path + '/*')
        file_paths = [p for p in paths if os.path.isfile(p)]
        for file_path in file_paths:
            ext = os.path.splitext(file_path)[-1]
            if ext in c_file.INOC_EXTS:
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


def get_real_lib_path(lib_path):
    """."""
    sub_dirs = ['src', 'include']
    for sub_dir in sub_dirs:
        path = os.path.join(lib_path, sub_dir)
        if os.path.isdir(path):
            lib_path = path
            break
    return lib_path


def import_lib(view, edit, lib_path):
    """."""
    src_path = get_real_lib_path(lib_path)

    incs = []
    for ext in c_file.H_EXTS:
        paths = glob.glob(src_path + '/*' + ext)
        incs += ['#incldue <%s>' % os.path.basename(p) for p in paths]
    text = '\n'.join(incs) + '\n\n'
    view.insert(edit, 0, text)


def install_library(category, name, version):
    """."""
    libs_info = arduino_info.get('libraries', {})
    cat_info = libs_info.get(category, {})
    name_info = cat_info.get(name, {})
    ver_info = name_info.get(version, {})
    url = ver_info.get('url', '')
    basename = os.path.basename(url)
    basename = os.path.splitext(basename)[0]
    if '-' in basename:
        basename = basename.split('-')[0]
    sketchbook_path = arduino_info['sketchbook_path']
    libs_path = os.path.join(sketchbook_path, 'libraries')
    lib_path = os.path.join(libs_path, basename)
    if os.path.isdir(lib_path):
        msg = '%s already exists. Continue?' % basename
        result = sublime.yes_no_cancel_dialog(msg)
        if result == sublime.DIALOG_YES:
            lib_downloader.put(url)
    else:
        lib_downloader.put(url)


def install_platform(package, platform, version):
    """."""
    msg = 'Download [%s] %s %s?' % (package, platform, version)
    result = sublime.yes_no_cancel_dialog(msg)
    if result == sublime.DIALOG_YES:
        packages_info = arduino_info.get('packages', {})
        package_info = packages_info.get(package, {})
        platforms_info = package_info.get('platforms', {})
        platform_info = platforms_info.get(platform, {})
        version_info = platform_info.get(version)
        url = version_info.get('url', '')

        down_info = {}
        down_info['type'] = 'platform'
        down_info['package'] = package
        down_info['name'] = platform
        down_info['version'] = version
        down_info['url'] = url
        platform_tool_downloader.put(down_info)


def import_avr_platform(ide_path=''):
    """."""
    global arduino_info
    is_ide = False
    if os.path.isdir(ide_path):
        arduino_app_path = arduino_info['arduino_app_path']
        sketchbook_path = arduino_info['sketchbook_path']

        sketch_examples_path = os.path.join(sketchbook_path, 'examples')
        sketch_libraries_path = os.path.join(sketchbook_path, 'libraries')

        examples_path = os.path.join(ide_path, 'examples')
        if os.path.isdir(examples_path):
            paths = glob.glob(examples_path + '/*')
            paths = [p for p in paths if os.path.isdir(p)]
            for path in paths:
                name = os.path.basename(path)
                target_path = os.path.join(sketch_examples_path, name)
                if not os.path.exists(target_path):
                    shutil.copytree(path, target_path)

        libraries_path = os.path.join(ide_path, 'libraries')
        if os.path.isdir(libraries_path):
            paths = glob.glob(libraries_path + '/*')
            paths = [p for p in paths if os.path.isdir(p)]
            for path in paths:
                name = os.path.basename(path)
                target_path = os.path.join(sketch_libraries_path, name)
                if not os.path.exists(target_path):
                    shutil.copytree(path, target_path)

        hardware_path = os.path.join(ide_path, 'hardware')
        index_file_path = os.path.join(hardware_path,
                                       'package_index_bundled.json')
        if os.path.isfile(index_file_path):
            index_files = index_file.PackageIndexFiles([index_file_path])
            info = index_files.get_info()
            packages_info = info.get('packages', {})
            package_names = packages_info.get('names', [])
            if package_names:
                package_name = package_names[0]
                package_info = packages_info.get(package_name, {})
                platforms_info = package_info.get('platforms', {})
                platform_names = platforms_info.get('names', [])
                if platform_names:
                    platform_name = platform_names[0]
                    platform_arch = platforms_info.get('arches')[0]
                    platform_info = platforms_info.get(platform_name, {})
                    versions = platform_info.get('versions', [])
                    if versions:
                        version = versions[0]
                        package_path = os.path.join(hardware_path,
                                                    package_name)
                        platform_path = os.path.join(package_path,
                                                     platform_arch)

                        if os.path.isdir(platform_path):
                            is_ide = True

                            target_path = os.path.join(arduino_app_path,
                                                       'packages')
                            target_path = os.path.join(target_path,
                                                       package_name)
                            target_path = os.path.join(target_path,
                                                       'hardware')
                            target_path = os.path.join(target_path,
                                                       platform_arch)
                            target_path = os.path.join(target_path,
                                                       version)
                            if not os.path.isdir(target_path):
                                shutil.copytree(platform_path, target_path)
                                msg = 'Importing Arduino IDE finished.'
                                installed_packages_info = \
                                    get_installed_packages_info(arduino_info)
                                arduino_info.update(installed_packages_info)
                                st_menu.update_platform_menu(arduino_info)
                                st_menu.update_version_menu(arduino_info)

                            else:
                                msg = '[%s] %s %s ' % (package_name,
                                                       platform_name,
                                                       version)
                                msg += 'exists.'
                            message_queue.put(msg)
                            check_platform_dep()
    if not is_ide:
        msg = '[Error] %s is not Arduino IDE.' % ide_path
        message_queue.put(msg)


def find_dirs(path, dir_name):
    """."""
    include_dirs = []
    name = os.path.basename(path)
    if name == dir_name:
        include_dirs.append(path)
    else:
        sub_paths = glob.glob(path + '/*')
        sub_paths = [p for p in sub_paths if os.path.isdir(p)]
        for sub_path in sub_paths:
            include_dirs += find_dirs(sub_path, dir_name)
    return include_dirs


def get_tool_dirs(dir_name):
    """Find include dirs."""
    tool_include_dirs = []
    platform_info = selected.get_sel_platform_info(arduino_info)
    tools_info = selected.get_dep_tools_info(arduino_info, platform_info)
    tool_names = tools_info.get('names', [])
    for name in tool_names:
        tool_info = tools_info.get(name, {})
        path = tool_info.get('path', '')
        if path:
            tool_include_dirs += find_dirs(path, dir_name)
    return tool_include_dirs


def get_h_path_info(project):
    """."""
    h_path_info = {}
    get_h_info = c_project.get_file_info_of_extensions

    sketchbook_path = arduino_info['sketchbook_path']
    ext_app_path = arduino_info['ext_app_path']
    platform_path = selected.get_sel_platform_path(arduino_info)

    paths = []
    if ext_app_path:
        paths.append(ext_app_path)
    if platform_path:
        paths.append(platform_path)
    paths.append(sketchbook_path)

    for path in paths:
        libraries_path = os.path.join(path, 'libraries')
        lib_paths = glob.glob(libraries_path + '/*')
        lib_paths = [p for p in lib_paths if os.path.isdir(p)]
        for lib_path in lib_paths:
            src_path = get_real_lib_path(lib_path)

            info = get_h_info(src_path, c_file.H_EXTS, 'recursion', EXCLUDES)
            h_path_info.update(info)

    if project.is_arduino_project():
        core_src_path = selected.get_build_core_src_path(arduino_info)
        variant_path = selected.get_build_variant_path(arduino_info)
        src_paths = [core_src_path, variant_path]
        for src_path in src_paths:
            if src_path:
                info = get_h_info(src_path, c_file.H_EXTS,
                                  'recursion', EXCLUDES)
                h_path_info.update(info)

    info = get_h_info(project.get_path(), c_file.H_EXTS, 'recursion', EXCLUDES)
    h_path_info.update(info)
    return h_path_info


def get_dep_cpps(dir_paths, h_path_info, used_cpps, used_headers, used_dirs):
    """."""
    for dir_path in dir_paths:
        if dir_path not in used_dirs:
            used_dirs.append(dir_path)

            parent_path = os.path.dirname(dir_path)
            parent_name = os.path.basename(parent_path)
            if parent_name == 'build':
                prj_name = os.path.basename(dir_path)
                ino_cpp_name = prj_name + '.ino.cpp'
                ino_cpp_path = os.path.join(dir_path, ino_cpp_name)
                h_paths = []
                cpp_paths = [ino_cpp_path]
            else:
                h_paths = \
                    c_project.list_files_of_extensions(dir_path, c_file.H_EXTS)
                cpp_paths = \
                    c_project.list_files_of_extensions(dir_path,
                                                       c_file.CC_EXTS)

            unused_src_paths = []
            for h_path in h_paths:
                header = os.path.basename(h_path)
                if header not in used_headers:
                    used_headers.append(header)
                    unused_src_paths.append(h_path)
            for cpp_path in cpp_paths:
                if cpp_path not in used_cpps:
                    used_cpps.append(cpp_path)
                    unused_src_paths.append(cpp_path)

            sub_dir_paths = []
            for src_path in unused_src_paths:
                f = c_file.CFile(src_path)
                headers = f.list_inclde_headers()
                for header in headers:
                    if '/' in header:
                        header = header.split('/')[-1]
                    if header in h_path_info:
                        dir_path = h_path_info.get(header)
                        if dir_path not in sub_dir_paths:
                            if dir_path not in used_dirs:
                                sub_dir_paths.append(dir_path)

            used_cpps, used_headers, used_dirs = \
                get_dep_cpps(sub_dir_paths, h_path_info, used_cpps,
                             used_headers, used_dirs)
    return used_cpps, used_headers, used_dirs


def is_modified(file_path, info):
    """."""
    state = False
    mtime = os.path.getmtime(file_path)
    last_mtime = info.get(file_path)
    if mtime and mtime != last_mtime:
        state = True
    return state


def get_hooks_cmds(cmds_info, pattern_key):
    """."""
    keys = []
    cmds = []
    msgs = []
    pattern_key = 'recipe.hooks.' + pattern_key
    for key in cmds_info:
        if key.startswith('recipe.hooks.') and key.endswith('.pattern'):
            if pattern_key in key:
                keys.append(key)
    keys.sort()
    for key in keys:
        cmd = cmds_info.get(key, '')
        cmds.append(cmd)
        msgs.append('')
    return cmds, msgs


def get_build_cmds(cmds_info, prj_build_path, all_src_paths):
    """."""
    cmds = []
    msgs = []

    if not all_src_paths:
        return cmds, msgs

    is_full_build = bool(arduino_info['settings'].get('full_build'))
    last_build_path = os.path.join(prj_build_path,
                                   'last_build.stino-settings')
    last_build_info = file.SettingsFile(last_build_path)
    prj_name = os.path.basename(prj_build_path)
    core_a_path = os.path.join(prj_build_path, 'core.a')

    last_package = last_build_info.get('package', '')
    last_platform = last_build_info.get('platform', '')
    last_version = last_build_info.get('version', '')
    last_board = last_build_info.get('board', '')

    arduino_sel = arduino_info['selected']
    sel_package = arduino_sel.get('package', '')
    sel_platform = arduino_sel.get('platform', '')
    sel_version = arduino_sel.get('version', '')
    sel_board = arduino_sel.get('board', '')
    sel_board_options = selected.get_sel_board_options(arduino_info)

    if not is_full_build:
        if sel_package != last_package:
            is_full_build = True
        elif sel_platform != last_platform:
            is_full_build = True
        elif sel_version != last_version:
            is_full_build = True
        elif sel_board != last_board:
            is_full_build = True
        else:
            for option in sel_board_options:
                key = 'option_%s' % option
                sel_option = arduino_sel.get(key, '')
                last_option = last_build_info.get(key, '')
                if sel_option != last_option:
                    is_full_build = True

    obj_paths = []
    src_paths = all_src_paths[::-1]
    for src_path in src_paths:
        src_name = os.path.basename(src_path)
        obj_name = src_name + '.o'
        obj_path = os.path.join(prj_build_path, obj_name)
        obj_path = obj_path.replace('\\', '/')
        obj_paths.append(obj_path)

    build_src_paths = []
    build_obj_paths = []

    libs_changed = False
    need_gen_bins = False

    if is_full_build:
        build_src_paths = src_paths
        build_obj_paths = obj_paths
        libs_changed = True
        need_gen_bins = True
    else:
        need_compile = False
        if is_modified(src_paths[0], last_build_info):
            need_compile = True
        elif not os.path.isfile(obj_paths[0]):
            need_compile = True

        if need_compile:
            build_src_paths.append(src_paths[0])
            build_obj_paths.append(obj_paths[0])
            need_gen_bins = True

        for src_path, obj_path in zip(src_paths[1:], obj_paths[1:]):
            need_compile = False
            if is_modified(src_path, last_build_info):
                need_compile = True
            elif not os.path.isfile(obj_path):
                need_compile = True
            if need_compile:
                libs_changed = True
                build_src_paths.append(src_path)
                build_obj_paths.append(obj_path)

    if libs_changed:
        need_gen_bins = True
        if os.path.isfile(core_a_path):
            os.remove(core_a_path)

    #########################
    if build_src_paths:
        sketch_prebuild_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                     'sketch.prebuild')
        cmds += sketch_prebuild_cmds
        msgs += _msgs

    for src_path, obj_path in zip(build_src_paths, build_obj_paths):
        src_ext = os.path.splitext(src_path)[-1]
        if src_ext in c_file.CPP_EXTS or src_ext in c_file.INO_EXTS:
            cmd = cmds_info.get('recipe.cpp.o.pattern', '')
        elif src_ext in c_file.C_EXTS:
            cmd = cmds_info.get('recipe.c.o.pattern', '')
        elif src_ext in c_file.S_EXTS:
            cmd = cmds_info.get('recipe.S.o.pattern', '')
        elif not src_ext:
            cmd = cmds_info.get('recipe.cpp.o.pattern', '')
        else:
            cmd = ''
        cmd = cmd.replace('{source_file}', src_path)
        cmd = cmd.replace('{object_file}', obj_path)
        msg = 'Compiling %s...' % os.path.basename(src_path)
        cmds.append(cmd)
        msgs.append(msg)

    if build_src_paths:
        sketch_postbuild_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                      'sketch.postbuild')
        cmds += sketch_postbuild_cmds
        msgs += _msgs

    if not os.path.isfile(core_a_path):
        msg = 'Linking everything together...'
        msgs.append(msg)

        linking_prelink_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                     'linking.prelink')
        cmds += linking_prelink_cmds
        msgs += _msgs

        cmd_pattern = cmds_info.get('recipe.ar.pattern', '')
        if '/core/' in cmd_pattern:
            cmd_pattern = cmd_pattern.replace('core/', '')
        for obj_path in obj_paths[1:]:
            cmd = cmd_pattern.replace('{object_file}', obj_path)
            cmds.append(cmd)
            msgs.append('')
        msgs.pop()

        linking_postlink_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                      'linking.postlink')
        cmds += linking_postlink_cmds
        msgs += _msgs

    out_file_name = cmds_info.get('recipe.output.save_file', '')
    if out_file_name:
        bin_ext = out_file_name[-4:]
    else:
        bin_ext = '.bin'

    elf_file_name = prj_name + '.elf'
    bin_file_name = prj_name + bin_ext
    elf_file_path = os.path.join(prj_build_path, elf_file_name)
    bin_file_path = os.path.join(prj_build_path, bin_file_name)

    if not (os.path.isfile(elf_file_path) and os.path.isfile(bin_file_path)):
        need_gen_bins = True

    msg = 'Creating binary files...'
    msgs.append(msg)
    if need_gen_bins:
        exts = ['.eep', '.hex', '.bin']
        bin_file_paths = c_project.list_files_of_extensions(prj_build_path,
                                                            exts)
        for bin_file_path in bin_file_paths:
            os.remove(bin_file_path)

        cmd_pattern = cmds_info.get('recipe.c.combine.pattern', '')
        cmd = cmd_pattern.replace('{object_files}', '"%s"' % obj_paths[0])
        cmds.append(cmd)
        msgs.append('')

        bin_keys = ['recipe.objcopy.eep.pattern']
        for key in cmds_info:
            if key.startswith('recipe.objcopy.') and key.endswith('.pattern'):
                if '.eep.' not in key and key not in bin_keys:
                    bin_keys.append(key)

        objcopy_preobjcopy_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                        'objcopy.preobjcopy')
        cmds += objcopy_preobjcopy_cmds
        msgs += _msgs

        for key in bin_keys:
            cmd = cmds_info.get(key, '')
            if cmd:
                cmds.append(cmd)
                msgs.append('')
        msgs.pop()

        objcopy_postobjcopy_cmds, _msgs = get_hooks_cmds(cmds_info,
                                                         'objcopy.postobjcopy')
        cmds += objcopy_postobjcopy_cmds
        msgs += _msgs

    postbuild_cmds, _msgs = get_hooks_cmds(cmds_info, 'postbuild')
    cmds += postbuild_cmds
    msgs += _msgs

    last_build_info.set('package', sel_package)
    last_build_info.set('platform', sel_platform)
    last_build_info.set('version', sel_version)
    last_build_info.set('board', sel_board)
    for option in sel_board_options:
        key = 'option_%s' % option
        sel_option = arduino_sel.get(key, '')
        last_build_info.set(key, sel_option)
    for src_path in src_paths:
        mtime = os.path.getmtime(src_path)
        last_build_info.set(src_path, mtime)
    return cmds, msgs


def run_command(cmd):
    """."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=True)
    result = proc.communicate()
    return_code = proc.returncode
    stdout = result[0].decode(sys_info.get_sys_encoding())
    stderr = result[1].decode(sys_info.get_sys_encoding())
    stdout = stdout.replace('\r', '')
    stderr = stderr.replace('\r', '')
    return return_code, stdout, stderr


def handle_build_error_messages(error_msg):
    """."""
    message_queue.put(error_msg)
    print(error_msg)


def run_build_command(percent, cmd, msg):
    """."""
    is_ok = True
    if cmd:
        cmd = cmd.replace('\\', '/')

        texts = _d_pattern.findall(cmd)
        for text in texts:
            key, value = text[1:-1].split('=')
            key = key.strip()
            value = value.strip().replace('"', '\\"')
            new_text = key + '="' + value + '"'
            cmd = cmd.replace(text, new_text)

        if msg:
            msg = '[%.1f%%] %s' % (percent, msg)
            message_queue.put(msg)
        return_code, stdout, stderr = run_command(cmd)
        verbose_build = bool(arduino_info['settings'].get('verbose_build'))
        if verbose_build:
            message_queue.put(cmd.replace('\\', '/'))
            if stdout:
                message_queue.put(stdout.replace('\r', ''))
        if stderr:
            handle_build_error_messages(stderr.replace('\r', ''))
        if return_code != 0:
            is_ok = False
    return is_ok


def run_upload_command(cmd):
    """."""
    is_ok = True
    if cmd:
        cmd = cmd.replace('\\', '/')
        return_code, stdout, stderr = run_command(cmd)
        verbose_upload = bool(arduino_info['settings'].get('verbose_upload'))
        if verbose_upload:
            message_queue.put(cmd.replace('\\', '/'))

        if stdout:
            message_queue.put(stdout)
        if stderr:
            message_queue.put(stderr)
        if return_code != 0:
            is_ok = False
    return is_ok


def run_build_commands(cmds, msgs):
    """."""
    is_ok = True
    if not cmds:
        is_ok = False
    else:
        n = 0

        non_blank_msgs = [m for m in msgs if m]
        total = len(non_blank_msgs)
        for cmd, msg in zip(cmds, msgs):
            if msg:
                n += 1
                percent = n / total * 100
            is_ok = run_build_command(percent, cmd, msg)
            if not is_ok:
                break
    return is_ok


def run_bootloader_cmds(cmds):
    """."""
    is_ok = True
    for cmd in cmds:
        cmd = cmd.replace('\\', '/')
        return_code, stdout, stderr = run_command(cmd)
        if stdout:
            message_queue.put(stdout)
        if stderr:
            message_queue.put(stderr)

        if return_code != 0:
            is_ok = False
            break
    return is_ok


def regular_numner(num):
    """."""
    txt = str(num)
    regular_num = ''
    for index, char in enumerate(txt[::-1]):
        regular_num += char
        if (index + 1) % 3 == 0 and index + 1 != len(txt):
            regular_num += ','
    regular_num = regular_num[::-1]
    return regular_num


def run_size_command(cmd, regex_info):
    """."""
    if cmd:
        cmd = cmd.replace('\\', '/')
        return_code, stdout, stderr = run_command(cmd)
        if stdout:
            board_info = selected.get_sel_board_info(arduino_info)
            size_total = int(board_info.get('upload.maximum_size', '253952'))
            size_data_total = int(board_info.get('upload.maximum_data_size',
                                                 '10000'))

            size_regex = regex_info.get('recipe.size.regex', '')
            if size_regex:
                pattern = re.compile(size_regex, re.M)
                result = pattern.findall(stdout)
                if result:
                    try:
                        int(result[0])
                    except TypeError:
                        result = result[0][:2]
                    size = sum(int(n) for n in result)
                    size_percent = size / size_total * 100

                    size = regular_numner(size)
                    size_total = regular_numner(size_total)
                    size_percent = '%.1f' % size_percent
                    text = 'Sketch uses '
                    text += '%s bytes (%s%%) ' % (size, size_percent)
                    text += 'of program storage space. '
                    text += 'Maximum is %s bytes.' % size_total
                    message_queue.put(text)

            data_regex = regex_info.get('recipe.size.regex.data', '')
            if data_regex:
                pattern = re.compile(data_regex, re.M)
                result = pattern.findall(stdout)
                if result:
                    try:
                        int(result[0])
                    except TypeError:
                        result = result[0][1:]
                size_data = sum(int(n) for n in result)
                size_data_percent = size_data / size_data_total * 100
                size_data_remain = size_data_total - size_data

                size_data = regular_numner(size_data)
                size_data_remain = regular_numner(size_data_remain)
                size_data_total = regular_numner(size_data_total)
                size_data_percent = '%.1f' % size_data_percent
                text = 'Global variables use '
                text += '%s bytes (%s%%) ' % (size_data, size_data_percent)
                text += 'of dynamic memory, leaving '
                text += '%s bytes for local variables. ' % size_data_remain
                text += 'Maximum is %s bytes.' % size_data_total
                message_queue.put(text)

            eeprom_regex = regex_info.get('recipe.size.regex.eeprom', '')
            if eeprom_regex:
                pattern = re.compile(eeprom_regex, re.M)
                result = pattern.findall(stdout)
                if result:
                    message_queue.put(result)


def save_project_files(project_path):
    """."""
    project_path = project_path.replace('\\', '/')
    wins = sublime.windows()
    for win in wins:
        views = win.views()
        for view in views:
            file_path = view.file_name()
            if file_path:
                file_path = file_path.replace('\\', '/')
                if project_path in file_path:
                    view.run_command('save')


def build_sketch(build_info={}):
    """."""
    if not build_info:
        return

    arduino_sel = arduino_info['selected']
    sel_package = arduino_sel.get('package', '')
    sel_platform = arduino_sel.get('platform', '')
    sel_version = arduino_sel.get('version', '')
    sel_board = arduino_sel.get('board', '')

    project_path = build_info.get('path')
    upload_mode = build_info.get('upload_mode', '')

    save_before_build = arduino_info['settings'].get('save_before_build', True)
    if save_before_build:
        save_project_files(project_path)

    is_ready = True
    if not (sel_package and sel_platform and sel_version and sel_board):
        is_ready = False
    else:
        sel_board_options = selected.get_sel_board_options(arduino_info)
        for option in sel_board_options:
            key = 'option_%s' % option
            sel_option = arduino_sel.get(key, '')
            if not sel_option:
                is_ready = False
    if not is_ready:
        return

    msg = '[Build] %s...' % project_path
    message_queue.put(msg)
    msg = '[Step 1] Check Toolchain.'
    message_queue.put(msg)

    is_ready = check_platform_dep()
    if not is_ready:
        return

    msg = '[Step 2] Find all source files.'
    message_queue.put(msg)
    arduino_app_path = arduino_info['arduino_app_path']
    build_dir_path = os.path.join(arduino_app_path, 'build')

    prj = c_project.CProject(project_path, build_dir_path)
    prj_build_path = prj.get_build_path()

    prj_src_dir_paths = []
    if prj.is_arduino_project():
        prj.gen_arduino_tmp_file()
        prj_src_dir_paths.append(prj.get_build_path())
    prj_src_dir_paths.append(prj.get_path())

    if prj.is_arduino_project():
        core_src_path = selected.get_build_core_src_path(arduino_info)
        variant_path = selected.get_build_variant_path(arduino_info)
        prj_src_dir_paths.append(core_src_path)
        prj_src_dir_paths.append(variant_path)

    all_src_paths = []
    used_headers = []
    tool_include_dirs = get_tool_dirs('include')

    h_path_info = get_h_path_info(prj)
    all_src_paths, used_headers, dep_dirs = \
        get_dep_cpps(prj_src_dir_paths, h_path_info, all_src_paths,
                     used_headers, tool_include_dirs)
    all_src_paths = [p.replace('\\', '/') for p in all_src_paths]

    include_dirs = [p.replace('\\', '/') for p in dep_dirs]
    arduino_info['include_paths'] = include_dirs

    cmds_info = selected.get_build_commands_info(arduino_info, prj)
    cmds, msgs = get_build_cmds(cmds_info, prj_build_path, all_src_paths)

    msg = '[Step 3] Start building.'
    message_queue.put(msg)
    is_ok = run_build_commands(cmds, msgs)
    if not is_ok:
        message_queue.put('[Build] Error occurred.')
        return

    arduino_info['settings'].set('full_build', False)
    size_cmd = cmds_info.get('recipe.size.pattern', '')

    regex_info = {}
    regex_keys = ['recipe.size.regex']
    regex_keys.append('recipe.size.regex.data')
    regex_keys.append('recipe.size.regex.eeprom')
    for key in regex_keys:
        regex = cmds_info.get(key, '')
        if regex:
            regex_info[key] = regex
    run_size_command(size_cmd, regex_info)

    if upload_mode:
        upload_cmd = selected.get_upload_command(arduino_info, prj,
                                                 upload_mode)
        sketch_uploader.put(upload_cmd)


def upload_sketch(upload_cmd=''):
    """."""
    if upload_cmd:
        message_queue.put('[Upload]...')
        serial_listener.stop()
        time.sleep(0.25)

        upload_port = arduino_info['selected'].get('serial_port', '')
        serial_file = serial_port.get_serial_file(upload_port)

        board_info = selected.get_sel_board_info(arduino_info)
        do_touch = serial_port.check_do_touch(board_info)
        do_reset = serial_port.checke_do_reset(board_info)
        new_upload_port = serial_port.prepare_upload_port(upload_port,
                                                          do_touch, do_reset)
        if new_upload_port != upload_port:
            new_serial_file = serial_port.get_serial_file(new_upload_port)
            upload_cmd = upload_cmd.replace(upload_port, new_upload_port)
            upload_cmd = upload_cmd.replace(serial_file, new_serial_file)

        is_ok = run_upload_command(upload_cmd)
        if is_ok and do_touch:
            serial_port.restore_serial_port(upload_port, 9600)

        time.sleep(0.25)
        serial_listener.start()


def burn_bootloader():
    """."""
    cmds = selected.get_bootloader_commands(arduino_info)
    run_bootloader_cmds(cmds)


def beautify_src(view, edit, file_path):
    """."""
    cur_file = c_file.CFile(file_path)
    if cur_file.is_cpp_file():
        beautiful_text = cur_file.get_beautified_text()
        region = sublime.Region(0, view.size())
        view.replace(edit, region, beautiful_text)


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


def check_pkgs():
    """."""
    global arduino_info
    is_changed = False
    arduino_dir_path = arduino_info['arduino_app_path']
    for key in arduino_info['package_index'].get_keys():
        url = arduino_info['package_index'].get(key)
        remote_etag = downloader.get_remote_etag(url)
        if remote_etag:
            local_etag = arduino_info['etags'].get(key)
            if remote_etag and remote_etag != local_etag:
                is_done = downloader.download(url, arduino_dir_path,
                                              message_queue.put,
                                              mode='replace')
                if is_done:
                    arduino_info['etags'].set(key, remote_etag)
                    is_changed = True
    if is_changed:
        index_files_info = get_index_files_info(arduino_dir_path)
        arduino_info.update(index_files_info)
        lib_index_files_info = get_lib_index_files_info(arduino_dir_path)
        arduino_info.update(lib_index_files_info)
        st_menu.update_install_platform_menu(arduino_info)
        st_menu.update_install_library_menu(arduino_info)


def init_app_dir_settings():
    """."""
    global arduino_info
    app_dir_settings = get_app_dir_settings()
    arduino_info['app_dir_settings'] = app_dir_settings


def init_ardunio_app_path():
    """."""
    global arduino_info
    app_dir_settings = arduino_info.get('app_dir_settings')
    arduino_app_path = get_arduino_dir_path(app_dir_settings)
    arduino_info['arduino_app_path'] = arduino_app_path


def init_sketchbook_path():
    """."""
    global arduino_info
    app_dir_settings = arduino_info.get('app_dir_settings')
    sketchbook_path = get_sketchbook_path(app_dir_settings)
    arduino_info['sketchbook_path'] = sketchbook_path


def init_ext_app_path():
    """."""
    global arduino_info
    app_dir_settings = arduino_info.get('app_dir_settings')
    ext_app_path = get_ext_app_path(app_dir_settings)
    arduino_info['ext_app_path'] = ext_app_path


def init_config_settings():
    """."""
    global arduino_info
    arduino_app_path = arduino_info['arduino_app_path']
    config_file_path = os.path.join(arduino_app_path, 'config.stino-settings')
    config_settings = file.SettingsFile(config_file_path)
    if config_settings.get('extra_build_flag') is None:
        config_settings.set('extra_build_flag', '')
    if config_settings.get('save_before_build') is None:
        config_settings.set('save_before_build', True)
    arduino_info['settings'] = config_settings


def init_selected_settings():
    """."""
    global arduino_info
    arduino_app_path = arduino_info['arduino_app_path']
    sel_file_path = os.path.join(arduino_app_path, 'selected.stino-settings')
    sel_settings = file.SettingsFile(sel_file_path)
    arduino_info['selected'] = sel_settings


def init_index_settings():
    """."""
    global arduino_info
    arduino_app_path = arduino_info['arduino_app_path']
    pkgs_file_path = os.path.join(arduino_app_path, 'packages.stino-settings')
    etags_file_path = os.path.join(arduino_app_path, 'etags.stino-settings')
    pkg_index_settings = file.SettingsFile(pkgs_file_path)
    etag_settings = file.SettingsFile(etags_file_path)
    arduino_info['package_index'] = pkg_index_settings
    arduino_info['etags'] = etag_settings
    if not arduino_info['package_index'].get('arduino'):
        arduino_info['package_index'].set('arduino', const.PACKAGE_INDEX_URL)
    if not arduino_info['package_index'].get('arduino_lib'):
        arduino_info['package_index'].set('arduino_lib',
                                          const.LIBRARY_INDEX_URL)


def init_pkgs_info():
    """."""
    global arduino_info
    arduino_app_path = arduino_info['arduino_app_path']
    index_files_info = get_index_files_info(arduino_app_path)
    arduino_info.update(index_files_info)


def init_libs_info():
    """."""
    global arduino_info
    arduino_app_path = arduino_info['arduino_app_path']
    lib_index_files_info = get_lib_index_files_info(arduino_app_path)
    arduino_info.update(lib_index_files_info)


def init_inst_pkgs_info():
    """."""
    global arduino_info
    installed_packages_info = get_installed_packages_info(arduino_info)
    arduino_info.update(installed_packages_info)
    check_platform_selected(arduino_info)


def init_boards_info():
    """."""
    global arduino_info
    arduino_info['boards'] = {}
    boards_info = get_boards_info(arduino_info)
    arduino_info.update(boards_info)
    check_selected(arduino_info, 'board')
    check_board_options_selected(arduino_info)


def init_programmers_info():
    """."""
    global arduino_info
    arduino_info['programmers'] = {}
    basic_programmers_info = get_programmers_info(arduino_info, src='buildin')
    arduino_info['basic_programmers'] = \
        basic_programmers_info.get('programmers', {})
    programmers_info = get_all_programmers_info(arduino_info)
    arduino_info.update(programmers_info)
    check_selected(arduino_info, 'programmer')


def init_menus():
    """."""
    st_menu.update_sketchbook_menu(arduino_info)
    st_menu.update_example_menu(arduino_info)
    st_menu.update_library_menu(arduino_info)
    st_menu.update_install_library_menu(arduino_info)

    st_menu.update_install_platform_menu(arduino_info)
    st_menu.update_platform_menu(arduino_info)
    st_menu.update_version_menu(arduino_info)
    st_menu.update_platform_example_menu(arduino_info)
    st_menu.update_platform_library_menu(arduino_info)

    st_menu.update_board_menu(arduino_info)
    st_menu.update_board_options_menu(arduino_info)
    st_menu.update_programmer_menu(arduino_info)

    st_menu.update_language_menu(arduino_info)


def _init():
    """."""
    # 0. init paths and settings
    init_app_dir_settings()
    init_ardunio_app_path()
    init_sketchbook_path()
    init_ext_app_path()

    init_config_settings()
    init_selected_settings()
    init_index_settings()

    # 1. init packages info
    init_pkgs_info()
    init_libs_info()
    init_inst_pkgs_info()

    # 2. init board info
    init_boards_info()
    init_programmers_info()

    # 3. init menus
    init_menus()

    # 4. update index files
    pkgs_checker.start()
    arduino_info['init_done'] = True


arduino_info = {'init_done': False}
message_queue = task_queue.TaskQueue(st_panel.StPanel().write)
message_queue.put('Thanks for supporting Stino!')

serial_listener = serial_port.SerialListener(update_serial_info)
serial_listener.start()

pkgs_checker = task_listener.TaskListener(task=check_pkgs,
                                          delay=const.REMOTE_CHECK_PERIOD)
platform_tool_downloader = downloader.DownloadQueue(download_platform_tool)
lib_downloader = downloader.DownloadQueue(download_lib)
ide_importer = task_queue.TaskQueue(import_avr_platform)
sketch_builder = task_queue.TaskQueue(build_sketch)
sketch_uploader = task_queue.TaskQueue(upload_sketch)
bootloader = task_queue.TaskQueue(burn_bootloader)

do_action = task_queue.ActionQueue()
do_action.put(_init)
