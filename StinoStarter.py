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
import sublime
import sublime_plugin

st_version = int(sublime.version())
if st_version < 3000:
    import stino
else:
    from . import stino


class SketchListener(sublime_plugin.EventListener):
    def on_close(self, view):
        monitor_module = stino.pyarduino.base.serial_monitor
        if stino.st_console.is_monitor_view(view):
            name = view.name()
            serial_port = name.split('-')[1].strip()
            if serial_port in monitor_module.serials_in_use:
                cur_serial_monitor = monitor_module.serial_monitor_dict.get(
                    serial_port, None)
                if cur_serial_monitor:
                    cur_serial_monitor.stop()
                monitor_module.serials_in_use.remove(serial_port)


class ShowArduinoMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        show_arduino_menu = stino.settings.get('show_arduino_menu', True)
        stino.settings.set('show_arduino_menu', not show_arduino_menu)
        stino.main.create_menus()

    def is_checked(self):
        show_arduino_menu = stino.settings.get('show_arduino_menu', True)
        return show_arduino_menu


class UpdateMenuCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.update_menu()


class NewSketchCommand(sublime_plugin.WindowCommand):
    def run(self):
        caption = stino.i18n.translate('Name for New Sketch:')
        self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, sketch_name):
        stino.main.new_sketch(self.window, sketch_name)


class OpenSketchCommand(sublime_plugin.WindowCommand):
    def run(self, sketch_path):
        stino.main.open_sketch(self.window, sketch_path)


class ImportLibraryCommand(sublime_plugin.TextCommand):
    def run(self, edit, library_path):
        stino.main.import_library(self.view, edit, library_path)


class ShowSketchFolderCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = self.view.file_name()
        if file_path:
            dir_path = os.path.dirname(file_path)
            url = 'file://' + dir_path
            sublime.run_command('open_url', {'url': url})


class CompileSketchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.is_dirty():
            self.view.run_command('save')
        file_path = self.view.file_name()
        if file_path:
            sketch_path = os.path.dirname(file_path)
            stino.main.build_sketch(self.view.window(), sketch_path)


class UploadSketchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.is_dirty():
            self.view.run_command('save')
        file_path = self.view.file_name()
        if file_path:
            sketch_path = os.path.dirname(file_path)
            stino.main.upload_sketch(self.view.window(), sketch_path)


class UploadUsingProgrammerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.is_dirty():
            self.view.run_command('save')
        file_path = self.view.file_name()
        if file_path:
            sketch_path = os.path.dirname(file_path)
            stino.main.upload_sketch(
                self.view.window(), sketch_path, using_programmer=True)


class SetExtraFlagCommand(sublime_plugin.WindowCommand):
    def run(self):
        caption = stino.i18n.translate('Extra compilation flags:')
        extra_flag = stino.settings.get('extra_flag', '')
        self.window.show_input_panel(caption, extra_flag, self.on_done,
                                     None, None)

    def on_done(self, extra_flag):
        stino.settings.set('extra_flag', extra_flag)


class ToggleFullCompilationCommand(sublime_plugin.WindowCommand):
    def run(self):
        build_verbose = stino.settings.get('full_compilation', False)
        stino.settings.set('full_compilation', not build_verbose)

    def is_checked(self):
        build_verbose = stino.settings.get('full_compilation', False)
        return build_verbose


class ShowCompilationOutputCommand(sublime_plugin.WindowCommand):
    def run(self):
        build_verbose = stino.settings.get('build_verbose', False)
        stino.settings.set('build_verbose', not build_verbose)

    def is_checked(self):
        build_verbose = stino.settings.get('build_verbose', False)
        return build_verbose


class ShowUploadOutputCommand(sublime_plugin.WindowCommand):
    def run(self):
        upload_verbose = stino.settings.get('upload_verbose', False)
        stino.settings.set('upload_verbose', not upload_verbose)

    def is_checked(self):
        upload_verbose = stino.settings.get('upload_verbose', False)
        return upload_verbose


class VerifyCodeCommand(sublime_plugin.WindowCommand):
    def run(self):
        verify_code = stino.settings.get('verify_code', False)
        stino.settings.set('verify_code', not verify_code)

    def is_checked(self):
        verify_code = stino.settings.get('verify_code', False)
        return verify_code


class ToggleBareGccOnly(sublime_plugin.WindowCommand):
    def run(self):
        bare_gcc = stino.settings.get('bare_gcc', False)
        stino.settings.set('bare_gcc', not bare_gcc)

    def is_checked(self):
        bare_gcc = stino.settings.get('bare_gcc', False)
        return bare_gcc


class ChooseBuildFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.change_build_dir(self.window)


class SelectBoardCommand(sublime_plugin.WindowCommand):
    def run(self, board_id):
        stino.main.change_board(board_id)

    def is_checked(self, board_id):
        target_board_id = stino.settings.get('target_board_id', '')
        return board_id == target_board_id


class SelectSubBoardCommand(sublime_plugin.WindowCommand):
    def run(self, option_index, sub_board_id):
        stino.main.change_sub_board(option_index, sub_board_id)

    def is_checked(self, option_index, sub_board_id):
        target_board_id = stino.settings.get('target_board_id', '')
        target_sub_board_ids = stino.settings.get(target_board_id, [])
        return sub_board_id in target_sub_board_ids


class SelectProgrammerCommand(sublime_plugin.WindowCommand):
    def run(self, programmer_id):
        stino.main.change_programmer(programmer_id)

    def is_checked(self, programmer_id):
        target_programmer_id = stino.settings.get('target_programmer_id', '')
        return programmer_id == target_programmer_id


class BurnBootloaderCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.burn_bootloader(self.window)


class SelectSerialPortCommand(sublime_plugin.WindowCommand):
    def run(self, serial_port):
        stino.settings.set('serial_port', serial_port)

    def is_checked(self, serial_port):
        target_serial_port = stino.settings.get('serial_port', '')
        return serial_port == target_serial_port


class RunSerialMonitorCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.toggle_serial_monitor(self.window)

    def is_checked(self):
        monitor_module = stino.pyarduino.base.serial_monitor
        state = False
        serial_port = stino.settings.get('serial_port', '')
        if serial_port in monitor_module.serials_in_use:
            serial_monitor = monitor_module.serial_monitor_dict.get(
                serial_port)
            if serial_monitor and serial_monitor.is_running():
                state = True
        return state


class SendSerialMessageCommand(sublime_plugin.WindowCommand):
    def run(self):
        caption = stino.i18n.translate('Send:')
        self.window.show_input_panel(caption, '', self.on_done, None, None)

    def on_done(self, text):
        stino.main.send_serial_message(text)


class ChooseBaudrateCommand(sublime_plugin.WindowCommand):
    def run(self, baudrate):
        stino.settings.set('baudrate', baudrate)

    def is_checked(self, baudrate):
        target_baudrate = stino.settings.get('baudrate', 9600)
        return baudrate == target_baudrate


class ChooseLineEndingCommand(sublime_plugin.WindowCommand):
    def run(self, line_ending):
        stino.settings.set('line_ending', line_ending)

    def is_checked(self, line_ending):
        target_line_ending = stino.settings.get('line_ending', '\n')
        return line_ending == target_line_ending


class ChooseDisplayModeCommand(sublime_plugin.WindowCommand):
    def run(self, display_mode):
        stino.settings.set('display_mode', display_mode)

    def is_checked(self, display_mode):
        target_display_mode = stino.settings.get('display_mode', 'Text')
        return display_mode == target_display_mode


class AutoFormatCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('reindent', {'single_line': False})


class ArchiveSketchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        file_path = self.view.file_name()
        if file_path:
            sketch_path = os.path.dirname(file_path)
            stino.main.archive_sketch(self.view.window(), sketch_path)


class ChooseArduinoFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.select_arduino_dir(self.window)


class ChangeSketchbookFolderCommand(sublime_plugin.WindowCommand):
    def run(self):
        stino.main.change_sketchbook_dir(self.window)


class ToggleGlobalSettings(sublime_plugin.WindowCommand):
    def run(self):
        global_settings = stino.settings.get('global_settings', True)
        stino.settings.set('global_settings', not global_settings)

    def is_checked(self):
        return True


class ToggleBigProject(sublime_plugin.WindowCommand):
    def run(self):
        big_project = stino.settings.get('big_project', False)
        stino.settings.set('big_project', not big_project)
        stino.main.update_menu()

    def is_checked(self):
        big_project = stino.settings.get('big_project', False)
        return big_project


class SelectLanguageCommand(sublime_plugin.WindowCommand):
    def run(self, lang_id):
        stino.i18n.change_lang(lang_id)
        stino.main.create_menus()

    def is_checked(self, lang_id):
        target_lang_id = stino.settings.get('lang_id', 'en')
        return lang_id == target_lang_id


class OpenRefCommand(sublime_plugin.WindowCommand):
    def run(self, url):
        url = stino.main.get_url(url)
        sublime.run_command('open_url', {'url': url})


class FindInReferenceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        stino.main.find_in_ref(self.view)


class StinoDocumentsCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.run_command('open_url',
                            {'url': 'https://github.com/Robot-Will/Stino'})


class AboutStinoCommand(sublime_plugin.WindowCommand):
    def run(self):
        sublime.run_command('open_url',
                            {'url': 'https://github.com/Robot-Will/Stino'})


class NoneCommandCommand(sublime_plugin.WindowCommand):
    def run(self):
        pass

    def is_enabled(self):
        return False


class PanelOutputCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        pos = self.view.size()
        self.view.insert(edit, pos, text)
        self.view.show(pos)
