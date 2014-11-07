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

import glob
import time

from . import pyserial
from . import sys_info
from . import settings
from . import board_port


if sys_info.get_os_name() == 'windows':
    if sys_info.get_python_version() < 3:
        import _winreg as winreg
    else:
        import winreg


def list_board_ports():
    board_ports = []
    serial_ports = list_serial_ports()
    for serial_port in serial_ports:
        board_name = resolve_device_attached_to(serial_port)
        label = serial_port
        if board_name:
            label += '(%s)' % board_name
        port = board_port.BoardPort()
        port.set_address(serial_port)
        port.set_protocol('serial')
        port.set_board_name(board_name)
        port.set_label(label)
        board_ports.append(port)
    return board_ports


def resolve_device_attached_to(serial_port):
    device_name = ''
    return device_name


def list_serial_ports():
    os_name = sys_info.get_os_name()
    if os_name == "windows":
        serial_ports = list_win_serial_ports()
    elif os_name == 'osx':
        serial_ports = list_osx_serial_ports()
    else:
        serial_ports = list_linux_serial_ports()
    serial_ports.sort()
    return serial_ports


def list_win_serial_ports():
    serial_ports = []
    has_ports = False
    path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
    try:
        reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path,)
        has_ports = True
    except WindowsError:
        pass

    if has_ports:
        for i in range(128):
            try:
                name, value, type = winreg.EnumValue(reg, i)
            except WindowsError:
                pass
            else:
                serial_ports.append(value)
    return serial_ports


def list_osx_serial_ports():
    serial_ports = []
    dev_path = '/dev/'
    dev_names = ['tty.usbserial-*', 'cu.usbserial-*',
                 'tty.usbmodem*', 'cu.usbmodem*']
    for dev_name in dev_names:
        pattern = dev_path + dev_name
        serial_ports += glob.glob(pattern)
    return serial_ports


def list_linux_serial_ports():
    serial_ports = []
    dev_path = '/dev/'
    dev_names = ['ttyACM*', 'ttyUSB*']
    for dev_name in dev_names:
        pattern = dev_path + dev_name
        serial_ports += glob.glob(pattern)
    return serial_ports


def check_target_serial_port():
    arduino_settings = settings.get_arduino_settings()
    serial_ports = list_serial_ports()
    target_serial_port = arduino_settings.get('serial_port', 'no_serial')
    if serial_ports and not target_serial_port in serial_ports:
        target_serial_port = serial_ports[0]
        arduino_settings.set('serial_port', target_serial_port)
    return target_serial_port


def touch_port(serial_port, baudrate):
    ser = pyserial.Serial()
    ser.port = serial_port
    ser.baudrate = baudrate
    ser.bytesize = pyserial.EIGHTBITS
    ser.stopbits = pyserial.STOPBITS_ONE
    ser.parity = pyserial.PARITY_NONE
    ser.open()
    ser.setDTR(True)
    time.sleep(0.022)
    ser.setDTR(False)
    ser.close()
    time.sleep(1)


def wait_for_port(upload_port, before_ports, message_queue):
    elapsed = 0
    os_name = sys_info.get_os_name()
    new_port = 'no_serial'
    while elapsed < 1000:
        now_ports = list_serial_ports()
        diff_ports = remove_ports(now_ports, before_ports)
        message_queue.put('Ports {{0}}/{{1}} => {{2}}\\n', before_ports,
                          now_ports, diff_ports)
        if diff_ports:
            new_port = diff_ports[0]
            message_queue.put('Found new upload port: {0}.\\n', new_port)
            break

        before_ports = now_ports
        time.sleep(0.25)
        elapsed += 25

        if ((os_name != 'windows' and elapsed >= 500) or elapsed >= 5000)\
                and (upload_port in now_ports):
            new_port = upload_port
            message_queue.put('Uploading using selected port: {0}.\\n',
                              upload_port)
            break

    if new_port == 'no_serial':
        txt = "Couldn't find a Leonardo on the selected port. "
        txt += 'Check that you have the correct port selected. '
        txt += "If it is correct, try pressing the board's reset button "
        txt += 'after initiating the upload.\\n'
        message_queue.put(txt)
    return new_port


def remove_ports(now_ports, before_ports):
    ports = now_ports[:]
    for port in before_ports:
        if port in ports:
            ports.remove(port)
    return ports
