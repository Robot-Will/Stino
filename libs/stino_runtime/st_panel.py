#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sublime

from base_utils import sys_info


class StPanel:
    """."""

    def __init__(self, name='stino_panel'):
        """."""
        self._name = name
        self._window = sublime.active_window()
        python_version = sys_info.get_python_version()
        if python_version < 3:
            self._panel = self._window.get_output_panel(self._name)
        else:
            self._panel = self._window.create_output_panel(self._name)
        self._panel.set_name(self._name)
        self._panel.run_command('toggle_setting', {'setting': 'word_wrap'})

        view = self._window.active_view()
        color_scheme = view.settings().get('color_scheme', '')
        if not color_scheme:
            color_scheme = 'Packages/Color Scheme - Default/Eiffel.tmTheme'
        self._panel.settings().set('color_scheme', color_scheme)

    def write(self, text):
        """."""
        view = self._window.active_view()
        self._panel.set_read_only(False)
        self._panel.run_command('stino_panel_write', {'text': text})
        panel_name = 'output.' + self._name
        self._window.run_command("show_panel", {"panel": panel_name})
        self._panel.set_read_only(True)
        self._window.focus_view(view)
