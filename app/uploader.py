#-*- coding: utf-8 -*-
# stino/uploader.py

import threading
import time

from . import constant
from . import compiler
from . import console
from . import serial
from . import pyserial

class Uploader:
	def __init__(self, args, cur_compiler, mode = 'upload'):
		self.args = args.getArgs()
		self.mode = mode
		self.compiler = cur_compiler
		self.command_list = []
		self.output_console = cur_compiler.getOutputConsole()
		self.no_error = True

		upload_command_text = ''
		if mode == 'upload':
			if 'upload.pattern' in self.args:
				upload_command_text = self.args['upload.pattern']
		elif mode == 'programmer':
			if 'program.pattern' in self.args:
				upload_command_text = self.args['program.pattern']

		if upload_command_text:
			upload_command = compiler.Command(upload_command_text)
			upload_command.setOutputText('Uploading...\n')
			self.command_list.append(upload_command)

		if 'reboot.pattern' in self.args:
			reboot_command_text = self.args['reboot.pattern']
			reboot_command = compiler.Command(reboot_command_text)
			self.command_list.append(reboot_command)

	def run(self):
		if self.command_list:
			upload_thread = threading.Thread(target=self.upload)
			upload_thread.start()
		else:
			self.no_error = False

	def upload(self):
		while not self.compiler.isFinished():
			time.sleep(0.5)
		if not self.compiler.noError():
			return

		serial_port = serial.getSelectedSerialPort()
		
		serial_monitor = None
		if serial_port in constant.serial_in_use_list:
			serial_monitor = constant.serial_monitor_dict[serial_port]
			serial_monitor.stop()

		force_to_reset = False
		if self.mode == 'upload':
			if 'bootloader.file' in self.args:
				if 'caterina' in self.args['bootloader.file'].lower():
					force_to_reset = True
			elif self.args.get('upload.use_1200bps_touch', 'false') == 'true':
				force_to_reset = True

			if force_to_reset:
				pre_serial_port = serial_port
				wait_for_upload_port = self.args.get('upload.wait_for_upload_port', 'false') == 'true'
				serial_port = resetSerial(pre_serial_port, self.output_console, wait_for_upload_port)
				if self.args['cmd'] != 'avrdude':
					if serial_port.startswith('/dev/'):
						serial_port = serial_port[5:]
				if serial_port:
					for cur_command in self.command_list:
						command_text = cur_command.getCommand()
						command_text = command_text.replace(pre_serial_port, serial_port)
						cur_command.setCommand(command_text)

		for cur_command in self.command_list:
			return_code = cur_command.run(self.output_console)
			if return_code > 0:
				self.output_console.printText('[Stino - Error %d]\n' % return_code)
				self.no_error = False
				break

		if self.no_error:
			self.output_console.printText('[Stino - Done uploading.]\n')

		if force_to_reset:
			time.sleep(5)

		if serial_monitor:
			serial_monitor.start()

def touchSerialPort(serial_port, baudrate):
	cur_serial = pyserial.Serial()
	cur_serial.port = serial_port
	cur_serial.baudrate = baudrate
	cur_serial.bytesize = pyserial.EIGHTBITS
	cur_serial.stopbits = pyserial.STOPBITS_ONE
	cur_serial.parity = pyserial.PARITY_NONE
	cur_serial.open()
	cur_serial.close()

def resetSerial(serial_port, output_console, wait_for_upload_port):
	show_upload_output = constant.sketch_settings.get('show_upload_output', False)

	caterina_serial_port = ''
	before_serial_list = serial.getSerialPortList()
	if serial_port in before_serial_list:
		non_serial_list = before_serial_list[:]
		non_serial_list.remove(serial_port)

		if show_upload_output:
			msg = 'Forcing reset using 1200bps open/close on port %s.\n' % serial_port
			output_console.printText(msg)
		touchSerialPort(serial_port, 1200)

		if not wait_for_upload_port:
			time.sleep(0.4)
			return serial_port

		# Scanning for available ports seems to open the port or
		# otherwise assert DTR, which would cancel the WDT reset if
		# it happened within 250 ms. So we wait until the reset should
		# have already occured before we start scanning.
		if constant.sys_platform == 'windows':
			time.sleep(3)
		else:
			time.sleep(0.3)

		# Wait for a port to appear on the list
		elapsed = 0
		while (elapsed < 10000):
			now_serial_list = serial.getSerialPortList()
			diff_serial_list = diffList(now_serial_list, non_serial_list)

			if show_upload_output:
				msg = 'Ports {%s}/{%s} => {%s}\n' % (before_serial_list, now_serial_list, 
					diff_serial_list)
				output_console.printText(msg)
			if len(diff_serial_list) > 0:
				caterina_serial_port = diff_serial_list[0]
				if show_upload_output:
					msg = 'Found new upload port: %s.\n' % caterina_serial_port
					output_console.printText(msg)
				break

			# Keep track of port that disappears
			# before_serial_list = now_serial_list
			time.sleep(0.25)
			elapsed += 250

			# On Windows, it can take a long time for the port to disappear and
			# come back, so use a longer time out before assuming that the selected
			# port is the bootloader (not the sketch).
			if (((constant.sys_platform != 'windows' and elapsed >= 500) 
				or elapsed >= 5000) and (serial_port in now_serial_list)):
				if show_upload_output:
					msg = 'Uploading using selected port: %s.\n' % serial_port
					output_console.printText(msg)
				caterina_serial_port = serial_port
				break

		if not caterina_serial_port:
			msg = 'Couldn\'t find a Leonardo on the selected port.\nCheck that you have the correct port selected.\nIf it is correct, try pressing the board\'s reset button after initiating the upload.\n'
			output_console.printText(msg)
	return caterina_serial_port

class Bootloader:
	def __init__(self, cur_project, args):
		self.args = args.getArgs()
		erase_command_text = self.args['erase.pattern']
		burn_command_text = self.args['bootloader.pattern']
		erase_command = compiler.Command(erase_command_text)
		burn_command = compiler.Command(burn_command_text)
		self.command_list = [erase_command, burn_command]
		self.output_console = console.Console(cur_project.getName())

	def start(self):
		upload_thread = threading.Thread(target=self.burn)
		upload_thread.start()

	def burn(self):
		for cur_command in self.command_list:
			return_code = cur_command.run(self.output_console)
			if return_code > 0:
				self.output_console.printText('[Error %d]\n' % return_code)
				break

def diffList(now_list, before_list):
	diff_list = now_list
	for before_item in before_list:
		if before_item in diff_list:
			diff_list.remove(before_item)
	return diff_list
