#!/usr/bin/env python
#-*- coding: utf-8 -*-

# 1. Copyright
# 2. Lisence
# 3. Author

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time
import threading

from . import deco
from . import serial_port


@deco.singleton
class SerialListener(object):
    def __init__(self, func=None):
        self.func = func
        self.serial_list = []
        self.is_alive = False

    def start(self):
        if not self.is_alive:
            self.is_alive = True
            listener_thread = threading.Thread(target=self.update)
            listener_thread.start()

    def update(self):
        while self.is_alive:
            pre_serial_list = self.serial_list
            self.serial_list = serial_port.list_serial_ports()
            if self.serial_list != pre_serial_list:
                serial_port.check_target_serial_port()
                if self.func:
                    self.func()
            time.sleep(1)

    def stop(self):
        self.is_alive = False
