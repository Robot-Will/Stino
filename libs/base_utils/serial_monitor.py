#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import threading
import serial
from. import task_queue


class SerialMonitor:
    """."""

    def __init__(self, port, baudrate, consumer):
        """."""
        self._is_alive = False
        self._is_ready = False
        self._msg_queue = task_queue.TaskQueue(consumer)
        self._port = port
        self._baudrate = baudrate

        self.ser = serial.Serial()
        self.ser.port = self._port
        self.ser.baudrate = self._baudrate

    def _check_ready(self):
        """."""
        try:
            self.ser.open()
        except serial.SerialException:
            self.ser = serial.Serial()
            self.ser.port = self._port
            self.ser.baudrate = self._baudrate
            try:
                self.ser.open()
            except serial.SerialException:
                self._is_ready = False
            else:
                self._is_ready = True
        else:
            self._is_ready = True

    def start(self):
        """."""
        self._check_ready()
        if not self._is_alive and self._is_ready:
            self._is_alive = True
            thread = threading.Thread(target=self._run)
            thread.start()

    def _run(self):
        """."""
        is_normal = True
        while self._is_alive:
            try:
                number = self.ser.in_waiting
            except serial.SerialException:
                is_normal = False
                self._is_alive = False
                break
            else:
                if number > 0:
                    text = self.ser.read(number)
                    text = text.decode('utf-8', 'replace')
                    self._msg_queue.put(text)
        if is_normal:
            self.ser.close()

    def stop(self):
        """."""
        self._is_alive = False

    def send(self, text):
        """."""
        if self._is_alive:
            self._msg_queue.put(text)
            self.ser.write(text.encode('utf-8', 'replace'))

    def is_running(self):
        """."""
        return self._is_alive
