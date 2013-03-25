#-*- coding: utf-8 -*-
# stino/stpanel.py

import sublime
import threading
import time

def isPanel(view):
	state = True
	file_name = view.file_name()
	name = view.name()
	if file_name or name:
		state = False
	return state

class STPanel:
	def __init__(self, name = 'stino_log'):
		self.name = name
		self.show_text = ''
		window = sublime.active_window()
		if not (window is None):
			self.panel = window.get_output_panel(self.name)
		else:
			self.panel = None

	def addText(self, text):
		if self.panel is None:
			window = sublime.active_window()
			if not (window is None):
				self.panel = window.get_output_panel(self.name)
		if not (self.panel is None):
			self.show_text += text
			show_thread = threading.Thread(target=self.show)
			show_thread.start()

	def show(self):
		sublime.set_timeout(self.update, 0)

	def update(self):
		if self.show_text:
			panel_edit = self.panel.begin_edit()
			self.panel.insert(panel_edit, self.panel.size(), self.show_text)
			self.panel.end_edit(panel_edit)
			self.panel.show(self.panel.size())
			self.show_text = ''

			window = sublime.active_window()
			panel_name = 'output.' + self.name
			window.run_command("show_panel", {"panel": panel_name})

	def clear(self):
		panel_edit = self.panel.begin_edit()
		self.panel.replace(panel_edit, sublime.Region(0, self.panel.size()), '')
		self.panel.end_edit(panel_edit)

	def toggleWordWrap(self):
		self.panel.run_command('toggle_setting', {'setting': 'word_wrap'})

class MonitorView:
	def __init__(self, name = 'Serial Monitor - Serial Port'):
		self.name = name
		self.show_text = ''
		self.window = sublime.active_window()
		if not (self.window is None):
			self.view = self.findInOpendView(self.name)
			if self.view is None:
				self.view = self.window.new_file()
				self.view.set_name(self.name)
		else:
			self.view = None

	def findInOpendView(self, view_name):
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

	def addText(self, text):
		if self.view is None:
			self.window = sublime.active_window()
			if not (self.window is None):
				self.view = self.findInOpendView(self.name)
				if self.view is None:
					self.view = self.window.new_file()
					self.view.set_name(self.name)
		if not (self.view is None):
			self.show_text += text
			shwo_thread = threading.Thread(target=self.show)
			shwo_thread.start()

	def show(self):
		sublime.set_timeout(self.update, 0)

	def update(self):
		if self.show_text:
			view_edit = self.view.begin_edit()
			self.view.insert(view_edit, self.view.size(), self.show_text)
			self.view.end_edit(view_edit)
			self.view.show(self.view.size())
			self.show_text = ''

	def raiseToFront(self):
		self.window.focus_view(self.view)

	def toggleWordWrap(self):
		self.view.run_command('toggle_setting', {'setting': 'word_wrap'})
