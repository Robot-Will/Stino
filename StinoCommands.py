#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import glob

import sublime
import sublime_plugin


def add_relative_dir_to_sys_path(relative_dir):
    """."""
    cur_path = os.path.dirname(os.path.realpath(__file__))
    dir_path = os.path.normpath(os.path.join(cur_path, relative_dir))

    zip_pattern = os.path.join(dir_path, '*.zip')
    zip_files = glob.glob(zip_pattern)

    paths = [dir_path] + zip_files
    for path in paths:
        if path not in sys.path:
            sys.path.append(dir_path)


stino = None
add_relative_dir_to_sys_path('libs')


def plugin_loaded():
    """."""
    global stino
    import stino_runtime as stino


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
        caption = 'Sketch Name:'
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
        stino.open_project(sketch_path, self.window)


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
        print(library_path)


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


class StinoInstallPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name, version):
        """."""
        print(package_name, platform_name, version)


class StinoRefreshPlatformsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_platform_menu(stino.arduino_info)


class StinoSelectPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name):
        """."""
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


class StinoSelectVersionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, version):
        """."""
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


class StinoBuildCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Build')


class StinoRefreshBoardsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.st_menu.update_board_menu(stino.arduino_info)


class StinoSelectBoardCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, board_name):
        """."""
        stino.on_board_select(board_name)

    def is_checked(self, board_name):
        """."""
        state = stino.arduino_info['selected'].get('board') == board_name
        return state


class StinoRefreshBoardOptionsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('refresh Baord Options')


class StinoSelectBoardOptionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, option_name, value):
        """."""
        print('select board option')


class StinoSetExtraFlagCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Set Extra Flag')


class StinoToggleFullBuildCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Full Build')

    def is_checked(self):
        """."""
        state = True
        return state


class StinoShowBuildOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('show build output')

    def is_checked(self):
        """."""
        state = True
        return state


class StinoShowUploadOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('show Upload output')

    def is_checked(self):
        """."""
        state = True
        return state


class StinoVerifyCodeCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Verify Code')

    def is_checked(self):
        """."""
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
        caption = '--Serial--'
        return caption


class StinoUploadCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Upload')


class StinoRefreshSerialsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('refresh Serials')


class StinoSelectSerialCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, serial_port):
        """."""
        print('select Serial')


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
        caption = '--Programmer--'
        return caption


class StinoUploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
    """Upload Using Programmer."""

    def run(self):
        """Upload Using Programmer."""
        pass


class StinoRefreshProgrammersCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('refresh Programmers')


class StinoSelectProgrammerCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, programmer_name):
        """."""
        print('select Programmer')


#############################################
# Tools Commands
#############################################
class StinoBurnBootloaderCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Burn Bootloader')


class StinoAutoFormatCommand(sublime_plugin.TextCommand):
    """Auto Format Src."""

    def run(self, edit):
        """Auto Format Src."""
        from base_utils import c_file
        file_path = self.view.file_name()
        cur_file = c_file.CFile(file_path)
        if cur_file.is_cpp_src():
            beautiful_text = cur_file.get_beautified_text()
            region = sublime.Region(0, self.view.size())
            self.view.replace(edit, region, beautiful_text)

    def is_enabled(self):
        """Auto Format Src."""
        state = False
        file_path = self.view.file_name()
        if file_path:
            ext = os.path.splitext(file_path)[1]
            if ext in ('.c', '.cxx', '.cpp', '.h',
                       '.hh', '.hpp', '.ino', '.dpe'):
                state = True
        return state


#############################################
# Help Commands
#############################################
class StinoRefreshLangsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('refresh Langs')


class StinoSelectLangCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, lang_name):
        """."""
        print('select Lang')


class StinoFindInRefCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Find in Ref')


class StinoAboutCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        print('Stino 2017')
