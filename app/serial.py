#-*- coding: utf-8 -*-
# stino/serial.py

import os
import threading
import time

from . import constant
from . import pyserial

class SerialListener:
	def __init__(self, menu):
		self.menu = menu
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
			self.serial_list = getSerialPortList()
			if self.serial_list != pre_serial_list:
				self.menu.refresh()
			time.sleep(1)

	def stop(self):
		self.is_alive = False

def getSerialPortList():
	serial_port_list = []
	has_ports = False
	if constant.sys_platform == "windows":
		if constant.sys_version < 3:
			import _winreg as winreg
		else:
			import winreg
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except WindowsError:
			pass

		if has_ports:
			for i in range(128):
				try:
					name,value,type = winreg.EnumValue(reg,i)
				except WindowsError:
					pass
				else:
					serial_port_list.append(value)
	else:
		if constant.sys_platform == 'osx':
			dev_names = ['tty.', 'cu.']
		else:
			dev_names = ['ttyACM', 'ttyUSB']
		
		serial_port_list = []
		dev_path = '/dev'
		dev_file_list = os.listdir(dev_path)
		for dev_file in dev_file_list:
			for dev_name in dev_names:
				if dev_name in dev_file:
					dev_file_path = os.path.join(dev_path, dev_file)
					serial_port_list.append(dev_file_path)
	return serial_port_list

def isSerialAvailable(serial_port):
	state = False
	serial = pyserial.Serial()
	serial.port = serial_port
	try:
		serial.open()
	except pyserial.serialutil.SerialException:
		pass
	except UnicodeDecodeError:
		pass
	else:
		if serial.isOpen():
			state = True
			serial.close()
	return state

def getSelectedSerialPort():
	serial_list = getSerialPortList()
	serial_port_id = constant.sketch_settings.get('serial_port', -1)

	serial_port = 'no_serial_port'
	if serial_list:
		try:
			serial_port = serial_list[serial_port_id]
		except IndexError:
			serial_port = serial_list[0]
	return serial_port