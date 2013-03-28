#-*- coding: utf-8 -*-
# stino/src.py

import sublime
import os
import re

from stino import osfile
from stino import const
from stino import utils

header_ext_list = ['.h', '.hpp']
arduino_ext_list = ['.ino', '.pde']
src_ext_list = ['.ino', '.pde', '.c', '.cc', '.cpp', '.cxx']

def getTextFromView(view):
	region = sublime.Region(0, view.size())
	text = view.substr(region)
	return text

def getTextFromSketch(sketch):
	sketch_text = ''
	if isinstance(sketch, type(sublime.active_window().active_view())):
		sketch_text = getTextFromView(sketch)
	else:
		if os.path.isfile(sketch):
			sketch_ext = os.path.splitext(sketch)[1]
			if sketch_ext in src_ext_list:
				sketch_text = osfile.readFileText(sketch)
		elif isinstance(sketch, basestring):
			sketch_text = sketch
	return sketch_text

def genSimpleSrcText(src_text):
	simple_src_text = ''
	
	pattern_list = [r'//[\S\s]*?\n', r'/\*[\S\s]*?\*/']
	replace_text_list = ['\n', '\n', ' ', '\n']
	replace_list = zip(pattern_list, replace_text_list)
	for (pattern_text, replace_text) in replace_list:
		src_text = re.sub(pattern_text, replace_text, src_text)

	src_text = src_text.replace('{', '\n{\n')
	src_text = src_text.replace('}', '\n}\n')
	src_lines = utils.convertTextToLines(src_text)
	
	level = 0
	for line in src_lines:
		line = line.strip()
		if line:
			if '}' in line:
				level -= 1
			if level == 0:
				simple_src_text += line
				simple_src_text += '\n'
			if '{' in line:
				level += 1
	simple_src_text = simple_src_text.replace(';', ';\n')
	simple_src_text = simple_src_text.replace('\n', ' ')
	return simple_src_text

def regulariseBlank(text):
	pattern_text = r'\S+'
	word_list = re.findall(pattern_text, text)
	
	text = ''
	for word in word_list:
		text += word
		text += ' '
	text = text[:-1]
	return text

def regulariseFunctionName(function_name):
	pattern_text = r'\S+'
	word_list = re.findall(pattern_text, function_name)[-2:]

	function_name = ''
	for word in word_list:
		function_name += word
		function_name += ' '
	function_name = function_name[:-1]
	return function_name

def regulariseFuctionText(function_text):
	text = function_text.split(')')[-2]
	if '(' in text:
		text_list = text.split('(')
		function_name = text_list[0].strip()
		function_name = regulariseFunctionName(function_name)
		parameters = text_list[1].strip()
		parameters = regulariseBlank(parameters)
		function_text = function_name + ' (' + parameters + ')'
	else:
		function_text = ''
	return function_text

def genSrcDeclarationList(simple_src_text):
	pattern_text = r'[\w*]+?\s+?[\w]+?\s*?\([\w\s,=*]*?\)\s*?;'
	declaration_list = re.findall(pattern_text, simple_src_text)
	src_declaration_list = [declaration[:-1].strip() for declaration in declaration_list]
	src_declaration_list = [regulariseFuctionText(declaration) for declaration in src_declaration_list]
	return src_declaration_list

def genSrcFunctionList(simple_src_text):
	src_function_list = []
	pattern_text = r'[\w*]+?\s+?[\w]+?\s*?\([\w\s,=*]*?\)\s*?\{ }'
	function_text_list = re.findall(pattern_text, simple_src_text)
	for function_text in function_text_list:
		function = regulariseFuctionText(function_text)
		if function:
			src_function_list.append(function)
	return src_function_list

def isMainSrcText(src_text):
	state = False
	simple_src_text = genSimpleSrcText(src_text)
	src_function_list = genSrcFunctionList(simple_src_text)
	if 'void setup ()' in src_function_list and 'void loop ()' in src_function_list:
		state = True
	return state

def isSketch(sketch):
	state = False
	sketch_ext = ''
	
	if isinstance(sketch, type(sublime.active_window().active_view())):
		sketch_name = sketch.file_name()
		if sketch_name:
			sketch_ext = os.path.splitext(sketch_name)[1]
	else:
		if os.path.isfile(sketch):
			sketch_ext = os.path.splitext(sketch)[1]		
	
	if sketch_ext in src_ext_list or sketch_ext in header_ext_list:
		state = True
	else:
		state = isMainSketch(sketch)
	return state

def isMainSketch(sketch):
	state = False
	sketch_text = getTextFromSketch(sketch)
	if sketch_text:
		state = isMainSrcText(sketch_text)
	return state

def createNewSketch(filename):
	sketchbook_root = const.settings.get('sketchbook_root')
	folder_path = os.path.join(sketchbook_root, filename)
	file_path = os.path.join(folder_path, filename)
	file_path += '.ino'

	template_file_path = os.path.join(const.template_root, 'sketch')
	os.mkdir(folder_path)
	text = osfile.readFileText(template_file_path)
	osfile.writeFile(file_path, text)
	openSketch(filename)

def openSketch(sketch):
	sketchbook_root = const.settings.get('sketchbook_root')
	folder_path = os.path.join(sketchbook_root, sketch)
	full_file_list = osfile.listDir(folder_path, with_dirs = False)

	file_list = []
	for cur_file in full_file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in src_ext_list or cur_file_ext in header_ext_list:
			file_list.append(cur_file)

	file_path_list = [os.path.join(folder_path, cur_file) for cur_file in file_list]

	sublime.run_command('new_window')
	window = sublime.windows()[-1]

	for cur_file_path in file_path_list:
		window.open_file(cur_file_path)

def createNewFile(window, file_path):
	filename = os.path.split(file_path)[1]
	text = '// %s\n\n' % filename
	osfile.writeFile(file_path, text)
	window.open_file(file_path)

def getSketchFolderPathFromSketchbook(file_path):
	sketchbook_root = const.settings.get('sketchbook_root')
	file_path = file_path.replace(sketchbook_root, '')
	file_path = file_path[1:]
	folder = file_path.split(os.path.sep)[0]
	folder_path = os.path.join(sketchbook_root, folder)
	return folder_path

def hasMainSketchInFolder(folder_path):
	state = False
	file_list = osfile.listDir(folder_path, with_dirs = False)
	for cur_file in file_list:
		cur_file_path = os.path.join(folder_path, cur_file)
		if isMainSketch(cur_file_path):
			state = True
			break
	return state

def getSketchFolderPathWithoutSketchbook(file_path):
	folder_path = os.path.split(file_path)[0]
	if not isMainSketch(file_path):
		has_main_sketch = False
		cur_path = file_path
		while not has_main_sketch:
			cur_path = os.path.split(cur_path)[0]
			if cur_path[-1] == os.path.sep:
				cur_path = cur_path[:-1]
			if not os.path.sep in cur_path:
				break
			has_main_sketch = hasMainSketchInFolder(cur_path)
		if has_main_sketch:
			folder_path = cur_path
	return folder_path

def getSketchFolderPath(file_path):
	sketchbook_root = const.settings.get('sketchbook_root')
	if sketchbook_root in file_path:
		folder_path = getSketchFolderPathFromSketchbook(file_path)
	else:
		folder_path = getSketchFolderPathWithoutSketchbook(file_path)
	return folder_path

def getSketchNameFromFolder(sketch_folder_path):
	sketch_name = os.path.split(sketch_folder_path)[1]
	return sketch_name

def genHeaderListFromSketchText(sketch_text):
	header_list = []
	simple_src_text = genSimpleSrcText(sketch_text)
	pattern_text = r'#include\s+?["<]\S+?[>"]'
	include_header_list = re.findall(pattern_text, simple_src_text)
	for include_header in include_header_list:
		header = include_header.replace('#include', '').strip()
		header = header[1:-1]
		header_list.append(header)
	return header_list

def genHeaderListFromSketch(sketch):
	sketch_text = getTextFromSketch(sketch)
	header_list = genHeaderListFromSketchText(sketch_text)
	return header_list

def getHeaderListFromFolder(folder_path):
	header_list = []
	file_list = osfile.listDir(folder_path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in header_ext_list:
			header_list.append(cur_file)
	return header_list

def getIncludeHeaderList(folder_path, view):
	header_list = []
	header_list_from_view = genHeaderListFromSketch(view)
	header_list_from_folder = getHeaderListFromFolder(folder_path)
	for header in header_list_from_folder:
		if not header in header_list_from_view:
			header_list.append(header)
	return header_list

def getIncludeHeaderText(folder_path, view):
	header_list = getIncludeHeaderList(folder_path, view)
	include_header_list = [('#include <' + header + '>\n') for header in header_list]
	include_text = ''
	for include_header in include_header_list:
		include_text += include_header
	if include_text:
		include_text += '\n'
	return include_text

def insertLibraries(folder_path, view):
	include_text = getIncludeHeaderText(folder_path, view)
	edit = view.begin_edit()
	position = 0
	view.insert(edit, position, include_text)
	view.end_edit(edit)

def openExample(path):
	sublime.run_command('new_window')
	window = sublime.windows()[-1]
	file_list = osfile.listDir(path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in src_ext_list or cur_file_ext in header_ext_list:
			cur_file_path = os.path.join(path, cur_file)
			window.open_file(cur_file_path)
