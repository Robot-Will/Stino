#-*- coding: utf-8 -*-
# stino/console.py

import sublime

import threading

from . import constant

class Console:
	def __init__(self, name = 'stino_console'):
		self.name = name
		self.panel = None
		self.show_text = ''

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

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
		window = sublime.active_window()
		if window:
			if not self.panel:
				if constant.sys_version < 3:
					self.panel = window.get_output_panel(self.name)
				else:
					self.panel = window.create_output_panel(self.name)

		if not self.panel is None:
			if self.show_text:
				text = self.show_text
				self.panel.run_command('panel_output', {'text': text})
				self.show_text = ''
				panel_name = 'output.' + self.name
				window.run_command("show_panel", {"panel": panel_name})
				