#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time
import threading
import platform
import glob
import serial
from . import decos


def list_serial_ports():
    """."""
    try:
        from serial.tools.list_ports import comports
    except ImportError:
        pass
    serial_ports = [port for port, d, h in comports() if port]

    if not serial_ports and platform.system() == "Darwin":
        for port in glob("/dev/tty.*"):
            serial_ports.append(port)
    return serial_ports


@decos.singleton
class SerialListener(object):
    """."""

    def __init__(self, call_back=None):
        """."""
        self.is_alive = False
        self.call_back = call_back

    def start(self):
        """."""
        if not self.is_alive:
            self.is_alive = True
            listener_thread = threading.Thread(target=self.update)
            listener_thread.start()

    def update(self):
        """."""
        pre_serial_ports = []
        while self.is_alive:
            serial_ports = list_serial_ports()
            if serial_ports != pre_serial_ports:
                pre_serial_ports = serial_ports
                if callable(self.call_back):
                    self.call_back(serial_ports)
            time.sleep(1)

    def stop(self):
        """."""
        self.is_alive = False
