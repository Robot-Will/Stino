#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


class StMonitorView:
    """."""

    def __init__(self, win, port, arduino_info, view=None):
        """."""
        self._name = '%s - Serial Monitor' % port
        if view:
            self._view = view
        else:
            self._view = win.new_file()
            self._view.set_name(self._name)
        self._info = arduino_info

    def get_view(self):
        """."""
        return self._view

    def write(self, text=''):
        """."""
        do_scroll = self._info['selected'].get('monitor_auto_scroll')
        self._view.run_command('stino_panel_write',
                               {'text': text, 'do_scroll': do_scroll})
