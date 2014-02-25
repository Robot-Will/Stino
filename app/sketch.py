#-*- coding: utf-8 -*-
# stino/sketch.py

import os

import sublime

from . import constant
from . import fileutil
from . import preprocess

h_src_ext_list = ['.h']
ino_src_ext_list = ['.ino', '.pde']
c_src_ext_list = ['.c', '.cpp']
asm_src_ext_list = ['.asm', '.S']
src_ext_list = ['.ino', '.pde', '.c', '.cpp', '.asm', '.S']

class Project:
	def __init__(self, folder):
		self.setFolder(folder)
		
	def getFolder(self):
		return self.folder

	def getName(self):
		return self.name

	def getHSrcFileList(self):
		return self.h_file_list

	def getInoSrcFileList(self):
		return self.ino_src_file_list

	def getCSrcFileList(self):
		return self.c_src_file_list

	def getAsmSrcFileList(self):
		return self.asm_src_file_list

	def setFolder(self, folder):
		self.folder = folder
		self.name = os.path.split(folder)[1]
		self.h_src_file_list = fileutil.getFileListOfExt(folder, h_src_ext_list)
		self.c_src_file_list = fileutil.getFileListOfExt(folder, c_src_ext_list)
		self.asm_src_file_list = fileutil.getFileListOfExt(folder, asm_src_ext_list)
		self.ino_src_file_list = fileutil.getFileListOfExt(folder, ino_src_ext_list)
		if self.ino_src_file_list:
			self.ino_src_file_list = preprocess.sortSrcFileList(self.ino_src_file_list)

class SrcFile:
	def __init__(self):
		self.view = None
		self.sketch_name = ''
		self.view_name = ''
		self.file_name = ''
		self.folder = ''
		self.file_ext = ''

	def getFolder(self):
		return self.folder

	def getView(self):
		return self.view

	def getViewName(self):
		return self.view_name

	def getFileName(self):
		return self.file_name

	def getSketchName(self):
		return self.sketch_name

	def setView(self, view):
		self.view = view
		self.view_name = view.name()
		self.file_name = view.file_name()
		if self.file_name:
			self.folder = os.path.split(self.file_name)[0]
			self.file_ext = os.path.splitext(self.file_name)[1]
		else:
			self.folder = ''
			self.file_ext = ''

		if self.isSrcFile():
			self.sketch_name = os.path.split(self.folder)[1]
		else:
			self.sketch_name = ''

	def isSrcFile(self):
		state = False
		if self.file_ext in src_ext_list:
			state = True
		return state

def isSrcFile(cur_file):
	state = False
	ext = os.path.splitext(cur_file)[1]
	if ext in src_ext_list:
		state = True
	return state

def openSketchFolder(sketch_folder):	
	src_file_list = []
	if os.path.isdir(sketch_folder):
		file_name_list = fileutil.listDir(sketch_folder, with_dirs = False)
		for file_name in file_name_list:
			cur_file = os.path.join(sketch_folder, file_name)
			if isSrcFile(cur_file):
				src_file_list.append(cur_file)

	if src_file_list:
		sublime.run_command('new_window')
		window = sublime.windows()[-1]
		for src_file in src_file_list:
			window.open_file(src_file)

		addFolderToProject(window, sketch_folder)

def addFolderToProject(window, folder):
	if os.path.isdir(folder):	
		project_data = window.project_data()
		
		if not project_data:
			project_data = {'folders': []}
		
		project_data['folders'].append({'follow_symlinks': True, 'path': folder})
		window.set_project_data(project_data)
		
def importLibrary(view, lib_folder):
	include_text = '\n'
	H_src_file_list = getHSrcFileList(lib_folder)
	if H_src_file_list:
		for H_src_file in H_src_file_list:
			cur_text = '#include "' + H_src_file + '"\n'
			include_text += cur_text
		view.run_command('insert_include', {'include_text': include_text})

def isHSrcFile(cur_file):
	state = False
	ext = os.path.splitext(cur_file)[1]
	if ext in h_src_ext_list:
		state = True
	return state

def getHSrcFileListFromFolder(lib_folder):
	H_src_file_list = []
	folder_name_list = fileutil.listDir(lib_folder, with_files = False)
	file_name_list = fileutil.listDir(lib_folder,with_dirs = False)

	for folder_name in folder_name_list:
		if folder_name.lower() == 'examples':
			continue
		cur_folder = os.path.join(lib_folder, folder_name)
		sub_H_src_file_list = getHSrcFileList(cur_folder)
		for sub_H_src_file in sub_H_src_file_list:
			sub_H_src_file = folder_name + '/' + sub_H_src_file
			H_src_file_list.append(sub_H_src_file)
	
	for file_name in file_name_list:
		cur_file = os.path.join(lib_folder, file_name)
		if isHSrcFile(cur_file):
			H_src_file_list.append(file_name)
	return H_src_file_list

def getHSrcFileList(lib_folder, platform_name = ''):
	H_src_file_list = []
	lib_folder_list = expandCoreFolder(lib_folder, platform_name)

	for lib_folder in lib_folder_list:
		H_src_file_list += getHSrcFileListFromFolder(lib_folder)
	return H_src_file_list

def isCSrcFile(cur_file):
	state = False
	ext = os.path.splitext(cur_file)[1]
	if ext in c_src_ext_list:
		state = True
	return state

def getCSrcFileListFromFolder(core_folder, level = 0):
	C_src_file_list = []
	folder_name_list = fileutil.listDir(core_folder, with_files = False)
	file_name_list = fileutil.listDir(core_folder,with_dirs = False)

	if level < 1:
		for folder_name in folder_name_list:
			if folder_name.lower() == 'examples':
				continue
			cur_folder = os.path.join(core_folder, folder_name)
			sub_C_src_file_list = getCSrcFileListFromFolder(cur_folder, level + 1)
			C_src_file_list += sub_C_src_file_list
	
	for file_name in file_name_list:
		cur_file = os.path.join(core_folder, file_name)
		if isCSrcFile(cur_file):
			C_src_file_list.append(cur_file)
	return C_src_file_list

def getCSrcFileListFromFolderList(core_folder_list):
	C_src_file_list = []
	core_folder_list = expandCorFolderList(core_folder_list)
	for core_folder in core_folder_list:
		sub_C_src_file_list = getCSrcFileListFromFolder(core_folder)
		C_src_file_list += sub_C_src_file_list
	return C_src_file_list

def isAsmSrcFile(cur_file):
	state = False
	ext = os.path.splitext(cur_file)[1]
	if ext in asm_src_ext_list:
		state = True
	return state

def getAsmSrcFileListFromFolder(core_folder, level = 0):
	asm_src_file_list = []
	folder_name_list = fileutil.listDir(core_folder, with_files = False)
	file_name_list = fileutil.listDir(core_folder,with_dirs = False)

	if level < 1:
		for folder_name in folder_name_list:
			if folder_name.lower() == 'examples':
				continue
			cur_folder = os.path.join(core_folder, folder_name)
			sub_asm_src_file_list = getAsmSrcFileListFromFolder(cur_folder, level + 1)
			asm_src_file_list += sub_asm_src_file_list
	
	for file_name in file_name_list:
		cur_file = os.path.join(core_folder, file_name)
		if isAsmSrcFile(cur_file):
			asm_src_file_list.append(cur_file)
	return asm_src_file_list

def getAsmSrcFileListFromFolderList(core_folder_list):
	asm_src_file_list = []
	core_folder_list = expandCorFolderList(core_folder_list)
	for core_folder in core_folder_list:
		sub_asm_src_file_list = getAsmSrcFileListFromFolder(core_folder)
		asm_src_file_list += sub_asm_src_file_list
	return asm_src_file_list

def getFolderListFromFolder(core_folder, level = 0):
	folder_list = [core_folder]
	if level < 1:
		folder_name_list = fileutil.listDir(core_folder, with_files = False)
		for folder_name in folder_name_list:
			if folder_name.lower() == 'examples':
				continue
			cur_folder = os.path.join(core_folder, folder_name)
			folder_list += getFolderListFromFolder(cur_folder, level + 1)
	return folder_list

def getFolderListFromFolderList(core_folder_list):
	folder_list = []
	core_folder_list = expandCorFolderList(core_folder_list)
	for core_folder in core_folder_list:
		folder_list += getFolderListFromFolder(core_folder)
	return folder_list

def expandCoreFolder(lib_folder, platform_name = ''):
	lib_folder_list = []
	if not platform_name:
		platform_name = constant.sketch_settings.get('platform_name', 'General')

	arduino_folder = constant.sketch_settings.get('arduino_folder', '')
	lib_src_folder = os.path.join(lib_folder, 'src')
	if not os.path.isdir(lib_src_folder) or (os.path.isdir(lib_src_folder) and not arduino_folder in lib_src_folder ):
		lib_folder_list.append(lib_folder)
	else:
		lib_folder_list.append(lib_src_folder)
		arch_folder = os.path.join(lib_folder, 'arch')
		avr_folder = os.path.join(arch_folder, 'avr')
		sam_folder = os.path.join(arch_folder, 'sam')
		if 'AVR' in platform_name:
			if os.path.isdir(avr_folder):
				lib_folder_list.append(avr_folder)
		if 'ARM' in platform_name:
			if os.path.isdir(sam_folder):
				lib_folder_list.append(sam_folder)
	return lib_folder_list

def expandCorFolderList(core_folder_list, platform_name = ''):
	folder_list = []
	for core_folder in core_folder_list:
		folder_list += expandCoreFolder(core_folder, platform_name)
	return folder_list

def isInEditor(view):
	view_name = view.name()
	file_name = view.file_name()
	state = False
	if view_name or file_name:
		state = True
	return state
