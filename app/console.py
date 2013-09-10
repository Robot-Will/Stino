#-*- coding: utf-8 -*-
# stino/console.py

import sublime

from . import constant

class Console:
	def __init__(self, name = 'stino_console'):
		self.name = name
		self.panel = None

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def printText(self, text):
		self.text = text
		if constant.sys_version < 3:
			sublime.set_timeout(self.update, 0)
		else:
			self.update()

	def update(self):
		window = sublime.active_window()
		if window:
			if not self.panel:
				if constant.sys_version < 3:
					self.panel = window.get_output_panel(self.name)
				else:
					self.panel = window.create_output_panel(self.name)

		if not self.panel is None:
			if self.text:
				self.panel.run_command('panel_output', {'text': self.text})
				panel_name = 'output.' + self.name
				window.run_command("show_panel", {"panel": panel_name})
				self.text = ''