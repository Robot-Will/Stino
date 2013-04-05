#-*- coding: utf-8 -*-
# stino/setting.py

import sublime
import os
import json

class Setting:
	def __init__(self):
		user_path = os.path.join(sublime.packages_path(), 'User')
		self.global_settings_file = 'Stino.sublime-settings'
		self.global_settings_file_path = os.path.join(user_path, self.global_settings_file)
		self.global_settings = sublime.load_settings(self.global_settings_file)
		
		global_setting_option = self.global_settings.get('global_setting')
		if global_setting_option is None:
			global_setting_option = True
			self.global_settings.set('global_setting', global_setting_option)
			sublime.save_settings(self.global_settings_file)
		
		self.use_global_setting = global_setting_option
		self.setting_filename = 'Stino.settings'
		self.setting_file_path = self.global_settings_file_path
		self.readSettingFile()

	def get(self, key, default_value = None):
		if self.use_global_setting or (key == 'global_setting') or (key == 'show_arduino_menu') \
			or (key == 'show_serial_monitor_menu') or (key == 'language') or (key == 'pre_setting_folder_path'):
			value = self.global_settings.get(key, default_value)
		else:
			if key in self.settings_dict:
				value = self.settings_dict[key]
			else:
				value = default_value
		return value

	def set(self, key, value):
		self.global_settings.set(key, value)
		sublime.save_settings(self.global_settings_file)
		if not self.use_global_setting:
			self.settings_dict[key] = value
			self.saveSettingFile()

	def readSettingFile(self):
		opened_file = open(self.setting_file_path, 'r')
		settings_text = opened_file.read()
		opened_file.close()

		settings_text = settings_text.decode('utf-8')
		self.settings_dict = json.loads(settings_text)

	def saveSettingFile(self):
		settings_text = json.dumps(self.settings_dict, sort_keys = True, indent = 4)

		opened_file = open(self.setting_file_path, 'w')
		opened_file.write(settings_text)
		opened_file.close()

	def changeSettingFileFolder(self, setting_file_folder_path):
		self.setting_file_path = os.path.join(setting_file_folder_path, self.setting_filename)
		if not os.path.isfile(self.setting_file_path):
			self.saveSettingFile()
		self.readSettingFile()

	def changeState(self, state):
		self.use_global_setting = state

class Status:
	def __init__(self, settings, arduino_info, language):
		self.settings = settings
		self.arduino_info = arduino_info
		self.language = language

		self.view = None
		self.global_setting = True
		self.arduino_version_text = ''
		self.board = ''
		self.board_option_list = []
		self.programmer = ''
		self.serial_port = ''
		self.baudrate = ''

		self.loadInfo()

	def update(self):
		text = ''
		show_arduino_menu = self.settings.get('show_arduino_menu')
		if show_arduino_menu and self.arduino_info.isReady():
			self.loadInfo()
			if self.global_setting:
				text += '%(Global_Setting)s - '
			text += 'Arduino %s' % self.arduino_version_text
			text += ', %s' % self.board
			for board_option in self.board_option_list:
				text += ', %s' % board_option
			if self.serial_port:
				text += ', %s' % self.serial_port
				text += ', %s bps' % self.baudrate
			if self.programmer:
				text += ', %s' % self.programmer
			text = text % self.language.getTransDict()
		if self.view:
			self.view.set_status('Stino_status', text)

	def loadInfo(self):
		if self.arduino_info.isReady():
			self.global_setting = self.settings.get('global_setting')
			self.arduino_version_text = self.arduino_info.getVersionText()
			self.board = self.settings.get('board')
			self.programmer = self.settings.get('programmer')
			self.serial_port = self.settings.get('serial_port')
			self.baudrate = self.settings.get('baudrate')

			platform = self.settings.get('platform')
			board_type_list = self.arduino_info.getBoardTypeList(platform, self.board)
			for board_type in board_type_list:
				type_caption = self.arduino_info.getPlatformTypeCaption(platform, board_type)
				type_value = self.settings.get(type_caption)
				self.board_option_list.append(type_value)

	def setView(self, view):
		self.view = view

