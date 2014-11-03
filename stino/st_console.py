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

import sublime

from . import pyarduino


class Console:
    def __init__(self, window, name='stino_console'):
        self.name = name
        self.window = window
        python_version = pyarduino.base.sys_info.get_python_version()
        if python_version < 3:
            self.panel = self.window.get_output_panel(self.name)
        else:
            self.panel = self.window.create_output_panel(self.name)
        self.panel.set_name(self.name)
        self.panel.run_command('toggle_setting', {'setting': 'word_wrap'})

    def print_screen(self, text):
        sublime.set_timeout(lambda: self.println(text), 0)

    def println(self, text):
        view = self.window.active_view()
        color_scheme = view.settings().get('color_scheme', '')
        if not color_scheme:
            color_scheme = 'Packages/Color Scheme - Default/Eiffel.tmTheme'
        self.panel.settings().set('color_scheme', color_scheme)

        self.panel.set_read_only(False)
        self.panel.run_command('panel_output', {'text': text})
        panel_name = 'output.' + self.name
        self.window.run_command("show_panel", {"panel": panel_name})
        self.panel.set_read_only(True)


class MonitorView:
    def __init__(self, window, serial_port):
        self.name = 'Serial Monitor - ' + serial_port
        self.window, self.view = find_in_opend_view(self.name)

        if self.view is None:
            self.window = window
            self.view = self.window.new_file()
            self.view.set_name(self.name)
        self.view.run_command('toggle_setting', {'setting': 'word_wrap'})
        self.view.set_scratch(True)
        self.window.focus_view(self.view)

    def print_screen(self, text):
        sublime.set_timeout(lambda: self.println(text), 0)

    def println(self, text):
        self.view.set_read_only(False)
        self.view.run_command('panel_output', {'text': text})
        self.view.set_read_only(True)


def find_in_opend_view(view_name):
    opened_view = None
    found = False
    windows = sublime.windows()
    for window in windows:
        views = window.views()
        for view in views:
            name = view.name()
            if name == view_name:
                opened_view = view
                found = True
                break
        if found:
            break
    return (window, opened_view)


def is_monitor_view(view):
    state = ''
    name = view.name()
    if name and 'Serial Monitor - ' in name:
        state = True
    return state
