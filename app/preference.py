#-*- coding: utf-8 -*-
# stino/preference.py

import os
import json

import sublime

from . import fileutil

class Setting:
	def __init__(self, default_folder, file_name):
		self.settings_dict = {}
		self.default_folder = default_folder
		self.file_name = file_name
		self.default_file = os.path.join(default_folder, file_name)
		self.file = self.default_file
		self.loadSettingsFile()

	def loadSettingsFile(self):
		if os.path.isfile(self.file):
			text = fileutil.readFile(self.file)
			self.settings_dict = json.loads(text)

	def saveSettingsFile(self):
		text = json.dumps(self.settings_dict, sort_keys = True, indent = 4)
		fileutil.writeFile(self.file, text)

	def get(self, key, default_value = None):
		if key in self.settings_dict:
			value = self.settings_dict[key]
		else:
			value = default_value
		return value

	def set(self, key, value):
		self.settings_dict[key] = value
		self.saveSettingsFile()

	def changeFolder(self, folder):
		if not os.path.isdir(folder):
			self.file = self.default_file
		else:
			self.file = os.path.join(folder, self.file_name)

		if os.path.isfile(self.file):
			self.loadSettingsFile()
		else:
			self.saveSettingsFile()