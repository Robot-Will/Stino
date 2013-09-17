#-*- coding: utf-8 -*-
# stino/base.py

import os
import re

from . import constant
from . import textutil
from . import fileutil
from . import sketch

ino_ext_list = ['.ino', '.pde']
build_folder_name_list = ['cores', 'variants', 'system', 'bootloaders']

class ArduinoInfo:
	def __init__(self):
		self.refresh()
		
	def refresh(self):
		self.version_text = getVersionText()
		self.version = getVersion(self.version_text)
		self.genSketchbook()
		self.genPlatformList()
		self.genKeywordList()

	def getSketchbook(self):
		return self.sketchbook

	def getPlatformList(self):
		return self.platform_list

	def getKeywordList(self):
		return self.keyword_list

	def getKeywordRefDict(self):
		return self.keyword_ref_dict

	def getVersion(self):
		return self.version

	def getVersionText(self):
		return self.version_text

	def genSketchbook(self):
		self.sketchbook = getSketchbook()

	def genPlatformList(self):
		self.platform_list = getPlatformList()

	def genKeywordList(self):
		self.keyword_list = []
		for platform in self.platform_list:
			self.keyword_list += getKeywordListFromPlatform(platform)
		self.keyword_ref_dict = getKeywordRefList(self.keyword_list)

class Platform:
	def __init__(self, name):
		self.name = name
		self.core_folder_list = []
		self.board_list = []
		self.programmer_list = []
		self.example = SketchItem(name)
		self.lib_list = []
		self.h_lib_dict = {}

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getCoreFolderList(self):
		return self.core_folder_list

	def setCoreFolderList(self, folder_list):
		self.core_folder_list = folder_list

	def addCoreFolder(self, core_folder):
		self.core_folder_list.append(core_folder)

	def getBoardList(self):
		return self.board_list

	def addBoardList(self, board_list):
		self.board_list += board_list

	def addBoard(self, board):
		self.board_list.append(board)

	def getProgrammerList(self):
		return self.programmer_list

	def addProgrammerList(self, programmer_list):
		self.programmer_list += programmer_list

	def addProgrammer(self, programmer):
		self.programmer_list.append(programmer)

	def getExample(self):
		return self.example

	def setExample(self, example):
		self.example = example

	def getLibList(self):
		return self.lib_list

	def setLibList(self, lib_list):
		self.lib_list = lib_list

	def getHLibDict(self):
		return self.h_lib_dict

	def setHLibDict(self, h_lib_dict):
		self.h_lib_dict = h_lib_dict

class SketchItem:
	def __init__(self, name):
		self.name = name
		self.folder = ''
		self.children = []

	def hasSubItem(self):
		state = False
		if self.children:
			state = True
		return state

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getFolder(self):
		return self.folder

	def setFolder(self, folder):
		self.folder = folder

	def getSubItemList(self):
		return self.children

	def setSubItemList(self, sub_item_list):
		self.children = sub_item_list

	def addSubItem(self, sub_item):
		self.children.append(sub_item)

	def addSubItemList(self, sub_item_list):
		self.children += sub_item_list

class LibItem:
	def __init__(self, name):
		self.name = name
		self.folder = ''
	
	def hasSubItem(self):
		state = False
		if self.children:
			state = True
		return state

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getFolder(self):
		return self.folder

	def setFolder(self, folder):
		self.folder = folder

class Board:
	def __init__(self, name):
		self.name = name
		self.option_list = []
		self.args = {}
		self.folder = ''

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getArgs(self):
		return self.args

	def setArgs(self, args):
		self.args = args

	def getFolder(self):
		return self.folder

	def setFolder(self, folder):
		self.folder = folder

	def getOptionList(self):
		return self.option_list

	def addOption(self, option):
		self.option_list.append(option)

class BoardOption:
	def __init__(self, name):
		self.name = name
		self.item_list = []

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getItemList(self):
		return self.item_list

	def addItem(self, item):
		self.item_list.append(item)

class BoardOptionItem:
	def __init__(self, name):
		self.name = name
		self.args = {}

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getArgs(self):
		return self.args

	def setArgs(self, args):
		self.args = args

class Programmer:
	def __init__(self, name):
		self.name = name
		self.args = {}

	def getName(self):
		return self.name

	def setName(self, name):
		self.name = name

	def getArgs(self):
		return self.args

	def setArgs(self, args):
		self.args = args

class Keyword:
	def __init__(self, name):
		self.name = name
		self.type = ''
		self.ref = ''

	def getName(self):
		return self.name

	def getType(self):
		return self.type

	def getRef(self):
		return self.ref

	def setName(self, name):
		self.name = name

	def setType(self, keyword_type):
		self.type = keyword_type

	def setRef(self, ref):
		self.ref = ref

def getRealArduinoPath(folder):
	if constant.sys_platform == 'osx':
		folder = os.path.join(folder, 'Contents/Resources/Java')
	return folder

def isArduinoFolder(folder):
	state = False
	if folder and os.path.isdir(folder):
		folder = getRealArduinoPath(folder)
		hardware_path = os.path.join(folder, 'hardware')
		lib_path = os.path.join(folder, 'lib')
		version_file_path = os.path.join(lib_path, 'version.txt')
		if os.path.isdir(hardware_path) and os.path.isfile(version_file_path):
			state = True
	return state

def getArduinoFolder():
	arduino_folder = constant.sketch_settings.get('arduino_folder', '')
	if arduino_folder:
		if not isArduinoFolder(arduino_folder):
			arduino_folder = ''
		else:
			if constant.sys_platform == 'osx':
				arduino_folder = getRealArduinoPath(arduino_folder)
	return arduino_folder

def setArduinoFolder(arduino_folder):
	constant.sketch_settings.set('arduino_folder', arduino_folder)

def isSketchFolder(folder):
	state = False
	file_list = fileutil.listDir(folder, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in ino_ext_list:
			state = True
			break
	return state

def getDefaultSketchbookFolder():
	document_folder = fileutil.getDocumentFolder()
	sketchbook_folder = os.path.join(document_folder, 'Arduino')
	return sketchbook_folder

def getSketchbookFolder():
	sketchbook_folder = constant.global_settings.get('sketchbook_folder', '')
	if (not sketchbook_folder) or (not os.path.isdir(sketchbook_folder)):
		sketchbook_folder = getDefaultSketchbookFolder()
		setSketchbookFolder(sketchbook_folder)
	checkSketchbookFolder(sketchbook_folder)
	return sketchbook_folder

def setSketchbookFolder(sketchbook_folder):
	constant.global_settings.set('sketchbook_folder', sketchbook_folder)

def checkSketchbookFolder(sketchbook_folder):
	libraries_folder = os.path.join(sketchbook_folder, 'libraries')
	hardware_folder = os.path.join(sketchbook_folder, 'hardware')
	folder_list = [sketchbook_folder, libraries_folder, hardware_folder]

	for folder in folder_list:
		if os.path.isfile(folder):
			os.rename(folder, folder+'.bak')
		if not os.path.exists(folder):
			os.makedirs(folder)

def getRootFolderList():
	sketchbook_folder = getSketchbookFolder()
	arduino_folder = getArduinoFolder()

	folder_list = [sketchbook_folder]
	if arduino_folder:
		folder_list.append(arduino_folder)
	return folder_list

def isCoreFolder(folder):
	state = False
	if os.path.isdir(folder):
		cores_folder = os.path.join(folder, 'cores')
		boards_file = os.path.join(folder, 'boards.txt')
		if os.path.isdir(cores_folder) or os.path.isfile(boards_file):
			state = True
	return state

def getCoreFolderList():
	core_folder_list = []
	folder_list = getRootFolderList()

	for folder in folder_list:
		hardware_folder = os.path.join(folder, 'hardware')
		if not os.path.isdir(hardware_folder):
			continue
		sub_folder_name_list = fileutil.listDir(hardware_folder, with_files = False)
		for sub_folder_name in sub_folder_name_list:
			if sub_folder_name == 'tools':
				continue
			sub_folder = os.path.join(hardware_folder, sub_folder_name)
			if isCoreFolder(sub_folder):
				core_folder_list.append(sub_folder)
			else:
				sub_sub_folder_name_list = fileutil.listDir(sub_folder, with_files = False)
				for sub_sub_folder_name in sub_sub_folder_name_list:
					sub_sub_folder = os.path.join(sub_folder, sub_sub_folder_name)
					if isCoreFolder(sub_sub_folder):
						core_folder_list.append(sub_sub_folder)
	return core_folder_list

def getPlatformNameFromFile(platform_file):
	platform_name = ''
	# opened_file = open(platform_file)
	# lines = opened_file.readlines()
	# opened_file.close()
	lines = fileutil.readFileLines(platform_file)

	for line in lines:
		if 'name=' in line:
			(key, value) = textutil.getKeyValue(line)
			platform_name = value
			break
	return platform_name

def getPlatformNameFromCoreFolder(core_folder):
	platform_name = 'Arduino AVR Boards'
	platform_file = os.path.join(core_folder, 'platform.txt')
	if os.path.isfile(platform_file):
		platform_name = getPlatformNameFromFile(platform_file)
	else:
		cores_folder = os.path.join(core_folder, 'cores')
		arduino_src_folder = os.path.join(cores_folder, 'arduino')
		if not os.path.isdir(arduino_src_folder):
			core_folder_name = os.path.split(core_folder)[1]
			platform_name = core_folder_name[0].upper() + core_folder_name[1:] + ' Boards'
	return platform_name

def getPlatformListFromCoreFolderList():
	platform_list = []
	platform_name_list = []
	name_platform_dict = {}

	root_folder_list = getRootFolderList()
	platform = Platform('General')
	platform.setCoreFolderList(root_folder_list)
	platform_list.append(platform)

	core_folder_list = getCoreFolderList()
	for core_folder in core_folder_list:
		platform_name = getPlatformNameFromCoreFolder(core_folder)
		if platform_name:
			if not platform_name in platform_name_list:
				platform = Platform(platform_name)
				platform_name_list.append(platform_name)
				platform_list.append(platform)
				name_platform_dict[platform_name] = platform
			else:
				platform = name_platform_dict[platform_name]
			platform.addCoreFolder(core_folder)
	return platform_list

def getBoardGeneralBlock(board_block):
	block = []
	for line in board_block:
		if 'menu.' in line:
			break
		block.append(line)
	return block

def getBoardOptionBlock(board_block, menu_option_id):
	block = []
	for line in board_block:
		if menu_option_id in line:
			index = line.index(menu_option_id) + len(menu_option_id) + 1
			block.append(line[index:])
	return block

def splitBoardOptionBlock(board_option_block):
	block_list = []

	item_id_list = []
	for line in board_option_block:
		(key, value) = textutil.getKeyValue(line)
		length = len(key.split('.'))
		if length <= 2 :
			item_id = key
			item_id = item_id.replace('name', '')
			item_id_list.append(item_id)

	for item_id in item_id_list:
		block = []
		for line in board_option_block:
			if item_id in line:
				block.append(line)
		block_list.append(block)
	return block_list

def getBlockInfo(block):
	title_line = block[0]
	(item_id, caption) = textutil.getKeyValue(title_line)
	item_id = item_id.replace('.name', '') + '.'

	args = {}
	for line in block[1:]:
		(key, value) = textutil.getKeyValue(line)
		key = key.replace(item_id, '')
		args[key] = value
	return (caption, args)
	
def getBoardListFromFolder(folder, build_folder_list):
	board_list = []
	boards_file = os.path.join(folder, 'boards.txt')
	if os.path.isfile(boards_file):
		# opened_file = open(boards_file, 'r')
		# lines = opened_file.readlines()
		# opened_file.close()
		lines = fileutil.readFileLines(boards_file)

		board_block_list = textutil.getBlockList(lines)

		board_option_id_list = []
		board_option_caption_dict = {}
		header_block = board_block_list[0]
		for line in header_block:
			(board_option_id, caption) = textutil.getKeyValue(line)
			board_option_id_list.append(board_option_id)
			board_option_caption_dict[board_option_id] = caption

		for board_block in board_block_list[1:]:
			board_general_block = getBoardGeneralBlock(board_block)
			(name, args) = getBlockInfo(board_general_block)

			args['build.cores_folder'] = build_folder_list[0]
			args['build.variants_folder'] = build_folder_list[1]
			args['build.system.path'] = build_folder_list[2]
			args['build.uploaders_folder'] = build_folder_list[3]

			cur_board = Board(name)
			cur_board.setFolder(folder)
			cur_board.setArgs(args)
			for board_option_id in board_option_id_list:
				board_option_block = getBoardOptionBlock(board_block, board_option_id)
				if board_option_block:
					cur_board_option = BoardOption(board_option_caption_dict[board_option_id])
					option_item_block_list = splitBoardOptionBlock(board_option_block)
					for option_item_block in option_item_block_list:
						(name, args) = getBlockInfo(option_item_block)
						cur_option_item = BoardOptionItem(name)
						cur_option_item.setArgs(args)
						cur_board_option.addItem(cur_option_item)
					cur_board.addOption(cur_board_option)
			board_list.append(cur_board)
	return board_list

def getProgrammerListFromFolder(folder):
	programmer_list = []
	programmers_file = os.path.join(folder, 'programmers.txt')
	if os.path.isfile(programmers_file):
		# opened_file = open(programmers_file, 'r')
		# lines = opened_file.readlines()
		# opened_file.close()
		lines = fileutil.readFileLines(programmers_file)

		programmer_block_list = textutil.getBlockList(lines)
		for programmer_block in programmer_block_list:
			if programmer_block:
				(name, args) = getBlockInfo(programmer_block)
				if not 'program.extra_params' in args:
					if 'Parallel' in name:
						value = '-F'
					else:
						value = ''
						if 'communication' in args:
							comm_type = args['communication']
							if comm_type == 'serial':
								port = '{serial.port}'
							else:
								port = comm_type
							value += '-P%s' % port
							value += ' '
						if 'speed' in args:
							if not 'program.speed' in args:
								args['program.speed'] = args['speed']
						if 'program.speed' in args:
							speed = args['program.speed']
							value += '-b%s' % speed
					args['program.extra_params'] = value

				cur_programmer = Programmer(name)
				cur_programmer.setArgs(args)
				programmer_list.append(cur_programmer)
	return programmer_list

def getSketchFromFolder(folder, level = 0):
	folder_name = os.path.split(folder)[1]
	sketch = SketchItem(folder_name)
	has_sub_folder = False

	if level < 4:
		sub_folder_name_list = fileutil.listDir(folder, with_files = False)
		if sub_folder_name_list:
			for sub_folder_name in sub_folder_name_list:
				sub_folder = os.path.join(folder, sub_folder_name)
				sub_sketch = getSketchFromFolder(sub_folder, level + 1)
				if sub_sketch.hasSubItem():
					sketch.addSubItem(sub_sketch)
				elif isSketchFolder(sub_folder):
					sub_sketch.setFolder(sub_folder)
					sketch.addSubItem(sub_sketch)
			has_sub_folder = True

	if not has_sub_folder:
		if isSketchFolder(folder):
			sketch.setFolder(folder)

	if level == 0:
		sub_sketch = SketchItem('-')
		sketch.addSubItem(sub_sketch)
	return sketch

def printSketch(sketch, level = 0):
	caption = sketch.getName()
	if level > 0:
		caption = '\t' * level + '|__' + caption
	if not sketch.hasSubItem():
		caption += ' ('
		caption += sketch.getFolder()
		caption += ')'
	print(caption)

	if sketch.hasSubItem():
		for sub_item in sketch.getSubItemList():
			printSketch(sub_item, level+1)

def getSketchbook():
	sketchbook_folder = getSketchbookFolder()
	sketchbook = getSketchFromFolder(sketchbook_folder)
	sketchbook.setName('Sketchbook')
	return sketchbook

def getGeneralLibraryListFromFolder(folder, platform_name = ''):
	lib_list = []
	libraries_folder = os.path.join(folder, 'libraries')
	if os.path.isdir(libraries_folder):
		sub_folder_name_list = fileutil.listDir(libraries_folder, with_files = False)
		for sub_folder_name in sub_folder_name_list:
			sub_folder = os.path.join(libraries_folder, sub_folder_name)
			lib_item = LibItem(sub_folder_name)
			lib_item.setFolder(sub_folder)

			arch_folder = os.path.join(sub_folder, 'arch')
			if os.path.isdir(arch_folder):
				avr_folder = os.path.join(arch_folder, 'avr')
				sam_folder = os.path.join(arch_folder, 'sam')
				if os.path.isdir(avr_folder):
					if 'AVR' in platform_name:
						lib_list.append(lib_item)
				if os.path.isdir(sam_folder):
					if 'ARM' in platform_name:
						lib_list.append(lib_item)
			else:
				if 'General' in platform_name:
					lib_list.append(lib_item)
	if lib_list:
		lib_item = LibItem('-')
		lib_list.append(lib_item)
	return lib_list

def getPlatformLibraryListFromFolder(folder):
	lib_list = []
	libraries_folder = os.path.join(folder, 'libraries')
	if os.path.isdir(libraries_folder):
		sub_folder_name_list = fileutil.listDir(libraries_folder, with_files = False)
		for sub_folder_name in sub_folder_name_list:
			sub_folder = os.path.join(libraries_folder, sub_folder_name)
			lib_item = LibItem(sub_folder_name)
			lib_item.setFolder(sub_folder)
			lib_list.append(lib_item)
	if lib_list:
		lib_item = LibItem('-')
		lib_list.append(lib_item)
	return lib_list

def getLibraryListFromPlatform(platform_list, platform_id):
	lib_list = []
	platform_general = platform_list[0]
	general_core_folder_list = platform_general.getCoreFolderList()

	cur_platform = platform_list[platform_id]
	core_folder_list = cur_platform.getCoreFolderList()

	platform_name = cur_platform.getName()
	for core_folder in general_core_folder_list:
		lib_list += getGeneralLibraryListFromFolder(core_folder, platform_name)

	if platform_id > 0:
		for core_folder in core_folder_list:
			lib_list += getPlatformLibraryListFromFolder(core_folder)
	return lib_list

def getExampleListFromFolder(folder):
	example_list = []
	libraries_folder = os.path.join(folder, 'libraries')
	examples_folder = os.path.join(folder, 'examples')
	sub_folder_list = [examples_folder, libraries_folder]
	for sub_folder in sub_folder_list:
		if os.path.isdir(sub_folder):
			example = getSketchFromFolder(sub_folder)
			example_list.append(example)
	return example_list

def getExampleFromPlatform(platform):
	name = platform.getName()
	example = SketchItem(name)

	example_list = []
	core_folder_list = platform.getCoreFolderList()
	for core_folder in core_folder_list:
		example_list += getExampleListFromFolder(core_folder)

	for cur_example in example_list:
		sub_example_list = cur_example.getSubItemList()
		example.addSubItemList(sub_example_list)
	return example

def hasCoreSrcFolder(folder):
	state = False
	cores_folder = os.path.join(folder, 'cores')
	if os.path.isdir(cores_folder):
		state = True
	return state

def getCoreSrcFolderFromPlatform(platform):
	core_src_folder = ''
	core_folder_list = platform.getCoreFolderList()
	for core_folder in core_folder_list:
		if hasCoreSrcFolder(core_folder):
			# core_src_folder = os.path.join(core_folder, 'cores')
			core_src_folder = core_folder
			break
	return core_src_folder

def findSubFolderInFolderList(folder_list, sub_folder_name):
	sub_folder = ''

	main_folder = ''
	arduino_folder = getArduinoFolder()
	for cur_folder in folder_list:
		if arduino_folder in cur_folder:
			main_folder = cur_folder
			break

	if main_folder:
		cur_sub_folder = os.path.join(main_folder, sub_folder_name)
		if os.path.isdir(cur_sub_folder):
			sub_folder = cur_sub_folder
	
	if not sub_folder:
		for cur_folder in folder_list:
			cur_sub_folder = os.path.join(cur_folder, sub_folder_name)
			if os.path.isdir(cur_sub_folder):
				sub_folder = cur_sub_folder
				break
	return sub_folder

def getDefaultBuildFolderList(core_folder_list, folder_name_list):
	default_build_folder_list = []
	for folder_name in folder_name_list:
		index = folder_name_list.index(folder_name)
		cur_folder = findSubFolderInFolderList(core_folder_list, folder_name)
		default_build_folder_list.append(cur_folder)
	return default_build_folder_list

def getFolderBuildFolderDict(core_folder_list, folder_name_list):
	folder_build_folder_dict = {}
	default_build_folder_list = getDefaultBuildFolderList(core_folder_list, folder_name_list)
	for core_folder in core_folder_list:
		build_folder_list = []
		for folder_name in folder_name_list:
			index = folder_name_list.index(folder_name)
			cur_folder = os.path.join(core_folder, folder_name)
			if not os.path.isdir(cur_folder):
				cur_folder = default_build_folder_list[index]
			build_folder_list.append(cur_folder)
		folder_build_folder_dict[core_folder] = build_folder_list
	return folder_build_folder_dict

def getPlatformList():
	platform_list = getPlatformListFromCoreFolderList()
	for platform in platform_list:
		platform_name = platform.getName()
		index = platform_list.index(platform)
		core_folder_list = platform.getCoreFolderList()
		folder_build_folder_dict = getFolderBuildFolderDict(core_folder_list, build_folder_name_list)

		example = getExampleFromPlatform(platform)
		lib_list = getLibraryListFromPlatform(platform_list, index)
		h_lib_dict = getHLibDict(lib_list, platform_name)

		platform.setExample(example)
		platform.setLibList(lib_list)
		platform.setHLibDict(h_lib_dict)

		for core_folder in core_folder_list:
			build_folder_list = folder_build_folder_dict[core_folder]
			board_list = getBoardListFromFolder(core_folder, build_folder_list)
			programmer_list = getProgrammerListFromFolder(core_folder)
			platform.addBoardList(board_list)
			platform.addProgrammerList(programmer_list)
	return platform_list

def getVersionText():
	version_text = '1.0.5'
	arduino_root = getArduinoFolder()
	if arduino_root:
		lib_folder = os.path.join(arduino_root, 'lib')
		version_file = os.path.join(lib_folder, 'version.txt')
		if os.path.isfile(version_file):
			# opened_file = open(version_file)
			# lines = opened_file.readlines()
			# opened_file.close()
			lines = fileutil.readFileLines(version_file)
			for line in lines:
				line = line.strip()
				if line:
					version_text = line
					break
	return version_text

def getVersion(version_text):
	version = 105
	patter_text = r'[\d.]+'
	pattern = re.compile(patter_text)
	match = pattern.search(version_text)
	if match:
		version_text = match.group()
		number_list = version_text.split('.')
		version = 0
		power = 0
		for number in number_list:
			number = int(number)
			version += number * (10 ** power)
			power -= 1
		version *= 100
	return int(version)

def getKeywordListFromFile(keywords_file):
	keyword_list = []
	# opened_file = open(keywords_file, 'r')
	# lines = opened_file.readlines()
	# opened_file.close()
	lines = fileutil.readFileLines(keywords_file)

	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			word_list = re.findall(r'\S+', line)
			if len(word_list) > 1:
				keyword_name = word_list[0]
				if len(word_list) == 3:
					keyword_type = word_list[1]
					keyword_ref = word_list[2]
				elif len(word_list) == 2:
					if 'LITERAL' in word_list[1] or 'KEYWORD' in word_list[1]:
						keyword_type = word_list[1]
						keyword_ref = ''
					else:
						keyword_type = ''
						keyword_ref = word_list[1]
				cur_keyword = Keyword(keyword_name)
				cur_keyword.setType(keyword_type)
				cur_keyword.setRef(keyword_ref)
				keyword_list.append(cur_keyword)
	return keyword_list

def getKeywordListFromCoreFolderList(core_folder_list):
	keyword_list = []
	for core_folder in core_folder_list:
		lib_folder = os.path.join(core_folder, 'lib')
		keywords_file = os.path.join(lib_folder, 'keywords.txt')
		if os.path.isfile(keywords_file):
			cur_keyword_list = getKeywordListFromFile(keywords_file)
			keyword_list += cur_keyword_list
	return keyword_list

def getKeywordListFromLibList(lib_list):
	keyword_list = []
	for lib in lib_list:
		lib_folder = lib.getFolder()
		keywords_file = os.path.join(lib_folder, 'keywords.txt')
		if os.path.isfile(keywords_file):
			cur_keyword_list = getKeywordListFromFile(keywords_file)
			keyword_list += cur_keyword_list
	return keyword_list

def getKeywordListFromPlatform(platform):
	keyword_list = []
	core_folder_list = platform.getCoreFolderList()
	lib_list = platform.getLibList()
	keyword_list += getKeywordListFromCoreFolderList(core_folder_list)
	keyword_list += getKeywordListFromLibList(lib_list)
	return keyword_list

def getKeywordRefList(keyword_list):
	keyword_ref_dict = {}
	for keyword in keyword_list:
		ref = keyword.getRef()
		if ref and ref[0].isupper():
			keyword_name = keyword.getName()
			keyword_ref_dict[keyword_name] = ref
	return keyword_ref_dict

def getUrl(url):
	file_name = url + '.html'
	arduino_folder = getArduinoFolder()
	reference_folder = os.path.join(arduino_folder, 'reference')
	reference_file = os.path.join(reference_folder, file_name)
	if os.path.isfile(reference_file):
		reference_file = reference_file.replace(os.path.sep, '/')
		url = 'file://' + reference_file
	else:
		url = 'http://arduino.cc'
	return url

def getSelectedTextFromView(view):
	selected_text = ''
	region_list = view.sel()
	for region in region_list:
		selected_region = view.word(region)
		selected_text += view.substr(selected_region)
		selected_text += '\n'
	return selected_text

def getWordListFromText(text):
	pattern_text = r'\b\w+\b'
	word_list = re.findall(pattern_text, text)
	return word_list

def getSelectedWordList(view):
	selected_text = getSelectedTextFromView(view)
	word_list = getWordListFromText(selected_text)
	return word_list

def getHLibDict(lib_list, platform_name):
	h_lib_dict = {}
	for lib in lib_list:
		lib_folder = lib.getFolder()
		h_list = sketch.getHSrcFileList(lib_folder, platform_name)
		for h in h_list:
			h_lib_dict[h] = lib_folder
	return h_lib_dict

def newSketch(sketch_name):
	sketch_file = ''
	sketchbook_folder = getSketchbookFolder()
	sketch_folder = os.path.join(sketchbook_folder, sketch_name)

	if not os.path.exists(sketch_folder):
		os.makedirs(sketch_folder)
		file_name = sketch_name + '.ino'
		sketch_file = os.path.join(sketch_folder, file_name)

		text = '// %s\n\n' % file_name
		text += 'void setup() {\n\n'
		text += '}\n\n'
		text += 'void loop() {\n\n'
		text += '}\n\n'
		fileutil.writeFile(sketch_file, text)
	return sketch_file