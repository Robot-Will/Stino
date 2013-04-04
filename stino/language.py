#-*- coding: utf-8 -*-
# stino/language.py

import os
import re

from stino import const
from stino import osfile
from stino import utils

class Language:
	def __init__(self):
		self.genAbvDict()
		self.genLanguageList()
		self.setDefaultLanguage()
		self.genDefaultTransDict()
		self.genDefaultLanguageFile()
		self.genTransDict()

	def update(self):
		self.genTransDict()

	def genAbvDict(self):
		self.abv_language_dict = {}
		self.abv_text_dict = {}
		template_root = const.template_root
		iso_file_path = os.path.join(template_root, 'ISO639_1')
		lines = osfile.readFileLines(iso_file_path)
		for line in lines:
			line = line.strip()
			if line:
				info_list = line.split('=')
				lang_abv = info_list[0].strip()
				lang = info_list[1].strip()
				lang_text = info_list[2].strip()
				self.abv_language_dict[lang_abv] = lang
				self.abv_text_dict[lang_abv] = '%s (%s)' % (lang_text, lang)

	def genLanguageList(self):
		self.language_list = []
		self.language_text_list = []
		self.language_file_dict = {}
		self.language_text_dict = {}
		self.text_language_dict = {}
		language_root = const.language_root
		file_list = osfile.listDir(language_root, with_dirs = False)
		for cur_file in file_list:
			cur_file_path = os.path.join(language_root, cur_file)
			if cur_file in self.abv_language_dict:
				language_abv = cur_file
				language = self.abv_language_dict[language_abv]
				language_text = self.abv_text_dict[language_abv]
				
				if not language in self.language_list:
					self.language_list.append(language)
					self.language_file_dict[language] = cur_file_path
					self.language_text_dict[language] = language_text
					self.text_language_dict[language_text] = language
		self.language_list.sort()
		for language in self.language_list:
			language_text = self.language_text_dict[language]
			self.language_text_list.append(language_text)

	def setDefaultLanguage(self):
		language = const.settings.get('language')
		if not language:
			language_abv = const.sys_language
			if language_abv in self.abv_language_dict:
				language = self.abv_language_dict[language_abv]
			else:
				language_abv = language_abv.split('_')[0].strip()
				if language_abv in self.abv_language_dict:
					language = self.abv_language_dict[language_abv]
		if not language in self.language_list:
			language = 'English'
		const.settings.set('language', language)

	def genDefaultTransDict(self):
		self.trans_dict = {}

		pattern_text = r'%\(([\S\s]+?)\)s'
		pattern = re.compile(pattern_text)
		# display_pattern_text = r"display_text\s*?=\s*?'([\S\s]+?)'"
		display_pattern_text = r"display_text\s*?=\s*?'((?:[^'\\']|\\.)+?)'"
		display_pattern = re.compile(display_pattern_text, re.S)

		plugin_root = const.plugin_root
		script_root = const.script_root
		template_root = const.template_root
		root_list = [plugin_root, script_root, template_root]

		for cur_dir in root_list:
			file_list = osfile.listDir(cur_dir, with_dirs = False)
			for cur_file in file_list:
				if ('menu_' in cur_file and not 'sublime' in cur_file) \
					or (os.path.splitext(cur_file)[1] == '.py'):
					cur_file_path = os.path.join(cur_dir, cur_file)
					text = osfile.readFileText(cur_file_path)
					key_list = pattern.findall(text)
					for key in key_list:
						if not key in self.trans_dict:
							value = key.replace('_', ' ')
							self.trans_dict[key] = value
					key_list = display_pattern.findall(text)
					for key in key_list:
						if not key in self.trans_dict:
							self.trans_dict[key] = key

	def genDefaultLanguageFile(self):
		template_root = const.template_root
		language_root = const.language_root
		template_file_path = os.path.join(template_root, 'language')
		text = osfile.readFileText(template_file_path)
		text += '\n'
		key_list = []
		for key in self.trans_dict:
			key_list.append(key)
		key_list.sort()
		for key in key_list:
			text += 'msgid "%s"\n' % key
			text += 'msgstr "%s"\n\n' % self.trans_dict[key]
		default_file_path = os.path.join(language_root, 'original_text')
		osfile.writeFile(default_file_path, text)

	def genTransDict(self):
		language = const.settings.get('language')
		language_file_path = self.getLanguageFile(language)
		if os.path.isfile(language_file_path):
			trans_block = []
			lines = osfile.readFileLines(language_file_path)
			for line in lines:
				line = line.strip()
				if line and line[0] != '#':
					trans_block.append(line)
			info_block_list = utils.splitToBlocks(trans_block, sep = 'msgid')
			for info_block in info_block_list:
				key = ''
				value = ''
				is_key_line = False
				is_value_line = False
				for line in info_block:
					if 'msgid' in line:
						is_key_line = True
					if 'msgstr' in line:
						is_key_line = False
						is_value_line = True
					if is_key_line:
						line = line.replace('msgid', '').strip()
						line = line[1:-1]
						key += line
					if is_value_line:
						line = line.replace('msgstr', '').strip()
						line = line[1:-1]
						value += line
				if key in self.trans_dict:
					self.trans_dict[key] = value

	def translate(self, display_text):
		display_text = display_text.replace('\n', '\\n')
		display_text = utils.convertAsciiToUtf8(display_text)
		trans_text = display_text
		if display_text in self.trans_dict:
			trans_text = self.trans_dict[display_text]
		trans_text = trans_text.replace('\\n', '\n')
		return trans_text

	def getTransDict(self):
		return self.trans_dict

	def getLanguageList(self):
		return self.language_list

	def getLanguageTextList(self):
		return self.language_text_list

	def getLanguageFile(self, language):
		file_path = ''
		if language in self.language_file_dict:
			file_path = self.language_file_dict[language]
		return file_path

	def getLanguageTextFromLanguage(self, language):
		language_text = ''
		if language in self.language_text_dict:
			language_text = self.language_text_dict[language]
		return language_text

	def getLanguageFromLanguageText(self, language_text):
		language = ''
		if language_text in self.text_language_dict:
			language = self.text_language_dict[language_text]
		return language