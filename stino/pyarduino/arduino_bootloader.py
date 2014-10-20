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
from . import arduino_info
from . import arduino_target_params
from . import arduino_compiler


class Bootloader(object):
    def __init__(self, console=None):
        self.message_queue = base.message_queue.MessageQueue(console)
        target_params_info = arduino_target_params.TargetParamsInfo()
        self.params = target_params_info.get_params()

    def burn(self):
        self.message_queue.start_print()
        build_thread = threading.Thread(target=self.start_burn)
        build_thread.start()

    def start_burn(self):
        self.message_queue.put('[Start burning bootloader...]\n')
        self.prepare_serial_port()
        self.prepare_cmds()
        print(self.cmds)
        self.exec_burn_cmds()
        if not self.error_occured:
            self.message_queue.put('[Done burning bootloader.]\n')
        time.sleep(20)
        self.message_queue.stop_print()

    def prepare_serial_port(self):
        settings = base.settings.get_arduino_settings()
        self.upload_port = settings.get('serial_port', 'no_serial')
        self.params['serial.port'] = self.upload_port
        if self.upload_port.startswith('/dev/'):
            self.upload_port_file = self.upload_port[5:]
        else:
            self.upload_port_file = self.upload_port
        self.params['serial.port.file'] = self.upload_port_file
        self.params = arduino_target_params.replace_param_values(self.params)

        if self.upload_port in base.serial_monitor.serials_in_use:
            serial_monitor = base.serial_monitor.serial_monitor_dict.get(
                self.upload_port, None)
            if serial_monitor:
                serial_monitor.stop()

    def prepare_cmds(self):
        self.cmds = []
        erase_cmd = self.params.get('erase.pattern', '')
        burn_cmd = self.params.get('bootloader.pattern', '')
        self.cmds.append(erase_cmd)
        self.cmds.append(burn_cmd)

    def exec_burn_cmds(self):
        settings = base.settings.get_arduino_settings()
        show_upload_output = settings.get('upload_verbose', False)
        info = arduino_info.get_arduino_info()
        working_dir = info.get_ide_dir().get_path()
        self.error_occured = arduino_compiler.exec_cmds(working_dir, self.cmds,
                                                        self.message_queue,
                                                        show_upload_output)
