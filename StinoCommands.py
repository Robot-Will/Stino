#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys

import sublime
import sublime_plugin


def get_relative_path(relative_dir):
    """."""
    cur_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.normpath(os.path.join(cur_path, relative_dir))
    return dir_path


def add_relative_dir_to_sys_path(relative_dir):
    """."""
    dir_path = get_relative_path(relative_dir)
    sys.path.append(dir_path)


stino = None
add_relative_dir_to_sys_path('libs')
st_version = 2 if sys.version_info < (3,) else 3


def plugin_loaded():
    """."""
    global stino
    import stino_runtime as stino

# if st_version == 2:
#     plugin_loaded()


#############################################
# Sketch Commands
#############################################
class StinoRefreshSketchbookCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_sketchbook_menu(stino.arduino_info)


class StinoNewSketchCommand(sublime_plugin.WindowCommand):
    """New Sketch."""

    def run(self):
        """New Sketch."""
        caption = stino.translate('Sketch Name:')
        self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, sketch_name):
        """New Sketch."""
        stino.new_sketch(sketch_name, self.window)


class StinoChangeSketchbookLocationCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        plugin_name = stino.plugin_name
        conf_path = stino.default_st_dirs.get_plugin_config_path(plugin_name)
        file_path = os.path.join(conf_path, 'app_dir.stino-settings')
        self.window.open_file(file_path)


class StinoOpenInNewWinCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('open_in_new_window'))
        stino.arduino_info['settings'].set('open_in_new_window', not state)

    def is_checked(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('open_in_new_window'))
        return state


class StinoOpenSketchCommand(sublime_plugin.WindowCommand):
    """Open Sketch."""

    def run(self, sketch_path):
        """Open Sketch."""
        in_new = bool(stino.arduino_info['settings'].get('open_in_new_window'))
        win = self.window
        if in_new:
            sublime.run_command('new_window')
            win = sublime.windows()[-1]
        stino.open_project(sketch_path, win)


class StinoShowSketchDirCommand(sublime_plugin.TextCommand):
    """Show Sketch Folder."""

    def run(self, edit):
        """Show Sketch Folder."""
        file_path = self.view.file_name()
        if file_path:
            dir_path = os.path.dirname(file_path)
            url = 'file://' + dir_path
            sublime.run_command('open_url', {'url': url})


#############################################
# Example and Library Commands
#############################################
class StinoRefreshExamplesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_example_menu(stino.arduino_info)


class StinoOpenExampleCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, example_path):
        """."""
        stino.open_project(example_path, self.window)


class StinoRefreshLibrariesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_library_menu(stino.arduino_info)


class StinoImportLibraryCommand(sublime_plugin.TextCommand):
    """Import Library."""

    def run(self, edit, library_path):
        """Import Library."""
        stino.import_lib(self.view, edit, library_path)

    def is_enabled(self):
        """Import Library."""
        state = False
        file_path = self.view.file_name()
        if file_path:
            if stino.c_file.is_cpp_file(file_path):
                state = True
        return state


class StinoRefreshInstallLibraryCommand(sublime_plugin.WindowCommand):
    """Import Library."""

    def run(self):
        """."""
        stino.st_menu.update_install_library_menu(stino.arduino_info)


class StinoInstallLibCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, category, name, version):
        """."""
        stino.install_library(category, name, version)


#############################################
# Package and Platform Commands
#############################################
class StinoPlatformInfoCommand(sublime_plugin.WindowCommand):
    """."""

    def is_enabled(self):
        """."""
        return False

    def description(self):
        """."""
        caption = '--'
        caption += '[%s] ' % stino.arduino_info['selected'].get('package')
        caption += '%s ' % stino.arduino_info['selected'].get('platform')
        caption += '%s' % stino.arduino_info['selected'].get('version')
        caption += '--'
        return caption


class StinoRefreshInstallPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_install_platform_menu(stino.arduino_info)


class StinoAddPackageCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        arduino_app_path = stino.arduino_info.get('arduino_app_path')
        file_path = os.path.join(arduino_app_path, 'packages.stino-settings')
        self.window.open_file(file_path)


class StinoImportAvrPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        caption = stino.translate('Arduino IDE Path:')
        self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, ide_path):
        """New Sketch."""
        stino.ide_importer.put(ide_path)


class StinoInstallPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name, version):
        """."""
        stino.install_platform(package_name, platform_name, version)

    def is_enabled(self, package_name, platform_name, version):
        """."""
        state = True
        pkgs_info = stino.arduino_info['installed_packages']
        vers = stino.selected.get_platform_versions(pkgs_info, package_name,
                                                    platform_name)
        if version in vers:
            state = False
        return state


class StinoRefreshPlatformsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_platform_menu(stino.arduino_info)


class StinoSelectPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name):
        """."""
        if not self.is_checked(package_name, platform_name):
            stino.on_platform_select(package_name, platform_name)

    def is_checked(self, package_name, platform_name):
        """."""
        c1 = stino.arduino_info['selected'].get('package') == package_name
        c2 = stino.arduino_info['selected'].get('platform') == platform_name
        state = c1 and c2
        return state


class StinoRefreshPlatformVersionsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_version_menu(stino.arduino_info)


class StinoCheckToolsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        platform_info = \
            stino.selected.get_sel_platform_info(stino.arduino_info)
        stino.check_tools_deps(platform_info)


class StinoSelectVersionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, version):
        """."""
        if not self.is_checked(version):
            stino.on_version_select(version)

    def is_checked(self, version):
        """."""
        state = stino.arduino_info['selected'].get('version') == version
        return state


class StinoRefreshPlatformExamplesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_platform_example_menu(stino.arduino_info)


class StinoRefreshPlatformLibrariesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_platform_library_menu(stino.arduino_info)


#############################################
# Board and Build Commands
#############################################
class StinoBoardInfoCommand(sublime_plugin.WindowCommand):
    """."""

    def is_enabled(self):
        """."""
        return False

    def description(self):
        """."""
        caption = '--%s--' % stino.arduino_info['selected'].get('board')
        return caption


class StinoBuildCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        file_path = self.view.file_name()
        dir_path = os.path.dirname(file_path)
        build_info = {'path': dir_path}
        stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        file_path = self.view.file_name()
        if file_path:
            if stino.c_file.is_cpp_file(file_path):
                info = stino.selected.get_sel_board_info(stino.arduino_info)
                if info:
                    state = True
        return state


class StinoRefreshBoardsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_board_menu(stino.arduino_info)


class StinoSelectBoardCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, board_name):
        """."""
        if not self.is_checked(board_name):
            stino.on_board_select(board_name)

    def is_checked(self, board_name):
        """."""
        state = stino.arduino_info['selected'].get('board') == board_name
        return state


class StinoRefreshBoardOptionsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_board_options_menu(stino.arduino_info)


class StinoSelectBoardOptionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, option, value):
        """."""
        if not self.is_checked(option, value):
            stino.on_board_option_select(option, value)

    def is_checked(self, option, value):
        """."""
        key = 'option_%s' % option
        state = stino.arduino_info['selected'].get(key) == value
        return state


class StinoSetExtraFlagCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        arduino_app_path = stino.arduino_info.get('arduino_app_path')
        file_path = os.path.join(arduino_app_path, 'config.stino-settings')
        self.window.open_file(file_path)


class StinoToggleFullBuildCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('full_build'))
        stino.arduino_info['settings'].set('full_build', not state)

    def is_checked(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('full_build'))
        return state


class StinoShowBuildOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verbose_build'))
        stino.arduino_info['settings'].set('verbose_build', not state)

    def is_checked(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verbose_build'))
        return state


class StinoShowUploadOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verbose_upload'))
        stino.arduino_info['settings'].set('verbose_upload', not state)

    def is_checked(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verbose_upload'))
        return state


class StinoVerifyCodeCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verify_code'))
        stino.arduino_info['settings'].set('verify_code', not state)

    def is_checked(self):
        """."""
        state = bool(stino.arduino_info['settings'].get('verify_code'))
        return state


class StinoShowBuildDirCommand(sublime_plugin.TextCommand):
    """Show Sketch Folder."""

    def run(self, edit):
        """Show Sketch Folder."""
        file_path = self.view.file_name()
        if file_path:
            prj_path = os.path.dirname(file_path)
            prj_name = os.path.basename(prj_path)
            arduino_app_path = stino.arduino_info['arduino_app_path']
            build_path = os.path.join(arduino_app_path, 'build')
            prj_build_path = os.path.join(build_path, prj_name)
            if os.path.isdir(prj_build_path):
                url = 'file://' + prj_build_path
                sublime.run_command('open_url', {'url': url})

    def is_enabled(self):
        """."""
        state = False
        file_path = self.view.file_name()
        if file_path:
            if stino.c_file.is_cpp_file(file_path):
                state = True
        return state


#############################################
# Serial and Upload Commands
#############################################
class StinoSerialInfoCommand(sublime_plugin.WindowCommand):
    """."""

    def is_enabled(self):
        """."""
        return False

    def description(self):
        """."""
        key = 'serial_port'
        caption = '--%s--' % stino.arduino_info['selected'].get(key)
        return caption


class StinoUploadCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        file_path = self.view.file_name()
        dir_path = os.path.dirname(file_path)
        build_info = {'path': dir_path}
        build_info['upload_mode'] = 'upload'
        stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        file_path = self.view.file_name()
        sel_serial = stino.arduino_info['selected'].get('serial_port')
        if sel_serial and file_path and stino.c_file.is_cpp_file(file_path):
            info = stino.selected.get_sel_board_info(stino.arduino_info)
            if info:
                state = True
        return state


class StinoNetworkUploadCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        file_path = self.view.file_name()
        dir_path = os.path.dirname(file_path)
        build_info = {'path': dir_path}
        build_info['upload_mode'] = 'network'
        stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        file_path = self.view.file_name()
        if file_path and stino.c_file.is_cpp_file(file_path):
            info = stino.selected.get_sel_board_info(stino.arduino_info)
            if 'upload.network.port' in info:
                state = True
        return state


class StinoRefreshSerialsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_serial_menu(stino.arduino_info)


class StinoSelectSerialCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, serial_port):
        """."""
        if not self.is_checked(serial_port):
            stino.on_serial_select(serial_port)

    def is_checked(self, serial_port):
        """."""
        key = 'serial_port'
        state = stino.arduino_info['selected'].get(key) == serial_port
        return state


class StinoGetPortInfoCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        serials_info = stino.serial_port.get_serials_info()
        sel_serial = stino.arduino_info['selected'].get('serial_port')
        if sel_serial:
            info = serials_info.get(sel_serial, {})
            if info:
                port = info.get('port')
                desc = info.get('description')
                hwid = info.get('hwid')
                stino.message_queue.put(port)
                stino.message_queue.put(desc)
                stino.message_queue.put(hwid)

                board_info = \
                    stino.selected.get_sel_board_info(stino.arduino_info)
                board_name = board_info.get('name')
                vid = board_info.get('build.vid', 'None')
                pid = board_info.get('build.pid', 'None')
                stino.message_queue.put(board_name)
                stino.message_queue.put('VID:PID=%s:%s' % (vid, pid))

    def is_enabled(self):
        """."""
        state = False
        sel_serial = stino.arduino_info['selected'].get('serial_port')
        if sel_serial:
            state = True
        return state


#############################################
# Programmer Commands
#############################################
class StinoProgrammerInfoCommand(sublime_plugin.WindowCommand):
    """."""

    def is_enabled(self):
        """."""
        return False

    def description(self):
        """."""
        key = 'programmer'
        caption = '--%s--' % stino.arduino_info['selected'].get(key)
        return caption


class StinoUploadUsingProgrammerCommand(sublime_plugin.TextCommand):
    """Upload Using Programmer."""

    def run(self, edit):
        """Upload Using Programmer."""
        file_path = self.view.file_name()
        dir_path = os.path.dirname(file_path)
        build_info = {'path': dir_path}
        build_info['upload_mode'] = 'programmer'
        stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        file_path = self.view.file_name()
        sel_prog = stino.arduino_info['selected'].get('programmer')
        if sel_prog and file_path and stino.c_file.is_cpp_file(file_path):
            cmds_info = stino.selected.get_sel_cmds_info(stino.arduino_info)
            upload_cmd = cmds_info.get('program.pattern', '')
            if upload_cmd:
                info = stino.selected.get_sel_board_info(stino.arduino_info)
                if info:
                    state = True
        return state


class StinoRefreshProgrammersCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_programmer_menu(stino.arduino_info)


class StinoSelectProgrammerCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, programmer_name):
        """."""
        if not self.is_checked(programmer_name):
            stino.on_programmer_select(programmer_name)

    def is_checked(self, programmer_name):
        """."""
        key = 'programmer'
        state = stino.arduino_info['selected'].get(key) == programmer_name
        return state


#############################################
# Tools Commands
#############################################
class StinoBurnBootloaderCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        msg = 'Beware: Please check your board type! Continue？'
        result = sublime.yes_no_cancel_dialog(msg)
        if result == sublime.DIALOG_YES:
            stino.bootloader.put()

    def is_enabled(self):
        """."""
        state = False
        sel_serial = stino.arduino_info['selected'].get('serial_port')
        if sel_serial:
            cmds_info = stino.selected.get_sel_cmds_info(stino.arduino_info)
            erase_cmd = cmds_info.get('erase.pattern', '')
            bootloader_cmd = cmds_info.get('bootloader.pattern', '')
            if erase_cmd and bootloader_cmd:
                info = stino.selected.get_sel_board_info(stino.arduino_info)
                if info:
                    state = True
        return state


class StinoAutoFormatCommand(sublime_plugin.TextCommand):
    """Auto Format Src."""

    def run(self, edit):
        """Auto Format Src."""
        file_path = self.view.file_name()
        stino.beautify_src(self.view, edit, file_path)

    def is_enabled(self):
        """Auto Format Src."""
        state = False
        file_path = self.view.file_name()
        if file_path and stino.c_file.is_cpp_file(file_path):
            state = True
        return state


#############################################
# Help Commands
#############################################
class StinoRefreshLangsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_language_menu(stino.arduino_info)


class StinoSelectLanguageCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, language):
        """."""
        if self.is_checked(language):
            stino.on_language_select(language)

    def is_checked(self, language):
        """."""
        key = 'language'
        state = stino.arduino_info['selected'].get(key) == language
        return state


class StinoOpenPlatformDocumentsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.open_platform_documents()


class StinoAboutCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.message_queue.put('Stino 2017')


class StinoPanelWriteCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit, text):
        """."""
        point = self.view.size()
        self.view.insert(edit, point, text)
        self.view.show(point)
