#-*- coding: utf-8 -*-
# stino/constant.py

import os
import sys
import locale
import codecs

import sublime

from . import preference

baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', 
		'19200', '28800', '38400', '57600', '115200']
line_ending_caption_list = ['None', 'Newline', 'Carriage return', 'Both NL & CR']
line_ending_list = ['', '\n', '\r', '\r\n']
display_mode_list = ['Text', 'Ascii', 'Hex']

def getSTVersion():
	ST_version_text = sublime.version()
	ST_version = int(ST_version_text) / 1000
	return ST_version

def getSysPlatform():
	# platform may be "osx", "linux" or "windows"
	sys_platform = sublime.platform()
	return sys_platform

def getSysEncoding():
	sys_platform = getSysPlatform()
	if sys_platform == 'osx':
		sys_encoding = 'utf-8'
	else:
		sys_encoding = codecs.lookup(locale.getpreferredencoding()).name
	return sys_encoding

def getSysLanguage():
	sys_language = locale.getdefaultlocale()[0]
	if not sys_language:
		sys_language = 'en'
	else:
		sys_language = sys_language.lower()
	return sys_language

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

ST_version = getSTVersion()
sys_version = int(sys.version[0])
sys_platform = getSysPlatform()
sys_encoding = getSysEncoding()
sys_language = getSysLanguage()

stino_root = getStinoRoot()
app_root = os.path.join(stino_root, 'app')
config_root = os.path.join(stino_root, 'config')
language_root = os.path.join(stino_root, 'language')
compile_root = os.path.join(stino_root, 'compile')

global_settings = preference.Setting(stino_root, 'stino.global_settings')
sketch_settings = preference.Setting(stino_root, 'stino.settings')

serial_in_use_list = []
serial_monitor_dict = {}
