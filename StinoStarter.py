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
import re
import sublime
import sublime_plugin

st_version = int(sublime.version())
if st_version < 3000:
    import stino
else:
    from . import stino


class SketchListener(sublime_plugin.EventListener):
    def __init__(self):
        super(SketchListener, self).__init__()
        self.sketch_files_dict = {}
        self.file_view_dict = {}

        pattern_text = r'^(\S*?):([0-9]+?):'
        self.pattern = re.compile(pattern_text, re.M | re.S)

    def on_activated(self, view):
        stino.main.set_status(view)

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

    def on_selection_modified(self, view):
        view_name = view.name()
        if view_name.startswith('build|') or view_name.startswith('upload|'):
            view_selection = view.sel()
            region = view_selection[0]
            region = view.line(region)
            text = view.substr(region)
            matches = list(self.pattern.finditer(text))
            if matches:
                view_selection.clear()
                view_selection.add(region)
                match = matches[0]
                file_path, line_no = match.groups()
                file_view = view.window().open_file(file_path)
                error_point = file_view.text_point(int(line_no) - 1, 0)
                region = file_view.line(error_point)
                selection = file_view.sel()
                selection.clear()
                selection.add(region)
                file_view.show(error_point)

    def on_modified(self, view):
        if st_version < 3000:
            flag = sublime.DRAW_OUTLINED
        else:
            flag = sublime.DRAW_NO_FILL

        view_name = view.name()
        if view_name.startswith('build|') or view_name.startswith('upload|'):
            sketch_path = view_name.split('|')[1]
            files = self.sketch_files_dict.get(sketch_path, [])
            for file_path in files:
                file_view = self.file_view_dict.get(file_path, None)
                if file_view in sublime.active_window().views():
                    key = 'stino.' + file_path
                    file_view.erase_regions(key)

            console_regions = []
            file_regions_dict = {}
            files = []
            text = view.substr(sublime.Region(0, view.size()))
            matches = self.pattern.finditer(text)
            for match in matches:
                cur_point = match.start()
                line_region = view.line(cur_point)
                console_regions.append(line_region)

                file_path, line_no = match.groups()
                file_view = view.window().open_file(file_path)
                error_point = file_view.text_point(int(line_no) - 1, 0)
                line_region = file_view.line(error_point)

                if not file_path in files:
                    files.append(file_path)
                    self.file_view_dict[file_path] = file_view
                regions = file_regions_dict.setdefault(file_path, [])
                if not line_region in regions:
                    regions.append(line_region)
                file_regions_dict[file_path] = regions
            view.add_regions('build_error', console_regions, 'string',
                             'circle', flag)

            self.sketch_files_dict[sketch_path] = files
            for file_path in files:
                key = 'stino.' + file_path
                file_view = self.file_view_dict.get(file_path)
                regions = file_regions_dict.get(file_path, [])
                file_view.add_regions(key, regions, 'string', 'circle',
                                      flag)

                if regions:
                    region = regions[0]
                    file_view.show(region)


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
        new_window = stino.settings.get('open_project_in_new_window', False)
        if new_window:
            sublime.run_command('new_window')
            window = sublime.windows()[-1]
        else:
            window = self.window
        stino.main.open_sketch(window, sketch_path)


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
        stino.main.handle_sketch(self.view, stino.main.build_sketch)


class UploadSketchCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        stino.main.handle_sketch(self.view, stino.main.upload_sketch)


class UploadUsingProgrammerCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        stino.main.handle_sketch(self.view, stino.main.upload_sketch,
                                 using_programmer=True)


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


class ToggleBareGccOnlyCommand(sublime_plugin.WindowCommand):
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
        stino.main.change_board(self.window, board_id)

    def is_checked(self, board_id):
        target_board_id = stino.settings.get('target_board_id', '')
        return board_id == target_board_id


class SelectSubBoardCommand(sublime_plugin.WindowCommand):
    def run(self, option_index, sub_board_id):
        stino.main.change_sub_board(self.window, option_index, sub_board_id)

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
        stino.main.set_status(self.window.active_view())

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


class ToggleOpenProjectInNewWindowCommand(sublime_plugin.WindowCommand):
    def run(self):
        new_window = stino.settings.get('open_project_in_new_window', False)
        stino.settings.set('open_project_in_new_window', not new_window)

    def is_checked(self):
        new_window = stino.settings.get('open_project_in_new_window', False)
        return new_window


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


class ShowItemListCommand(sublime_plugin.WindowCommand):
    def run(self, item_type):
        print(item_type)
