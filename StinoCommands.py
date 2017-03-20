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
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.st_menu.update_sketchbook_menu,
                                stino.arduino_info)


class StinoNewSketchCommand(sublime_plugin.WindowCommand):
    """New Sketch."""

    def run(self):
        """New Sketch."""
        if stino.arduino_info['init_done']:
            caption = stino.translate('Sketch Name:')
            self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, sketch_name):
        """New Sketch."""
        stino.new_sketch(sketch_name, self.window)


class StinoChangeSketchbookLocationCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            sketchbook_path = stino.arduino_info['sketchbook_path']
            caption = stino.translate('Sketchbook Path:')
            self.window.show_input_panel(caption, sketchbook_path,
                                         self.on_done, None, None)
            stino.do_action.put(stino.st_menu.update_sketchbook_menu,
                                stino.arduino_info)
            stino.do_action.put(stino.st_menu.update_example_menu,
                                stino.arduino_info)
            stino.do_action.put(stino.st_menu.update_library_menu,
                                stino.arduino_info)

    def on_done(self, sketchbook_path):
        """New Sketch."""
        sketchbook_path = sketchbook_path.replace('\\', '/')
        stino.arduino_info['sketchbook_path'] = sketchbook_path
        stino.arduino_info['app_dir_settings'].set('sketchbook_path',
                                                   sketchbook_path)


class StinoOpenInNewWinCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = \
                bool(stino.arduino_info['settings'].get('open_in_new_window'))
            stino.arduino_info['settings'].set('open_in_new_window', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = \
                bool(stino.arduino_info['settings'].get('open_in_new_window'))
        return state


class StinoOpenSketchCommand(sublime_plugin.WindowCommand):
    """Open Sketch."""

    def run(self, sketch_path):
        """Open Sketch."""
        if stino.arduino_info['init_done']:
            in_new = \
                bool(stino.arduino_info['settings'].get('open_in_new_window'))
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
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.st_menu.update_example_menu,
                                stino.arduino_info)


class StinoOpenExampleCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, example_path):
        """."""
        stino.open_project(example_path, self.window)


class StinoRefreshLibrariesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.st_menu.update_library_menu,
                                stino.arduino_info)


class StinoImportLibraryCommand(sublime_plugin.TextCommand):
    """Import Library."""

    def run(self, edit, library_path):
        """Import Library."""
        if stino.arduino_info['init_done']:
            stino.import_lib(self.view, edit, library_path)

    def is_enabled(self):
        """Import Library."""
        state = False
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            if file_path:
                if stino.c_file.is_cpp_file(file_path):
                    state = True
        return state


class StinoRefreshInstallLibraryCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_libs_info)
            stino.do_action.put(stino.st_menu.update_install_library_menu,
                                stino.arduino_info)


class StinoInstallLibCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, category, name, version):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.install_library, category, name, version)


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
        if stino.arduino_info['init_done']:
            caption += '[%s] ' % stino.arduino_info['selected'].get('package')
            caption += '%s ' % stino.arduino_info['selected'].get('platform')
            caption += '%s' % stino.arduino_info['selected'].get('version')
        caption += '--'
        return caption


class StinoRefreshInstallPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_pkgs_info)
            stino.do_action.put(stino.st_menu.update_install_platform_menu,
                                stino.arduino_info)


class StinoAddPackageCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            arduino_app_path = stino.arduino_info.get('arduino_app_path')
            file_path = \
                os.path.join(arduino_app_path, 'packages.stino-settings')
            self.window.open_file(file_path)


class StinoAddIdeCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            ide_path = stino.arduino_info['ext_app_path']
            caption = stino.translate('Arduino IDE Path:')
            self.window.show_input_panel(caption, ide_path, self.on_done,
                                         None, None)
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.st_menu.update_install_platform_menu,
                                stino.arduino_info)
            stino.do_action.put(stino.st_menu.update_example_menu,
                                stino.arduino_info)
            stino.do_action.put(stino.st_menu.update_library_menu,
                                stino.arduino_info)

    def on_done(self, ide_path):
        """New Sketch."""
        ide_path = ide_path.replace('\\', '/')
        stino.arduino_info['ext_app_path'] = ide_path
        stino.arduino_info['app_dir_settings'].set('additional_app_path',
                                                   ide_path)


class StinoImportAvrPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            caption = stino.translate('Arduino IDE Path:')
            self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, ide_path):
        """New Sketch."""
        stino.ide_importer.put(ide_path)


class StinoInstallPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name, version):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.install_platform, package_name,
                                platform_name, version)

    def is_enabled(self, package_name, platform_name, version):
        """."""
        state = True
        if stino.arduino_info['init_done']:
            pkgs_info = stino.arduino_info['installed_packages']
            vers = stino.selected.get_platform_versions(pkgs_info,
                                                        package_name,
                                                        platform_name)
            if version in vers:
                state = False
        return state


class StinoRefreshPlatformsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.st_menu.update_platform_menu,
                                stino.arduino_info)


class StinoSelectPlatformCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, package_name, platform_name):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(package_name, platform_name):
                stino.do_action.put(stino.on_platform_select, package_name,
                                    platform_name)

    def is_checked(self, package_name, platform_name):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            c1 = stino.arduino_info['selected'].get('package') == package_name
            c2 = \
                stino.arduino_info['selected'].get('platform') == platform_name
            state = c1 and c2
        return state


class StinoRefreshPlatformVersionsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.st_menu.update_version_menu,
                                stino.arduino_info)


class StinoCheckToolsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.check_platform_dep)


class StinoSelectVersionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, version):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(version):
                stino.do_action.put(stino.on_version_select, version)

    def is_checked(self, version):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = stino.arduino_info['selected'].get('version') == version
        return state


class StinoRefreshPlatformExamplesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.st_menu.update_platform_example_menu,
                                stino.arduino_info)


class StinoRefreshPlatformLibrariesCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.st_menu.update_platform_library_menu,
                                stino.arduino_info)


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
        caption = '----'
        if stino.arduino_info['init_done']:
            caption = '--%s--' % stino.arduino_info['selected'].get('board')
        return caption


class StinoBuildCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            dir_path = os.path.dirname(file_path)
            build_info = {'path': dir_path}
            stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            if file_path:
                if stino.c_file.is_cpp_file(file_path):
                    info = \
                        stino.selected.get_sel_board_info(stino.arduino_info)
                    if info:
                        state = True
        return state


class StinoRefreshBoardsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.init_boards_info)
            stino.do_action.put(stino.st_menu.update_board_menu,
                                stino.arduino_info)


class StinoSelectBoardCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, board_name):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(board_name):
                stino.do_action.put(stino.on_board_select, board_name)

    def is_checked(self, board_name):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = stino.arduino_info['selected'].get('board') == board_name
        return state


class StinoRefreshBoardOptionsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.init_boards_info)
            stino.do_action.put(stino.st_menu.update_board_options_menu,
                                stino.arduino_info)


class StinoSelectBoardOptionCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, option, value):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(option, value):
                stino.on_board_option_select(option, value)

    def is_checked(self, option, value):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            key = 'option_%s' % option
            state = stino.arduino_info['selected'].get(key) == value
        return state


class StinoSetExtraFlagCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            arduino_app_path = stino.arduino_info.get('arduino_app_path')
            file_path = os.path.join(arduino_app_path, 'config.stino-settings')
            self.window.open_file(file_path)


class StinoSaveBeforeBuildCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = \
                bool(stino.arduino_info['settings'].get('save_before_build'))
            stino.arduino_info['settings'].set('save_before_build', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = \
                bool(stino.arduino_info['settings'].get('save_before_build'))
        return state


class StinoToggleFullBuildCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('full_build'))
            stino.arduino_info['settings'].set('full_build', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('full_build'))
        return state


class StinoShowBuildOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verbose_build'))
            stino.arduino_info['settings'].set('verbose_build', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verbose_build'))
        return state


class StinoShowUploadOutputCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verbose_upload'))
            stino.arduino_info['settings'].set('verbose_upload', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verbose_upload'))
        return state


class StinoVerifyCodeCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verify_code'))
            stino.arduino_info['settings'].set('verify_code', not state)

    def is_checked(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            state = bool(stino.arduino_info['settings'].get('verify_code'))
        return state


class StinoShowBuildDirCommand(sublime_plugin.TextCommand):
    """Show Sketch Folder."""

    def run(self, edit):
        """Show Sketch Folder."""
        if stino.arduino_info['init_done']:
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
        if stino.arduino_info['init_done']:
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
        caption = '----'
        if stino.arduino_info['init_done']:
            key = 'serial_port'
            caption = '--%s--' % stino.arduino_info['selected'].get(key)
        return caption


class StinoUploadCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            dir_path = os.path.dirname(file_path)
            build_info = {'path': dir_path}
            build_info['upload_mode'] = 'upload'
            stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            sel_serial = stino.arduino_info['selected'].get('serial_port')
            if sel_serial and file_path and \
                    stino.c_file.is_cpp_file(file_path):
                info = stino.selected.get_sel_board_info(stino.arduino_info)
                if info:
                    state = True
        return state


class StinoRefreshSerialsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.st_menu.update_serial_menu,
                                stino.arduino_info)


class StinoSelectSerialCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, serial_port):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(serial_port):
                stino.on_serial_select(serial_port)

    def is_checked(self, serial_port):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            key = 'serial_port'
            state = stino.arduino_info['selected'].get(key) == serial_port
        return state


class StinoGetPortInfoCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit):
        """."""
        if stino.arduino_info['init_done']:
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
        if stino.arduino_info['init_done']:
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
        caption = '----'
        if stino.arduino_info['init_done']:
            key = 'programmer'
            caption = '--%s--' % stino.arduino_info['selected'].get(key)
        return caption


class StinoUploadUsingProgrammerCommand(sublime_plugin.TextCommand):
    """Upload Using Programmer."""

    def run(self, edit):
        """Upload Using Programmer."""
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            dir_path = os.path.dirname(file_path)
            build_info = {'path': dir_path}
            build_info['upload_mode'] = 'program'
            stino.sketch_builder.put(build_info)

    def is_enabled(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            file_path = self.view.file_name()
            sel_prog = stino.arduino_info['selected'].get('programmer')
            if file_path and stino.c_file.is_cpp_file(file_path) and sel_prog:
                cmd = stino.selected.get_upload_command(stino.arduino_info,
                                                        mode='program')
                if cmd:
                    info = \
                        stino.selected.get_sel_board_info(stino.arduino_info)
                    if info:
                        state = True
        return state


class StinoRefreshProgrammersCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.init_inst_pkgs_info)
            stino.do_action.put(stino.init_programmers_info)
            stino.do_action.put(stino.st_menu.update_programmer_menu,
                                stino.arduino_info)


class StinoSelectProgrammerCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, programmer_name):
        """."""
        if stino.arduino_info['init_done']:
            if not self.is_checked(programmer_name):
                stino.on_programmer_select(programmer_name)

    def is_checked(self, programmer_name):
        """."""
        state = False
        if stino.arduino_info['init_done']:
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
        if stino.arduino_info['init_done']:
            msg = 'Beware: Please check your board type! Continue？'
            result = sublime.yes_no_cancel_dialog(msg)
            if result == sublime.DIALOG_YES:
                stino.bootloader.put()

    def is_enabled(self):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            sel_prog = stino.arduino_info['selected'].get('programmer')
            if sel_prog:
                cmds = \
                    stino.selected.get_bootloader_commands(stino.arduino_info)
                if cmds and cmds[0] and cmds[1]:
                    info = \
                        stino.selected.get_sel_board_info(stino.arduino_info)
                    if info:
                        state = True
        return state


class StinoAutoFormatCommand(sublime_plugin.TextCommand):
    """Auto Format Src."""

    def run(self, edit):
        """Auto Format Src."""
        self.view.run_command('save')
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
class StinoShowPanelCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        panel_name = 'stino_panel'
        if not self.window.find_output_panel(panel_name):
            stino.message_queue.put()
        out_panel_name = 'output.stino_panel'
        self.window.run_command("show_panel", {"panel": out_panel_name})


class StinoRefreshLangsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.do_action.put(stino.st_menu.update_language_menu,
                                stino.arduino_info)


class StinoSelectLanguageCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self, language):
        """."""
        if stino.arduino_info['init_done']:
            if self.is_checked(language):
                stino.do_action.put(stino.on_language_select, language)

    def is_checked(self, language):
        """."""
        state = False
        if stino.arduino_info['init_done']:
            key = 'language'
            state = stino.arduino_info['selected'].get(key) == language
        return state


class StinoOpenPlatformDocumentsCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        if stino.arduino_info['init_done']:
            stino.open_platform_documents()


class StinoAboutCommand(sublime_plugin.WindowCommand):
    """."""

    def run(self):
        """."""
        stino.message_queue.put('Stino 2017')


class StinoPanelWriteCommand(sublime_plugin.TextCommand):
    """."""

    def run(self, edit, text, mode='insert', do_scroll=True):
        """."""
        point = self.view.size()
        if mode == 'insert':
            self.view.insert(edit, point, text)
        else:
            region = sublime.Region(0, point)
            self.view.replace(edit, region, text)

        if do_scroll:
            point = self.view.size()
            self.view.show(point)
