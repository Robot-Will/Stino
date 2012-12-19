#-*- coding: utf-8 -*-

import sublime
import serial
import threading
from stino import utils
import time

def isAvailable(port):
	state = False
	ser = None
	try:
		ser = serial.Serial(port)
	except serial.serialutil.SerialException:
		pass
	if ser:
		state = True
		ser.close()
	return state

class SerialListener(threading.Thread):
	def __init__(self, stmenu):
		threading.Thread.__init__(self)
		self.stmenu = stmenu

	def run(self):
		pre_serial_list = utils.getSerialPortList()
		while True:
			serial_list = utils.getSerialPortList()
			if serial_list != pre_serial_list:
				self.stmenu.serialUpdate()
				pre_serial_list = serial_list
			time.sleep(1)

class serialMonitor(threading.Thread):
	def __init__(self, view, serial_port, baudrate):
		threading.Thread.__init__(self)
		self.view = view
		self.serial_port = serial_port
		self.baudrate = baudrate

	def run(self):
		self.active = True
		ser = serial.Serial()
		ser.port = self.serial_port
		ser.baudrate = int(self.baudrate)
		ser.timeout = 1
		ser.open()
		print ser

		text = ''
		pre_number = ser.inWaiting()
		while self.active:
			number = ser.inWaiting()
			if number > 0:
				line = ser.read(number)
				text += line
			if number == 0:
				if text:
					text = text.replace('\r', '')
					text = text.rstrip()
					print text
					text = ''
			pre_number = number
			time.sleep(0.01)
		ser.close()

	def stop(self):
		self.active = False