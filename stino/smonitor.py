#-*- coding: utf-8 -*-
# stino/smonitor.py

import sublime
import os
import serial
import threading
import time

from stino import const
from stino import stpanel
from stino import actions

if const.sys_platform == 'windows':
	import _winreg

def getBaudrateList():
	baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
	return baudrate_list

def genSerialPortList():
	serial_port_list = []
	has_ports = False
	if const.sys_platform == "windows":
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except WindowsError:
			pass

		if has_ports:
			for i in xrange(128):
				try:
					name,value,type = _winreg.EnumValue(reg,i)
					serial_port_list.append(value)
				except WindowsError:
					pass
	else:
		if const.sys_platform == 'osx':
			dev_names = ['tty.*']
		else:
			dev_names = ['ttyACM*', 'ttyUSB*']
		for dev_name in dev_names:
			cmd = 'ls /dev/%s' % dev_name
			serial_port_list += [f.strip() for f in os.popen(cmd).readlines()]
	return serial_port_list

def isSerialPortAvailable(serial_port):
	state = False
	ser = serial.Serial()
	ser.port = serial_port
	try:
		ser.open()
	except serial.serialutil.SerialException:
		pass
	except UnicodeDecodeError:
		pass
	else:
		if ser.isOpen():
			state = True
			ser.close()
	return state

def isMonitorView(view):
	state = ''
	name = view.name()
	if name:
		if 'Serial Monitor - ' in name:
			state = True
	return state

class SerialPortListener:
	def __init__(self):
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
			self.serial_list = genSerialPortList()
			if self.serial_list != pre_serial_list:
				sublime.set_timeout(actions.updateSerialMenu, 0)
			time.sleep(0.5)

	def stop(self):
		if self.is_alive:
			self.is_alive = False

class SerialMonitor:
	def __init__(self, serial_port):
		self.serial_port = serial_port
		self.name = 'Serial Monitor - ' + self.serial_port
		self.view = stpanel.MonitorView(self.name)
		self.view.toggleWordWrap()
		self.baudrate = int(const.settings.get('baudrate'))
		self.ser = serial.Serial()
		self.ser.baudrate = self.baudrate
		self.setSerialPort(self.serial_port)
		self.is_alive = False

	def setSerialPort(self, serial_port):
		self.serial_port = serial_port
		self.ser.port = self.serial_port
		
	def start(self):
		self.view.raiseToFront()
		if not self.is_alive:
			self.ser.open()
			self.is_alive = True
			monitor_thread = threading.Thread(target=self.receive)
			monitor_thread.start()

	def stop(self):
		if self.is_alive:
			self.is_alive = False

	def receive(self):
		while self.is_alive:
			number = self.ser.inWaiting()
			if number > 0:
				in_text = self.ser.read(number)
				self.view.addText(in_text)
			time.sleep(0.01)
		self.ser.close()

	def send(self, out_text):
		self.ser.write(out_text.encode('utf-8'))
		self.view.addText(out_text)
		self.view.addText('\n')