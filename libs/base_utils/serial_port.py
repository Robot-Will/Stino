#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time
import threading
import glob
import serial
from serial.tools.list_ports import comports
from . import sys_info


def list_serial_ports():
    """."""
    serial_ports = [port for port, d, h in comports() if port]
    os_name = sys_info.get_os_name()
    if not serial_ports and os_name == "osx":
        for port in glob("/dev/tty.*"):
            serial_ports.append(port)
    return serial_ports


def list_network_ports():
    """."""
    return []


def get_serials_info():
    """."""
    serials_info = {'ports': []}
    for port, desc, hwid in comports():
        if port:
            serials_info['ports'].append(port)
            info = {'port': port, 'description': desc, 'hwid': hwid}

            vid = ''
            pid = ''
            if hwid:
                hwid_infos = hwid.split()
                for hwid_info in hwid_infos:
                    if hwid_info.startswith('VID') and '=' in hwid_info:
                        vid_pid = hwid_info.split('=')[-1]
                        if ':' in vid_pid:
                            vid, pid = vid_pid.split(':')
                            vid = '0x' + vid.strip()
                            pid = '0x' + pid.strip()
                        break
            info['vid'] = vid
            info['pid'] = pid
            serials_info[port] = info

    os_name = sys_info.get_os_name()
    if not serials_info['ports'] and os_name == 'osx':
        for port in glob('/dev/tty.*'):
            serials_info['ports'].append(port)
            info = {'port': port, 'description': '', 'hwid': ''}
            info['vid'] = ''
            info['pid'] = ''
            serials_info[port] = info
    return serials_info


def get_serial_info(port):
    """."""
    serials_info = get_serials_info()
    info = serials_info.get(port, {})
    return info


def is_available(serial_port):
    """."""
    is_avail = True
    ser = serial.Serial()
    ser.port = serial_port
    try:
        ser.open()
    except (serial.SerialException, UnicodeDecodeError):
        is_avail = False
    else:
        ser.close()
    return is_avail


class PortListener(object):
    """."""

    def __init__(self, list_func, call_back=None):
        """."""
        self._is_alive = False
        self._list_func = list_func
        self._call_back = call_back

    def start(self):
        """."""
        if not self._is_alive:
            self._is_alive = True
            listener_thread = threading.Thread(target=self._update)
            listener_thread.start()

    def _update(self):
        """."""
        pre_serial_ports = []
        while self._is_alive:
            serial_ports = self._list_func()
            if serial_ports != pre_serial_ports:
                pre_serial_ports = serial_ports
                if callable(self._call_back):
                    self._call_back(serial_ports)
            time.sleep(1)

    def stop(self):
        """."""
        self._is_alive = False


def flush_serial_buffer(serial_port):
    """."""
    ser = serial.Serial(serial_port)
    ser.flushInput()
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(0.1)
    ser.setDTR(True)
    ser.setRTS(True)
    ser.close()


def touch_port(serial_port, baudrate):
    """."""
    ser = serial.Serial()
    ser.port = serial_port
    ser.baudrate = baudrate
    ser.bytesize = serial.EIGHTBITS
    ser.stopbits = serial.STOPBITS_ONE
    ser.parity = serial.PARITY_NONE
    try:
        ser.open()
    except serial.SerialException:
        pass
    else:
        ser.setDTR(True)
        time.sleep(0.022)
        ser.setDTR(False)
        ser.close()
        time.sleep(0.4)


def auto_reset(serial_port):
    """."""
    ser = serial.Serial()
    ser.port = serial_port
    try:
        ser.open()
    except serial.SerialException:
        pass
    else:
        ser.setRTS(False)
        ser.setDTR(False)
        ser.setDTR(True)
        time.sleep(0.05)
        ser.setDTR(False)
        ser.setRTS(True)
        ser.setDTR(True)
        time.sleep(0.05)
        ser.setDTR(False)
        time.sleep(0.05)
        ser.write('1EAF')
        time.sleep(0.05)
        ser.close()


def wait_for_new_port(upload_port, before_ports):
    """."""
    new_port = ''
    elapsed = 0
    os_name = sys_info.get_os_name()
    while elapsed < 10:
        now_ports = list_serial_ports()
        diff = list(set(now_ports) - set(before_ports))
        if diff:
            new_port = diff[0]
            break

        before_ports = now_ports
        time.sleep(0.25)
        elapsed += 0.25

        if upload_port in now_ports:
            if elapsed >= 5 and os_name != 'windows':
                new_port = upload_port
                break

    if not new_port:
        text = "Couldn't find a Leonardo on the selected port. "
        text += 'Check that you have the correct port selected. '
        text += "If it is correct, try pressing the board's reset "
        text += 'button after initiating the upload.'
        print(text)
    return new_port


def auto_detect_upload_port(board_info):
    """."""
    upload_port = None
    vid = board_info.get('build.vid', '')
    pid = board_info.get('build.pid', '')
    board_hwid = ("%s:%s" % (vid, pid)).replace('0x', '')

    serials_info = get_serials_info()
    ports = serials_info.get('ports', [])
    for port in ports:
        port_info = serials_info.get(port, {})
        port_hwid = port_info.get('hwid', '')
        if 'VID:PID' in port_hwid:
            if board_hwid in port_hwid:
                upload_port = port
                break
    return upload_port


def check_do_touch(board_info):
    """."""
    do_touch = False
    bootloader_file = board_info.get('bootloader.file', '')
    if 'caterina' in bootloader_file.lower():
        do_touch = True
    elif board_info.get('upload.use_1200bps_touch') == 'true':
        do_touch = True
    return do_touch


def checke_do_reset(board_info):
    """."""
    return board_info.get('upload.auto_reset', '') == 'true'


def prepare_upload_port(upload_port, do_touch=False, do_reset=False):
    """."""
    if do_touch:
        before_ports = list_serial_ports()
        if upload_port in before_ports:
            text = 'Forcing reset using 1200bps open/close '
            text += 'on port %s.' % upload_port
            print(text)
            touch_port(upload_port, 1200)

            if sys_info.get_os_name() != 'osx':
                time.sleep(0.4)
            upload_port = wait_for_new_port(upload_port, before_ports)

    if do_reset:
        text = 'Resetting to bootloader via DTR pulse\\n'
        print(text)
        auto_reset(upload_port)
    return upload_port


def restore_serial_port(upload_port, baudrate, timeout=4):
    """."""
    time.sleep(0.1)
    before_time = time.time()
    while time.time() - before_time < timeout:
        ports = list_serial_ports()
        if upload_port in ports:
            touch_port(upload_port, baudrate)
        else:
            break
        time.sleep(0.25)


def get_serial_file(port):
    """."""
    serial_file = port
    if serial_file and '/dev/' in serial_file:
        serial_file = serial_file[5:]
    return serial_file
