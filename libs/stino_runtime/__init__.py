#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import glob
import zipfile
import tarfile
import platform
import shutil
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


def get_index_files_info(arduino_dir_path):
    """."""
    file_paths = glob.glob(arduino_dir_path + '/package*_index.json')
    index_files = index_file.IndexFiles(file_paths)
    info = index_files.get_info()
    return info


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
            ptfm_arch = os.path.basename(platform_path)
            ptfm_name = selected.get_platform_name_by_arch(arduino_info,
                                                           pkg_name,
                                                           ptfm_arch)
            pkg_info['platforms']['names'].append(ptfm_name)

            version_paths = glob.glob(platform_path + '/*')
            versions = [os.path.basename(p) for p in version_paths]
            ptfm_info = {'versions': versions}
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


def get_programmers_info(arduino_info):
    """."""
    programmers_info = {'programmers': {}}
    platform_path = selected.get_sel_platform_path(arduino_info)
    if platform_path:
        progs_file_path = os.path.join(platform_path, 'programmers.txt')
        progs_file = plain_params_file.ProgrammersFile(progs_file_path)
        programmers_info = progs_file.get_programmers_info()
    return programmers_info


def update_serial_info(serial_ports):
    """."""
    global arduino_info
    arduino_info['serial_ports'] = {'names': serial_ports}
    st_menu.update_serial_menu(arduino_info)
    check_selected(arduino_info, 'serial_port')


def check_platform_selected(arduino_info):
    """."""
    sel_settings = arduino_info.get('selected', {})
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
    sel_settings = arduino_info.get('selected', {})
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
    programmers_info = get_programmers_info(arduino_info)
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
    platform_info = selected.get_sel_platform_info(arduino_info)
    check_tools_deps(platform_info)


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
                if zip_name.endswith('.zip'):
                    with zipfile.ZipFile(zip_path, 'r') as f:
                        names = f.namelist()
                        try:
                            f.extractall(name_path)
                        except (IOError, FileNotFoundError) as e:
                            message_queue.put('%s' % e)
                elif zip_name.endswith('.gz') or zip_name.endswith('.bz2'):
                    with tarfile.open(zip_path, 'r') as f:
                        names = f.getnames()
                        try:
                            f.extractall(name_path)
                        except (IOError, FileNotFoundError) as e:
                            message_queue.put('%s' % e)

                if names:
                    dir_name = names[0]
                    new_path = os.path.join(name_path, dir_name)
                    os.rename(new_path, version_path)

                msg = '[%s] %s %s: ' % (package, name, version)
                msg += 'Installation completed.'
                message_queue.put(msg)

                if down_type == 'platform':
                    installed_packages_info = \
                        get_installed_packages_info(arduino_info)
                    arduino_info.update(installed_packages_info)
                    st_menu.update_platform_menu(arduino_info)
                    st_menu.update_version_menu(arduino_info)
                    check_tools_deps(version_info)


def check_tools_deps(platform_info):
    """."""
    is_ready = True

    tools_info = selected.get_sel_tools_info(arduino_info, platform_info)
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
            tools_info = package_info.get('tools', {})
            tool_info = tools_info.get(name, {})
            version_info = tool_info.get(version, {})
            systems_info = version_info.get('systems', [])
            for system_info in systems_info:
                host = system_info.get('host', '')
                url = system_info.get('url', '')
                if '-' in host:
                    host_infos = host.split('-')
                    if len(host_infos) > 1:
                        arch = host_infos[0]
                        os_name = host_infos[1]

                        go_down = False
                        if sys_info.get_os_name() == 'windows':
                            if os_name == 'mingw32':
                                go_down = True
                                break
                        elif sys_info.get_os_name() == 'osx':
                            if os_name == 'apple':
                                go_down = True
                                break
                        elif sys_info.get_os_name() == 'linux':
                            if os_name == 'linux':
                                machine = platform.machine()
                                if machine == 'i686' and arch == 'i686':
                                    go_down = True
                                    break
                                elif machine == 'x86_64' and arch == 'x86_64':
                                    go_down = True
                                    break
                                elif arch == 'arm':
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


def import_avr_platform(ide_path):
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
            index_files = index_file.IndexFiles([index_file_path])
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
                        version_info = platform_info.get(version, {})

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
                            check_tools_deps(version_info)
    if not is_ide:
        msg = '[Error] %s is not Arduino IDE.' % ide_path
        message_queue.put(msg)


def build_sketch(project_path):
    """."""
    # 1. Check Toolchain
    msg = '[Build] %s...' % project_path
    message_queue.put(msg)
    msg = '[Step 1] Check Toolchain.'
    message_queue.put(msg)
    platform_info = selected.get_sel_platform_info(arduino_info)
    is_ready = check_tools_deps(platform_info)
    if is_ready:
        msg = '[Step 1] Done.'
        message_queue.put(msg)
        msg = '[Step 2] Find main source file.'
        message_queue.put(msg)
        arduino_app_path = arduino_info['arduino_app_path']
        build_dir_path = os.path.join(arduino_app_path, 'build')

        prj = c_project.CProject(project_path)
        main_file_path = prj.get_main_file(build_dir_path)
        message_queue.put(main_file_path)
        if main_file_path:
            msg = '[Step 2] Done.'
            message_queue.put(msg)
            msg = '[Step 3] List all cpp files.'
            message_queue.put(msg)
            msg = '[Step 4] List Commands.'

            message_queue.put(msg)
            cmds_info = selected.get_commands_info(arduino_info, prj)
            print(cmds_info)

            msg = '[Step 5] Run Commands.'
            message_queue.put(msg)


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
            if remote_etag != local_etag:
                is_done = downloader.download(url, arduino_dir_path,
                                              message_queue.put,
                                              mode='replace')
                if is_done:
                    arduino_info['etags'].set(key, remote_etag)
                    is_changed = True
    if is_changed:
        index_files_info = get_index_files_info(arduino_dir_path)
        arduino_info.update(index_files_info)
        st_menu.update_install_platform_menu(arduino_info)


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
    etags_file_path = os.path.join(arduino_dir_path, 'etags.stino-settings')
    pkg_index_settings = file.SettingsFile(pkgs_file_path)
    etag_settings = file.SettingsFile(etags_file_path)
    arduino_info['package_index'] = pkg_index_settings
    arduino_info['etags'] = etag_settings
    if not arduino_info['package_index'].get('arduino'):
        arduino_info['package_index'].set('arduino', const.PACKAGE_INDEX_URL)

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
    check_selected(arduino_info, 'board')
    check_board_options_selected(arduino_info)

    programmers_info = get_programmers_info(arduino_info)
    arduino_info.update(programmers_info)
    check_selected(arduino_info, 'programmer')

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


message_queue = task_queue.TaskQueue(st_panel.StPanel().write)
message_queue.put('Thanks for supporting Stino!')

arduino_info = {}
init()

pkgs_checker = task_listener.TaskListener(task=check_pkgs,
                                          delay=const.REMOTE_CHECK_PERIOD)
pkgs_checker.start()

platform_tool_downloader = downloader.DownloadQueue(download_platform_tool)
ide_importer = task_queue.TaskQueue(import_avr_platform)
sketch_builder = task_queue.TaskQueue(build_sketch)
