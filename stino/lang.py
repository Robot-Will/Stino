#-*- coding: utf-8 -*-
import sublime
import os, re
from stino import utils

class Lang():
	"""Language"""
	def __init__(self):
		self.Settings = sublime.load_settings('Stino.sublime-settings')
		self.trans_dict = {}
		self.file_dict = {}
		self.lang_list = []
		self.lang_text_dict = {}
		self.genLangList()
		self.genDefaultTransDict()
		self.genTransDict()

	def genDefaultTransDict(self):
		plugin_root = utils.getPluginRoot()
		template_dir = os.path.join(plugin_root, 'template')
		mod_dir = os.path.join(plugin_root, 'stino')
		dirs = [plugin_root, template_dir, mod_dir]
		pattern = re.compile(r'%\([\S\s]+?\)s')

		for cur_dir in dirs:
			files = os.listdir(cur_dir)
			files = [os.path.join(cur_dir, cur_file) for cur_file in files if (not '.pyc' in cur_file) and (not '.sublime' in cur_file) and (not '.tm' in cur_file)]
			files = [cur_file for cur_file in files if os.path.isfile(cur_file)]
			for cur_file in files:
				lines = utils.readFile(cur_file, mode = 'lines')
				for cur_line in lines:
					match = pattern.search(cur_line)
					if match:
						captions = pattern.findall(cur_line)
						for caption in captions:
							caption = caption[2:-2]
							caption_txt = caption.replace('_', ' ')
							if not caption in self.trans_dict:
								self.trans_dict[caption] = caption_txt

	def genLangList(self):
		plugin_root = utils.getPluginRoot()
		lang_dir = os.path.join(plugin_root, 'lang')
		files = os.listdir(lang_dir)
		for lang_file in files:
			lang_file = os.path.join(lang_dir, lang_file)
			if os.path.isfile(lang_file):
				f = open(lang_file, 'r')
				lines = f.readlines()
				f.close()

				for line in lines:
					(key, value) = utils.getKeyValue(line)
					if key == 'LANG':
						value = value.decode('utf-8')
						pattern = re.compile(r'\([\S\s]+\)')
						match = pattern.search(value)
						if match:
							lang = match.group()[1:-1]
						else:
							lang = value
						self.lang_list.append(lang)
						self.lang_text_dict[lang] = value
						self.file_dict[value] = lang_file
						break
		self.lang_list.sort()

	def genTransDict(self):
		language = self.Settings.get('language')
		if language:
			if language in self.lang_text_dict.values():
				lang_file = self.file_dict[language]
				f = open(lang_file, 'r')
				lines = f.readlines()
				f.close()

				for line in lines:
					line = line.strip()
					if line and (not '#' in line):
						(key, value) = utils.getKeyValue(line)
						value = value.decode('utf-8')
						self.trans_dict[key] = value

	def update(self):
		self.genTransDict()

	def getDisplayTextDict(self):
		return self.trans_dict

	def getLangList(self):
		return self.lang_list
						
		
