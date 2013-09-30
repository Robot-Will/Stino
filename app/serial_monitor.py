#-*- coding: utf-8 -*-
# stino/serial_monitor.py

import threading
import time

import sublime

from . import constant
from . import serial
from . import pyserial

class MonitorView:
	def __init__(self, name = 'Serial Monitor'):
		self.name = name
		self.show_text = ''
		self.window = sublime.active_window()
		self.view = findInOpendView(self.name)
		if not self.view:
			self.view = self.window.new_file()
			self.view.set_name(self.name)
		self.raiseToFront()

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getWindow(self):
		return self.window

	def getView(self):
		return self.view

	def printText(self, text):
		self.show_text += text
		if constant.sys_version < 3: 
			show_thread = threading.Thread(target=self.show)
			show_thread.start()
		else:
			self.update()

	def show(self):
		sublime.set_timeout(self.update, 0)

	def update(self):
		if self.show_text:
			text = self.show_text
			self.view.run_command('panel_output', {'text': text})
			self.show_text = ''

	def raiseToFront(self):
		self.window.focus_view(self.view)

class SerialMonitor:
	def __init__(self, serial_port):
		self.port = serial_port
		self.serial = pyserial.Serial()
		self.serial.port = serial_port

		self.is_alive = False
		self.name = 'Serial Monitor - ' + serial_port
		self.view = MonitorView(self.name)

	def isRunning(self):
		return self.is_alive

	def start(self):
		if not self.is_alive:
			baudrate_id = constant.sketch_settings.get('baudrate', 4)
			baudrate = int(constant.baudrate_list[baudrate_id])
			self.serial.baudrate = baudrate
			if serial.isSerialAvailable(self.port):
				self.serial.open()
				self.is_alive = True
				monitor_thread = threading.Thread(target=self.receive)
				monitor_thread.start()
			else:
				display_text = 'Serial port {0} already in use. Try quitting any programs that may be using it.'
				msg = display_text
				msg = msg.replace('{0}', self.port)
				self.view.printText(msg)

	def stop(self):
		self.is_alive = False

	def receive(self):
		length_before = 0
		while self.is_alive:
			number = self.serial.inWaiting()
			if number > 0:
				in_text = self.serial.read(number)
				length_in_text = len(in_text)
				in_text = convertMode(in_text, length_before)
				self.view.printText(in_text)

				length_before += length_in_text
				length_before %= 20
			time.sleep(0.01)
		self.serial.close()

	def send(self, out_text):
		line_ending_id = constant.sketch_settings.get('line_ending', 0)
		line_ending = constant.line_ending_list[line_ending_id]
		out_text += line_ending
		
		self.view.printText('[SEND] ' + out_text + '\n')
		out_text = out_text.encode('utf-8', 'replace')
		self.serial.write(out_text)
		
def isMonitorView(view):
	state = ''
	name = view.name()
	if name:
		if 'Serial Monitor - ' in name:
			state = True
	return state

def findInOpendView(view_name):
	opened_view = None
	found = False
	windows = sublime.windows()
	for window in windows:
		views = window.views()
		for view in views:
			name = view.name()
			if name == view_name:
				opened_view = view
				found = True
				break
		if found:
			break
	return opened_view

def convertMode(in_text, str_len = 0):
	text = u''
	display_mode = constant.sketch_settings.get('display_mode', 0)
	if display_mode == 0:
		text = in_text.decode('utf-8', 'replace')
	elif display_mode == 1:
		for character in in_text:
			text += chr(character)
	elif display_mode == 2:
		for (index, character) in enumerate(in_text):
			text += u'%02X ' % character
			if (index + str_len + 1) % 10 == 0:
				text += '\t'
			if (index + str_len + 1) % 20 == 0:
				text += '\n'
	return text