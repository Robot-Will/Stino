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
from serial.tools.list_ports import comports
from . import decos


def list_serial_ports():
    """."""
    serial_ports = [port for port, d, h in comports() if port]

    if not serial_ports and platform.system() == "Darwin":
        for port in glob("/dev/tty.*"):
            serial_ports.append(port)
    return serial_ports


def get_serials_info():
    """."""
    serials_info = {'ports': []}
    for port, desc, hwid in comports():
        if port:
            serials_info['ports'].append(port)
            info = {'port': port, 'description': desc, 'hwid': hwid}
            serials_info[port] = info

    if not serials_info['ports'] and platform.system() == "Darwin":
        for port in glob("/dev/tty.*"):
            serials_info['ports'].append(port)
            info = {"port": port, "description": "", "hwid": ""}
            serials_info[port] = info
    return serials_info


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
