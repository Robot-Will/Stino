#-*- coding: utf-8 -*-
# stino/fileutil.py

import sublime
import os
import sys
import codecs
import locale

sys_version = int(sys.version[0])
sys_platform = sublime.platform()

if sys_platform == 'osx':
	sys_encoding = 'utf-8'
else:
	sys_encoding = codecs.lookup(locale.getpreferredencoding()).name

def getWinVolumeList():
	vol_list = []
	for label in range(65, 91):
		vol = chr(label) + ':\\'
		if os.path.isdir(vol):
			vol_list.append(vol)
	return vol_list

def getOSRootList():
	root_list = []
	if sys_platform == 'windows':
		root_list = getWinVolumeList()
	else:
		root_list = ['/']
	return root_list

def getDocumentFolder():
	if sys_platform == 'windows':
		if sys_version < 3:
			import _winreg as winreg
		else:
			import winreg
		key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,\
	            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
		document_folder = winreg.QueryValueEx(key, 'Personal')[0]
	elif sys_platform == 'osx':
		home_folder = os.getenv('HOME')
		document_folder = os.path.join(home_folder, 'Documents')
	else:
		document_folder = os.getenv('HOME')
	return document_folder

def listDir(folder, with_files = True, with_dirs = True):
	if sys_version < 3:
		if not isinstance(folder, unicode):
			folder = folder.decode(sys_encoding)

	file_list = []
	if os.path.isdir(folder):
		try:
			original_file_list = os.listdir(folder)
		except IOError:
			pass
		else:
			for cur_file in original_file_list:
				if cur_file[0] == '$' or cur_file[0] == '.' or cur_file == 'CVS' or '.tmp' in cur_file:
					continue
				cur_file_path = os.path.join(folder, cur_file)
				if os.path.isdir(cur_file_path):
					if with_dirs:
						file_list.append(cur_file)
				else:
					if with_files:
						file_list.append(cur_file)
	file_list.sort()
	return file_list

def enterNextLevel(index, folder_list, level, top_folder_list):
	chosen_folder = folder_list[index]
	chosen_folder = os.path.normpath(chosen_folder)
	if level > 0:
		if index == 1:
			level -= 1
		elif index > 1:
			level += 1
	else:
		level += 1

	if level == 0:
		sub_folder_list = top_folder_list
	else:
		if level == 1 or index > 0:
			try:
				sub_folder_name_list = listDir(chosen_folder, with_files = False)
			except IOError:
				level -= 1
				sub_folder_list = folder_list
			else:
				sub_folder_list = []
				sub_folder_list.append('Select current folder (%s)' % chosen_folder)
				sub_folder_list.append(os.path.join(chosen_folder, '..'))
				for sub_folder_name in sub_folder_name_list:
					sub_folder = os.path.join(chosen_folder, sub_folder_name)
					sub_folder_list.append(sub_folder)
		else:
			sub_folder_list = folder_list
	return (sub_folder_list, level)

def getFolderNameList(folder_list):
	folder_name_list = []
	index = 0
	for folder in folder_list:
		if index == 0:
			folder_name_list.append(folder)
		else:
			folder_name = os.path.split(folder)[1]
			if not folder_name:
				folder_name = folder
			folder_name_list.append(folder_name)
		index += 1

	if sys_version < 3:
		new_list = []
		for folder_name in folder_name_list:
			new_list.append(folder_name)
		folder_name_list = new_list
	return folder_name_list

def getFileListOfExt(folder, ext_list):
	file_list = []
	file_name_list = listDir(folder, with_dirs = False)
	for file_name in file_name_list:
		file_ext = os.path.splitext(file_name)[1]
		if file_ext in ext_list:
			cur_file = os.path.join(folder, file_name)
			file_list.append(cur_file)
	return file_list

def readFile(cur_file, encoding = 'utf-8'):
	text = ''
	if sys_version < 3:
		opened_file = codecs.open(cur_file, 'r', encoding = encoding)
		text = opened_file.read()
		opened_file.close()
	else:
		opened_file = open(cur_file, 'r', encoding = encoding)
		text = opened_file.read()
		opened_file.close()
	return text

def readFileLines(cur_file):
	text =readFile(cur_file)
	lines = text.splitlines(True)
	return lines

def writeFile(cur_file, text, encoding = 'utf-8'):
	if sys_version < 3:
		opened_file = codecs.open(cur_file, 'w', encoding = encoding)
		opened_file.write(text)
		opened_file.close()
	else:
		opened_file = open(cur_file, 'w', encoding = encoding)
		opened_file.write(text)
		opened_file.close()
