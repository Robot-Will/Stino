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

import time
import threading

from . import sys_info
from . import i18n

if sys_info.get_python_version() < 3:
    import Queue as queue
else:
    import queue


class MessageQueue(object):
    def __init__(self, console=None):
        self.i18n = i18n.I18N()
        self.queue = queue.Queue(0)
        self.is_alive = False
        self.console = console

    def put(self, text, *args):
        text = self.i18n.translate(text, *args)
        text = text.replace('\\n', '\n')
        self.queue.put(text)

    def start_print(self, one_time=False):
        if not self.is_alive:
            self.is_alive = True
            thread = threading.Thread(
                target=lambda: self.print_screen(one_time))
            thread.start()

    def print_screen(self, one_time=False):
        if one_time:
            self.print_once()
        else:
            while self.is_alive:
                self.print_once()
                time.sleep(0.01)

    def print_once(self):
        while not self.queue.empty():
            text = self.queue.get()
            if self.console:
                self.console.print_screen(text)
            else:
                print(text)
            time.sleep(0.01)

    def stop_print(self):
        while(not self.queue.empty()):
            time.sleep(2)
        self.is_alive = False
