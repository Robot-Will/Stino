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

from . import pyserial
from . import settings
from . import message_queue

serials_in_use = []
serial_monitor_dict = {}


class SerialMonitor(object):
    def __init__(self, serial_port, console=None):
        super(SerialMonitor, self).__init__()
        self.port = serial_port
        self.serial = pyserial.Serial()
        self.serial.port = serial_port
        self.queue = message_queue.MessageQueue(console)
        self.arduino_settings = settings.get_arduino_settings()
        self.is_alive = False

    def is_running(self):
        return self.is_alive

    def start(self):
        self.queue.start_print()
        if not self.is_alive:
            baudrate = self.arduino_settings.get('baudrate', 9600)
            self.serial.baudrate = baudrate
            if self.is_serial_available():
                self.serial.open()
                self.is_alive = True
                monitor_thread = threading.Thread(target=self.receive)
                monitor_thread.start()
            else:
                self.stop()

    def stop(self):
        self.is_alive = False
        self.queue.stop_print()

    def receive(self):
        length_before = 0
        while self.is_alive:
            number = self.serial.inWaiting()
            if number > 0:
                in_text = self.serial.read(number)
                length_in_text = len(in_text)
                in_text = convert_mode(in_text, length_before)
                self.queue.put(in_text)

                length_before += length_in_text
                length_before %= 20
            time.sleep(0.01)
        self.serial.close()

    def send(self, out_text):
        line_ending = self.arduino_settings.get('line_ending', '\n')
        out_text += line_ending

        self.queue.put('[SEND] {0}\\n', out_text)
        out_text = out_text.encode('utf-8', 'replace')
        self.serial.write(out_text)


    def is_serial_available(self):
        state = False
        serial = pyserial.Serial()
        serial.port = self.port
        try:
            serial.open()
        except Exception as e:
            self.queue.put(str(e), self.port)
        else:
            if serial.isOpen():
                state = True
                serial.close()
        return state



def convert_mode(in_text, str_len=0):
    arduino_settings = settings.get_arduino_settings()
    text = u''
    display_mode = arduino_settings.get('display_mode', 'Text')
    if display_mode == 'Ascii':
        for character in in_text:
            text += chr(character)
    elif display_mode == 'Hex':
        for (index, character) in enumerate(in_text):
            text += u'%02X ' % character
            if (index + str_len + 1) % 8 == 0:
                text += '\t'
            if (index + str_len + 1) % 16 == 0:
                text += '\n'
    else:
        text = in_text.decode('utf-8', 'replace')
    return text


def convert_to_ascii_mode():
    pass


def convert_to_hex_mode():
    pass