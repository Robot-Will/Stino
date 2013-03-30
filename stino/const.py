#-*- coding: utf-8 -*-
# stino/const.py

import sublime
import os
import locale
import codecs

from stino import utils

# Sublime Text Version
st_version = sublime.version()

# platform may be "osx", "linux" or "windows"
sys_platform = sublime.platform()

# arch may be "x32" or "x64"
sys_arch = sublime.arch()

# encoding
if sys_platform == 'osx':
	sys_encoding = 'utf-8'
else:
	sys_encoding = codecs.lookup(locale.getpreferredencoding()).name

# language
sys_language = locale.getdefaultlocale()[0]
if sys_language:
	sys_language = sys_language.lower()
else:
	sys_language = 'en'

# Stino plugin root directory
plugin_root = utils.convertAsciiToUtf8(os.getcwd())
script_root = os.path.join(plugin_root, 'stino')
template_root = os.path.join(plugin_root, 'template')
language_root = os.path.join(plugin_root, 'language')
compilation_script_root = os.path.join(plugin_root, 'compilation')

# Stino settings file
# $packages/User/Stino.sublime-settings
settings_file = 'Stino.sublime-settings'
settings = sublime.load_settings(settings_file)

def save_settings():
	sublime.save_settings(settings_file)