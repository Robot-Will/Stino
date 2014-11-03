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

import threading
import time

from . import base
from . import arduino_compiler
from . import arduino_target_params


class Uploader(object):
    def __init__(self, path, console=None):
        self.message_queue = base.message_queue.MessageQueue(console)
        self.compiler = arduino_compiler.Compiler(path, console)
        self.error_occured = False
        self.params = {}
        self.do_touch = False
        self.wait_for_upload_port = False

    def upload(self, using_programmer=False):
        self.compiler.build()
        self.message_queue.start_print()
        upload_thread = threading.Thread(
            target=lambda: self.start_upload(using_programmer))
        upload_thread.start()

    def start_upload(self, using_programmer):
        while not self.compiler.is_finished():
            time.sleep(1)
        if not self.compiler.has_error():
            self.message_queue.put('[Stino - Start uploading...]\\n')
            self.params = self.compiler.get_params()
            self.prepare_upload_port(using_programmer)
            self.prepare_cmd(using_programmer)
            self.exec_cmd()
            if not self.error_occured:
                self.retouch_serial_port()
                self.message_queue.put('[Stino - Done uploading.]\\n')
        time.sleep(20)
        self.message_queue.stop_print()

    def prepare_upload_port(self, using_programmer):
        settings = base.settings.get_arduino_settings()
        self.upload_port = settings.get('serial_port', 'no_serial')
        self.params['serial.port'] = self.upload_port
        if self.upload_port.startswith('/dev/'):
            self.upload_port_file = self.upload_port[5:]
        else:
            self.upload_port_file = self.upload_port
        self.params['serial.port.file'] = self.upload_port_file

        if self.upload_port in base.serial_monitor.serials_in_use:
            serial_monitor = base.serial_monitor.serial_monitor_dict.get(
                self.upload_port, None)
            if serial_monitor:
                serial_monitor.stop()

        if not using_programmer or not self.params.get('upload.protocol'):
            bootloader_file = self.params.get('bootloader.file', '')
            if 'caterina' in bootloader_file.lower():
                self.do_touch = True
            elif self.params.get('upload.use_1200bps_touch') == 'true':
                self.do_touch = True

            if self.params.get('upload.wait_for_upload_port') == 'true':
                self.wait_for_upload_port = True

            if self.do_touch:
                before_ports = base.serial_port.list_serial_ports()
                if self.upload_port in before_ports:
                    text = 'Forcing reset using 1200bps open/close '
                    text += 'on port {0}.\\n'
                    self.message_queue.put(text, self.upload_port)
                    base.serial_port.touch_port(self.upload_port, 1200)
                if self.wait_for_upload_port:
                    if base.sys_info.get_os_name() != 'osx':
                        time.sleep(0.4)
                    self.upload_port = base.serial_port.wait_for_port(
                        self.upload_port, before_ports, self.message_queue)
                else:
                    time.sleep(4)
                self.params['serial.port'] = self.upload_port

                if self.upload_port.startswith('/dev/'):
                    self.upload_port_file = self.upload_port[5:]
                else:
                    self.upload_port_file = self.upload_port
                self.params['serial.port.file'] = self.upload_port_file
        self.params = arduino_target_params.replace_param_values(self.params)

    def prepare_cmd(self, using_programmer):
        if not using_programmer or not self.params.get('upload.protocol'):
            self.cmd = self.params.get('upload.pattern')
        else:
            self.cmd = self.params.get('program.pattern')

        settings = base.settings.get_arduino_settings()
        verify_code = settings.get('verify_code', False)
        if verify_code:
            self.cmd += ' -V'

    def exec_cmd(self):
        settings = base.settings.get_arduino_settings()
        show_upload_output = settings.get('upload_verbose', False)
        working_dir = self.compiler.get_ide_path()
        self.error_occured = arduino_compiler.exec_cmds(
            working_dir, [self.cmd], self.message_queue, show_upload_output)

    def retouch_serial_port(self):
        if self.do_touch:
            if self.wait_for_upload_port:
                time.sleep(0.1)
                timeout = time.time() + 2
                while timeout > time.time():
                    ports = base.serial_port.list_serial_ports()
                    if self.upload_port in ports:
                        base.serial_port.touch_port(self.upload_port, 9600)
                        break
                    time.sleep(0.25)
            else:
                base.serial_port.touch_port(self.upload_port, 9600)
