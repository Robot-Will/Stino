#-*- coding: utf-8 -*-
# stino/preprocess.py

import re

from . import fileutil

c_keyword_list = ['if', 'elif', 'else', 'while', 'for', 'switch', 'case']

def getPatternList(src_text, pattern_text):
	pattern = re.compile(pattern_text, re.M|re.S)
	pattern_list = pattern.findall(src_text)
	return pattern_list

def getSingleLineCommentList(src_text):
	pattern_text = r'//.*?$'
	comment_list = getPatternList(src_text, pattern_text)
	return comment_list

def getMultiLineCommentList(src_text):
	pattern_text = r'/\*.*?\*/'
	comment_list = getPatternList(src_text, pattern_text)
	return comment_list

def getStringList(src_text):
	pattern_text = r'"(?:[^"\\"]|\\.)*?"' # double-quoted string
	string_list = getPatternList(src_text, pattern_text)
	return string_list

def getPreProcessorList(src_text):
	pattern_text = r'^#.*?$' # pre-processor directive
	pre_processor_list = getPatternList(src_text, pattern_text)
	return pre_processor_list

def getIncludeList(src_text):
	pattern_text = r'#include\s+?["<]\S+?[>"]'
	include_list = getPatternList(src_text, pattern_text)
	return include_list

def getDeclarationList(src_text):
	pattern_text = r'^\s*[\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\)(?=\s*?;)'
	declaration_list = getPatternList(src_text, pattern_text)
	return declaration_list

def getFunctionList(src_text):
	pattern_text = r'^\s*([\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\))(?=\s*?\{)'
	function_list = getPatternList(src_text, pattern_text)
	return function_list

def removeCertainTypeText(src_text, cur_type):
	if cur_type == 'single-comment':
		text_list = getSingleLineCommentList(src_text)
	elif cur_type == 'multi-comment':
		text_list = getMultiLineCommentList(src_text)
	elif cur_type == 'string':
		text_list = getStringList(src_text)
	text_list.sort(key=lambda x:len(x))
	text_list.reverse()
	for text in text_list:
		src_text = src_text.replace(text, '')
	return src_text

def genFunctionList(src_text):
	function_list = []
	src_text = removeCertainTypeText(src_text, 'multi-comment')
	src_text = removeCertainTypeText(src_text, 'single-comment')
	src_text = removeCertainTypeText(src_text, 'string')
	org_func_list = getFunctionList(src_text)
	for org_func in org_func_list:
		is_not_function = False
		word_list = re.findall(r'\b\w+\b', org_func)
		for word in word_list:
			if word in c_keyword_list:
				is_not_function = True
				break
		if is_not_function:
			continue
		else:
			function_list.append(org_func)
	return function_list

def splitSrcText(src_text):
	function_list = genFunctionList(src_text)
	if function_list:
		first_function = function_list[0]
		index = src_text.index(first_function)
		src_text_header = src_text[:index]
		src_text_body = src_text[index:]
	else:
		src_text_header = src_text
		src_text_body = ''
	return (src_text_header, src_text_body)

def genIncludeList(src_text):
	src_text = removeCertainTypeText(src_text, 'multi-comment')
	src_text = removeCertainTypeText(src_text, 'single-comment')
	include_list = getIncludeList(src_text)
	return include_list

def getHList(src_text):
	pattern_text = r'#include\s+?["<](\S+?)[>"]'
	h_list = getPatternList(src_text, pattern_text)
	return h_list

def genHList(src_text):
	src_text = removeCertainTypeText(src_text, 'single-comment')
	src_text = removeCertainTypeText(src_text, 'multi-comment')
	h_list = getHList(src_text)
	return h_list

def isMainSrcFile(src_file):
	state = False
	src_text = fileutil.readFile(src_file)

	has_setup = False
	has_loop = False
	function_list = genFunctionList(src_text)
	for function in function_list:
		if 'setup' in function:
			has_setup = True
		if 'loop' in function:
			has_loop = True
	if has_setup and has_loop:
		state = True
	return state

def getMainSrcFile(src_file_list):
	main_src_file = src_file_list[0]
	for src_file in src_file_list:
		if isMainSrcFile(src_file):
			main_src_file = src_file
			break
	return main_src_file

def sortSrcFileList(src_file_list):
	main_src_file = getMainSrcFile(src_file_list)
	src_file_list.remove(main_src_file)
	new_file_list = [main_src_file] + src_file_list
	return new_file_list

def genFunctionListFromFile(src_file):
	text = fileutil.readFile(src_file)
	function_list = genFunctionList(text)
	return function_list

def genFunctionListFromSrcList(src_file_list):
	function_list = []
	for src_file in src_file_list:
		function_list += genFunctionListFromFile(src_file)
	return function_list

def getInsertText(src_file_list):
	insert_text = '\n'
	function_list = genFunctionListFromSrcList(src_file_list)

	for function in function_list:
		if (' setup' in function) or (' loop' in function):
			continue
		insert_text += '%s;\n' % function
	insert_text += '\n'
	return insert_text

def genCppFileFromInoFileList(cpp_file, ino_src_file_list, arduino_version, preprocess=True):
	cpp_text = ''

	if preprocess:
		if arduino_version < 100:
			include_text = '#include <WProgram.h>\n'
		else:
			include_text = '#include <Arduino.h>\n'

		cpp_text += include_text

		if ino_src_file_list:
			insert_text = getInsertText(ino_src_file_list)
			main_src_file = ino_src_file_list[0]
			src_text = fileutil.readFile(main_src_file)

			function_list = genFunctionList(src_text)
			if function_list:
				first_function = function_list[0]
				index = src_text.index(first_function)
				header_text = src_text[:index]
				body_text = src_text[index:]
			else:
				index = len(src_text)
				header_text = src_text
				body_text = ''

			cpp_text += header_text
			cpp_text += insert_text
			cpp_text += body_text

			for src_file in ino_src_file_list[1:]:
				src_text = fileutil.readFile(src_file)
				cpp_text += src_text

	# Don't do any preprocessing at all
	else:

		if len(ino_src_file_list) != 1:
			raise ValueError("Too many source files! Only one \".ino\" file is supported")

		main_src_file = ino_src_file_list[0]
		cpp_text = fileutil.readFile(main_src_file)

	fileutil.writeFile(cpp_file, cpp_text)

def getHListFromSrcList(ino_src_list):
	h_list = []
	for ino_src in ino_src_list:
		text = fileutil.readFile(ino_src)
		h_list += genHList(text)
	return h_list
