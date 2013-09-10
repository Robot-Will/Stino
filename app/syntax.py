#-*- coding: utf-8 -*-
# stino/syntax.py

import os

from . import constant
from . import fileutil

class Syntax:
	def __init__(self, arduino_info, file_name):
		self.arduino_info = arduino_info
		self.file_name = file_name
		self.constant_keyword_list = []
		self.common_keyword_list = []
		self.function_keyword_list = []
		self.refresh()

	def refresh(self):
		self.classifyKeywordList()
		self.genFile()

	def classifyKeywordList(self):
		keyword_list = self.arduino_info.getKeywordList()
		for keyword in keyword_list:
			keyword_name = keyword.getName()
			if len(keyword_name) > 1:
				keyword_type = keyword.getType()
				if keyword_type:
					if 'LITERAL' in keyword_type:
						self.constant_keyword_list.append(keyword)
					elif keyword_type == 'KEYWORD1':
						self.common_keyword_list.append(keyword)
					else:
						self.function_keyword_list.append(keyword)

	def genFile(self):
		text = ''
		text += genDictBlock(self.constant_keyword_list, 'constant.arduino')
		text += genDictBlock(self.common_keyword_list, 'storage.modifier.arduino')
		text += genDictBlock(self.function_keyword_list, 'support.function.arduino')

		temp_file = os.path.join(constant.config_root, 'syntax')
		# opened_file = open(temp_file, 'r')
		# syntax_text = opened_file.read()
		# opened_file.close()
		syntax_text = fileutil.readFile(temp_file)

		syntax_text = syntax_text.replace('(_$dict$_)', text)
		syntax_file = os.path.join(constant.stino_root, self.file_name)
		# opened_file = open(syntax_file, 'w')
		# opened_file.write(syntax_text)
		# opened_file.close()
		fileutil.writeFile(syntax_file, syntax_text)

def genDictBlock(keyword_list, description):
	dict_text = ''
	if keyword_list:
		dict_text += '\t' * 2
		dict_text += '<dict>\n'
		dict_text += '\t' * 3
		dict_text += '<key>match</key>\n'
		dict_text += '\t' * 3
		dict_text += '<string>\\b('
		for keyword in keyword_list:
			dict_text += keyword.getName()
			dict_text += '|'
		dict_text = dict_text[:-1]
		dict_text += ')\\b</string>\n'
		dict_text += '\t' * 3
		dict_text += '<key>name</key>\n'
		dict_text += '\t' * 3
		dict_text += '<string>'
		dict_text += description
		dict_text += '</string>\n'
		dict_text += '\t' * 2
		dict_text += '</dict>\n'
	return dict_text