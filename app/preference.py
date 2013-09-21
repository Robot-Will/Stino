#-*- coding: utf-8 -*-
# stino/preference.py

import os
import sys
import json

import sublime

from . import fileutil

sys_version = int(sys.version[0])

def getStinoRoot():
	if sys_version < 3:
		stino_root = os.getcwd()
	else:
		for module_key in sys.modules:
			if 'StinoStarter' in module_key:
				stino_module = sys.modules[module_key]
				break
		stino_root = os.path.split(stino_module.__file__)[0]
	return stino_root

def getStPackageRoot():
	st_packages_folder = sublime.packages_path()
	if not st_packages_folder:
		stino_folder = getStinoRoot()
		st_data_folder = stino_folder.split('Data')[-1]
		st_data_folder = stino_folder.split(st_data_folder)[0]
		st_packages_folder = os.path.join(st_data_folder, 'Packages')
	return st_packages_folder

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

		try:
			value + 'string'
		except TypeError:
			pass
		else:
			stino_folder = getStinoRoot()
			st_package_folder = getStPackageRoot()
			value = value.replace('${stino_root}', stino_folder)
			value = value.replace('${packages}', st_package_folder)
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