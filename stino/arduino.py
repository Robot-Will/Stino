#-*- coding: utf-8 -*-
# stino/arduino.py

import os
import re

from stino import utils
from stino import const
from stino import osfile
from stino import src

def isArduinoRoot(path):
	state = False
	if path and os.path.isdir(path):
		path = osfile.getRealPath(path)
		hardware_path = os.path.join(path, 'hardware')
		lib_path = os.path.join(path, 'lib')
		version_file_path = os.path.join(lib_path, 'version.txt')
		if os.path.isdir(hardware_path) and os.path.isfile(version_file_path):
			state = True
	return state

def convertTextToVersion(version_text):
	if not '.' in version_text:
		version = int(version_text)
	else:
		number_patter_text = r'[\d.]+'
		number_pattern = re.compile(number_patter_text)
		match = number_pattern.search(version_text)
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
		else:
			version = 1000
	return int(version)

def parseVersionInfo(arduino_root):
	version = 1000
	version_text = 'unknown'
	lib_path = os.path.join(arduino_root, 'lib')
	version_file_path = os.path.join(lib_path, 'version.txt')
	if os.path.isfile(version_file_path):
		lines = osfile.readFileLines(version_file_path)
		for line in lines:
			line = line.strip()
			if line:
				version_text = line
				break
	if version_text != 'unknown':
		version = convertTextToVersion(version_text)
	return (version, version_text)

def isSketchFolder(path):
	state = False
	src_ext_list = src.src_ext_list
	file_list = osfile.listDir(path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in src_ext_list:
			state = True
			break
	return state

def isCoreRoot(path):
	state = False
	if os.path.isdir(path):
		cores_path = os.path.join(path, 'cores')
		boards_file_path = os.path.join(path, 'boards.txt')
		if os.path.isdir(cores_path) or os.path.isfile(boards_file_path):
			state = True
	return state

def getPlatformFromFile(platform_file_path):
	lines = osfile.readFileLines(platform_file_path)
	for line in lines:
		if 'name=' in line:
			(key, value) = utils.getKeyValue(line)
			platform = value
			break
	return platform

def getPlatformFromCoreRoot(core_root):
	platform = 'Arduino AVR Boards'
	platform_file_path = os.path.join(core_root, 'platform.txt')
	if os.path.isfile(platform_file_path):
		platform = getPlatformFromFile(platform_file_path)
	else:
		cores_path = os.path.join(core_root, 'cores')
		if os.path.isdir(cores_path):
			arduino_path = os.path.join(cores_path, 'arduino')
			if not os.path.isdir(arduino_path):
				core_root_folder_name = os.path.split(core_root)[1]
				platform = core_root_folder_name + ' Boards'
	return platform

def findCoresPath(core_root_list):
	cores_path = ''
	for core_root in core_root_list:
		path = os.path.join(core_root, 'cores')
		if os.path.isdir(path):
			cores_path = path
			break
	return cores_path

def splitBoardsFile(boards_file_path):
	boards_file_header_block = []
	boards_file_body_block = []
	lines = osfile.readFileLines(boards_file_path)
	is_header = True
	for line in lines:
		if '.name' in line:
			is_header = False
		if is_header:
			boards_file_header_block.append(line)
		else:
			boards_file_body_block.append(line)
	return (boards_file_header_block, boards_file_body_block)

def isBoard150(boards_file_path):
	state = False
	text = osfile.readFileText(boards_file_path)
	if '.container=' in text:
		state = True
	return state

def parseBoardHeader(boards_file_header_block):
	board_type_list = []
	board_type_caption_dict = {}
	for line in boards_file_header_block:
		line = line.strip()
		if line and (not '#' in line):
			if '=' in line:
				(board_type, board_type_caption) = utils.getKeyValue(line)
				if not board_type in board_type_list:
					board_type_list.append(board_type)
					board_type_caption_dict[board_type] = board_type_caption
	return (board_type_list, board_type_caption_dict)
				
def parseBoardFile150(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}

	board_type = 'menu.cpu'
	board_type_list = [board_type]
	type_key = utils.genKey(board_type, platform)
	type_caption_dict = {type_key:'Processor'}

	lines = osfile.readFileLines(boards_file_path)
	board_info_block_list = utils.splitToBlocks(lines, sep = '.name')
	for board_info_block in board_info_block_list:
		cpu = ''
		for line in board_info_block:
			if '.name' in line:
				(key, board) = utils.getKeyValue(line)
			if '.cpu' in line:
				(key, cpu) = utils.getKeyValue(line)
			if '.container' in line:
				(key, board) = utils.getKeyValue(line)
				break

		board_key = utils.genKey(board, platform)
		key = utils.genKey(board_type, board_key)

		if not board in board_list:
			board_list.append(board)

			board_file_dict[board_key] = boards_file_path
			if cpu:
				board_type_list_dict[board_key] = board_type_list
				board_item_list_dict[key] = [cpu]
		else:
			if cpu and (not cpu in board_item_list_dict[key]):
				board_item_list_dict[key].append(cpu)
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseBoardFile(platform, boards_file_path):
	board_list = []
	board_file_dict = {}
	board_type_list_dict = {}
	board_item_list_dict = {}
	type_caption_dict = {}

	(boards_file_header_block, boards_file_body_block) = splitBoardsFile(boards_file_path)
	(board_type_list, board_type_caption_dict) = parseBoardHeader(boards_file_header_block)

	for board_type in board_type_caption_dict:
		type_key = utils.genKey(board_type, platform)
		type_caption_dict[type_key] = board_type_caption_dict[board_type]

	board_info_block_list = utils.splitToBlocks(boards_file_body_block, sep = '.name', none_sep = 'menu.')
	for board_info_block in board_info_block_list:
		board_name_line = board_info_block[0]
		(key, board) = utils.getKeyValue(board_name_line)
		if not board in board_list:
			board_list.append(board)

			board_key = utils.genKey(board, platform)
			board_file_dict[board_key] = boards_file_path
			board_type_list_dict[board_key] = []

			for board_type in board_type_list:
				item_list = []
				board_type_info_block = utils.getTypeInfoBlock(board_info_block, board_type)
				item_blocks = utils.splitToBlocks(board_type_info_block, sep = '.name', key_length = 4)
				for item_block in item_blocks:
					item_name_line = item_block[0]
					(key, item) = utils.getKeyValue(item_name_line)
					if not item in item_list:
						item_list.append(item)
				if item_list:
					board_type_list_dict[board_key].append(board_type)
					key = utils.genKey(board_type, board_key)
					board_item_list_dict[key] = item_list
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseBoardInfo(platform, core_root):
	board_list = []
	boards_file_path = os.path.join(core_root, 'boards.txt')
	if os.path.isfile(boards_file_path):
		if isBoard150(boards_file_path):
			(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardFile150(platform, boards_file_path)
		else:
			(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardFile(platform, boards_file_path)
	return (board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict)

def parseProgrammerInfo(platform, core_root):
	programmer_list = []
	programmer_file_dict = {}
	programmers_file_path = os.path.join(core_root, 'programmers.txt')
	if os.path.isfile(programmers_file_path):
		lines = osfile.readFileLines(programmers_file_path)
		programmer_info_block_list = utils.splitToBlocks(lines, sep = '.name')
		for programmer_info_block in programmer_info_block_list:
			programmer_name_line = programmer_info_block[0]
			(key, programmer) = utils.getKeyValue(programmer_name_line)
			if not programmer in programmer_list:
				programmer_list.append(programmer)

				programmer_key = utils.genKey(programmer, platform)
				programmer_file_dict[programmer_key] = programmers_file_path
	return (programmer_list, programmer_file_dict)

def isLibraryFolder(path):
	state = False
	header_ext_list = src.header_ext_list
	file_list = osfile.listDir(path, with_dirs = False)
	for cur_file in file_list:
		cur_file_ext = os.path.splitext(cur_file)[1]
		if cur_file_ext in header_ext_list:
			state = True
			break
	return state

def parseLibraryInfo(platform, root):
	library_list = []
	library_path_dict = {}
	libraries_path = os.path.join(root, 'libraries')
	dir_list = osfile.listDir(libraries_path, with_files = False)
	for cur_dir in dir_list:
		cur_dir_path = os.path.join(libraries_path, cur_dir)
		if isLibraryFolder(cur_dir_path):
			library_list.append(cur_dir)
			key = utils.genKey(cur_dir, platform)
			library_path_dict[key] = cur_dir_path
	return (library_list, library_path_dict)

def parseExampleInfo(platform, root):
	example_list = []
	example_path_dict = {}
	examples_path = os.path.join(root, 'examples')
	dir_list = osfile.listDir(examples_path, with_files = False)
	for cur_dir in dir_list:
		example_list.append(cur_dir)
		key = utils.genKey(cur_dir, platform)
		cur_dir_path = os.path.join(examples_path, cur_dir)
		example_path_dict[key] = cur_dir_path
	return (example_list, example_path_dict)

def parseLibraryExampleInfo(platform, library_path_list):
	example_list = []
	example_path_dict = {}
	for library_path in library_path_list:
		examples_path = os.path.join(library_path, 'examples')
		if os.path.isdir(examples_path):
			example_name = os.path.split(library_path)[1]
			example_list.append(example_name)
			key = utils.genKey(example_name, platform)
			example_path_dict[key] = examples_path
	return (example_list, example_path_dict)

def parseKeywordListFromFile(keywords_file_path):
	keyword_list = []
	keyword_type_dict = {}
	keyword_ref_dict = {}
	lines = osfile.readFileLines(keywords_file_path)
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			word_list = re.findall(r'\S+', line)
			if len(word_list) > 1:
				keyword = word_list[0]
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
				if not keyword in keyword_list:
					keyword_list.append(keyword)
					keyword_type_dict[keyword] = keyword_type
					keyword_ref_dict[keyword] = keyword_ref
	return (keyword_list, keyword_type_dict, keyword_ref_dict)

def parseKeywordList(platform, lib_path_list):
	keyword_list = []
	keyword_type_dict = {}
	keyword_ref_dict = {}

	for lib_path in lib_path_list:
		keywords_file_path = os.path.join(lib_path, 'keywords.txt')
		if os.path.isfile(keywords_file_path):
			(keyword_list_form_file, keyword_type_dict_from_file, keyword_ref_dict_from_file) = parseKeywordListFromFile(keywords_file_path)
			for keyword in keyword_list_form_file:
				if not keyword in keyword_list:
					keyword_list.append(keyword)
					key = utils.genKey(keyword, platform)
					keyword_type_dict[key] = keyword_type_dict_from_file[keyword]
					keyword_ref_dict[key] = keyword_ref_dict_from_file[keyword]
	return (keyword_list, keyword_type_dict, keyword_ref_dict)

class Arduino:
	def __init__(self):
		self.sketch_list = []
		self.sketch_path_dict = {}
		self.platform_list = []
		self.platform_core_root_list_dict = {}
		self.platform_cores_path_dict = {}
		self.platform_board_lists_dict = {}
		self.board_file_dict = {}
		self.board_type_list_dict = {}
		self.board_item_list_dict = {}
		self.type_caption_dict = {}
		self.platform_programmer_lists_dict = {}
		self.programmer_file_dict = {}
		self.platform_library_lists_dict = {}
		self.library_path_dict = {}
		self.platform_example_lists_dict = {}
		self.example_path_dict = {}
		self.version = 0
		self.version_text = 'unknown'

		self.update()

	def update(self):
		self.sketchbookUpdate()
		if self.isReady():
			self.boardUpdate()

	def sketchbookUpdate(self):
		self.genSketchList()

	def boardUpdate(self):
		self.genVersion()
		self.genPlatformBoardLists()
		self.genPlatformProgrammerLists()
		self.genPlatformLibraryLists()
		self.genPlatformExampleLists()
		self.genKeywordList()
		self.genOperatorList()

	def isReady(self):
		state = False
		arduino_root = self.getArduinoRoot()
		if arduino_root:
			state = True
		return state

	def genSketchList(self):
		self.sketch_list = []
		self.sketch_path_dict = {}
		sketchbook_root = self.getSketchbookRoot()
		dir_list = osfile.listDir(sketchbook_root, with_files = False)
		for cur_dir in dir_list:
			cur_dir_path = os.path.join(sketchbook_root, cur_dir)
			if isSketchFolder(cur_dir_path):
				self.sketch_list.append(cur_dir)
				self.sketch_path_dict[cur_dir] = cur_dir_path

	def genVersion(self):
		arduino_root = self.getArduinoRoot()
		(self.version, self.version_text) = parseVersionInfo(arduino_root)

	def genCoreRootList(self):
		core_root_list = []
		arduino_root = self.getArduinoRoot()
		sketchbook_root = self.getSketchbookRoot()
		path_list = [arduino_root, sketchbook_root]
		for path in path_list:
			hardware_path = os.path.join(path, 'hardware')
			dir_list = osfile.listDir(hardware_path, with_files = False)
			for cur_dir in dir_list:
				if cur_dir == 'tools':
					continue
				cur_dir_path = os.path.join(hardware_path, cur_dir)
				if isCoreRoot(cur_dir_path):
					core_root_list.append(cur_dir_path)
				else:
					subdir_list = osfile.listDir(cur_dir_path)
					for cur_subdir in subdir_list:
						cur_subdir_path = os.path.join(cur_dir_path, cur_subdir)
						if isCoreRoot(cur_subdir_path):
							core_root_list.append(cur_subdir_path)
		return core_root_list

	def genPlatformList(self):
		self.platform_list = []
		self.platform_core_root_list_dict = {}
		self.platform_cores_path_dict = {}

		core_root_list = self.genCoreRootList()
		for core_root in core_root_list:
			platform = getPlatformFromCoreRoot(core_root)
			if not platform in self.platform_list:
				self.platform_list.append(platform)
				self.platform_core_root_list_dict[platform] = [core_root]
			else:
				self.platform_core_root_list_dict[platform].append(core_root)
		
		for platform in self.platform_list:
			core_root_list = self.getCoreRootList(platform)
			cores_path = findCoresPath(core_root_list)
			self.platform_cores_path_dict[platform] = cores_path

		for platform in self.platform_cores_path_dict:
			cores_path = self.getCoresPath(platform)
			if not cores_path:
				self.platform_list.remove(platform)
		return self.platform_list

	def genPlatformBoardLists(self):
		self.platform_board_lists_dict = {}
		self.board_file_dict = {}
		self.board_type_list_dict = {}
		self.board_item_list_dict = {}
		self.type_caption_dict = {}

		platform_list = self.genPlatformList()
		for platform in platform_list:
			self.platform_board_lists_dict[platform] = []
			self.board_type_list_dict[platform] = []
			core_root_list = self.getCoreRootList(platform)
			for core_root in core_root_list:
				(board_list, board_file_dict, board_type_list_dict, board_item_list_dict, type_caption_dict) = parseBoardInfo(platform, core_root)
				if board_list:
					self.platform_board_lists_dict[platform].append(board_list)
					self.board_file_dict.update(board_file_dict)
					self.board_type_list_dict.update(board_type_list_dict)
					self.board_item_list_dict.update(board_item_list_dict)
					self.type_caption_dict.update(type_caption_dict)

	def genPlatformProgrammerLists(self):
		self.platform_programmer_lists_dict = {}
		self.programmer_file_dict = {}
		platform_list = self.getPlatformList()
		for platform in platform_list:
			self.platform_programmer_lists_dict[platform] = []
			core_root_list = self.getCoreRootList(platform)
			for core_root in core_root_list:
				(programmer_list, programmer_file_dict) = parseProgrammerInfo(platform, core_root)
				if programmer_list:
					self.platform_programmer_lists_dict[platform].append(programmer_list)
					self.programmer_file_dict.update(programmer_file_dict)

	def genPlatformLibraryLists(self):
		self.platform_library_lists_dict = {}
		self.library_path_dict = {}

		arduino_root = self.getArduinoRoot()
		sketchbook_root = self.getSketchbookRoot()

		platform_list = self.getPlatformList()
		for platform in platform_list:
			self.platform_library_lists_dict[platform] = []
			core_root_list = self.getCoreRootList(platform)
			root_list = [arduino_root, sketchbook_root]
			root_list += core_root_list
			for root in root_list:
				(library_list, library_path_dict) = parseLibraryInfo(platform, root)
				if library_list:
					self.platform_library_lists_dict[platform].append(library_list)
					self.library_path_dict.update(library_path_dict)

	def genPlatformExampleLists(self):
		self.platform_example_lists_dict = {}
		self.example_path_dict = {}

		arduino_root = self.getArduinoRoot()
		platform_list = self.getPlatformList()
		for platform in platform_list:
			self.platform_example_lists_dict[platform] = []
			(example_list, example_path_dict) = parseExampleInfo(platform, arduino_root)
			if example_list:
				self.platform_example_lists_dict[platform].append(example_list)
				self.example_path_dict.update(example_path_dict)
			
			library_lists = self.getLibraryLists(platform)
			for library_list in library_lists:
				library_path_list = [self.getLibraryPath(platform, library) for library in library_list]
				(example_list, example_path_dict) = parseLibraryExampleInfo(platform, library_path_list)
				if example_list:
					self.platform_example_lists_dict[platform].append(example_list)
					self.example_path_dict.update(example_path_dict)

	def genKeywordList(self):
		self.platform_keyword_list_dict = {}
		self.keyword_type_dict = {}
		self.keyword_ref_dict = {}

		arduino_root = self.getArduinoRoot()
		lib_path = os.path.join(arduino_root, 'lib')

		platform_list = self.getPlatformList()
		for platform in platform_list:
			lib_path_list = [lib_path]
			library_lists = self.getLibraryLists(platform)
			for library_list in library_lists:
				library_path_list = [self.getLibraryPath(platform, library) for library in library_list]
				lib_path_list += library_path_list
			(keyword_list, keyword_type_dict, keyword_ref_dict) = parseKeywordList(platform, lib_path_list)
			self.platform_keyword_list_dict[platform] = keyword_list
			self.keyword_type_dict.update(keyword_type_dict)
			self.keyword_ref_dict.update(keyword_ref_dict)

	def genOperatorList(self):
		self.platform_operator_list_dict = {}
		platform_list = self.getPlatformList()
		for platform in platform_list:
			operator_list =[]
			keyword_list = self.getKeywordList(platform)
			for keyword in keyword_list:
				keyword_type = self.getKeywordType(platform, keyword)
				keyword_ref = self.getKeywordRef(platform, keyword)
				if (not keyword_type) and keyword_ref:
					operator_list.append(keyword)
			self.platform_operator_list_dict[platform] = operator_list

	def setArduinoRoot(self, arduino_root):
		const.settings.set('arduino_root', arduino_root)

	def getArduinoRoot(self):
		arduino_root = const.settings.get('arduino_root')
		if not isArduinoRoot(arduino_root):
			arduino_root = self.getDefaultArduinoRoot()
		if arduino_root:
			arduino_root = osfile.getRealPath(arduino_root)
		return arduino_root

	def getDefaultArduinoRoot(self):
		arduino_root = ''
		if const.sys_platform == 'osx':
			arduino_root = '/Applications/Arduino'
		elif const.sys_platform == 'linux':
			arduino_root = '/usr/share/arduino'
		if not isArduinoRoot(arduino_root):
			arduino_root = None
		return arduino_root

	def setSketchbookRoot(self, sketchbook_root):
		const.settings.set('sketchbook_root', sketchbook_root)
		libraries_path = os.path.join(sketchbook_root, 'libraries')
		hardware_path = os.path.join(sketchbook_root, 'hardware')
		path_list = [sketchbook_root, libraries_path, hardware_path]
		for path in path_list:
			if not os.path.exists(path):
				os.makedirs(path)

	def getSketchbookRoot(self):
		sketchbook_root = const.settings.get('sketchbook_root')
		if not (sketchbook_root and os.path.isdir(sketchbook_root)):
			sketchbook_root = self.getDefaultSketchbookRoot()
			self.setSketchbookRoot(sketchbook_root)
		return sketchbook_root

	def getDefaultSketchbookRoot(self):
		if const.sys_platform == 'windows':
			import _winreg
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,\
	            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
			document_root = _winreg.QueryValueEx(key, 'Personal')[0]
			sketchbook_root = os.path.join(document_root, 'Arduino')
		elif const.sys_platform == 'linux':
			home_root = os.getenv('HOME')
			sketchbook_root = os.path.join(home_root, 'sketchbook')
		elif const.sys_platform == 'osx':
			home_root = os.getenv('HOME')
			document_root = os.path.join(home_root, 'Documents')
			sketchbook_root = os.path.join(document_root, 'Arduino')
		return sketchbook_root

	def getSketchList(self):
		return self.sketch_list

	def getSketchPath(self, sketch):
		path = ''
		if sketch in self.sketch_path_dict:
			path = self.sketch_path_dict[sketch]
		return path

	def getPlatformList(self):
		return self.platform_list

	def getCoreRootList(self, platform):
		core_root_list = []
		if platform in self.platform_list:
			core_root_list = self.platform_core_root_list_dict[platform]
		return core_root_list

	def getCoresPath(self, platform):
		cores_path = ''
		if platform in self.platform_list:
			cores_path = self.platform_cores_path_dict[platform]
		return cores_path

	def getBoardLists(self, platform):
		board_lists = []
		if platform in self.platform_list:
			board_lists = self.platform_board_lists_dict[platform]
		return board_lists

	def getBoardFile(self, platform, board):
		file_path = ''
		key = utils.genKey(board, platform)
		if key in self.board_file_dict:
			file_path = self.board_file_dict[key]
		return file_path

	def getBoardTypeList(self, platform, board):
		type_list = []
		key = utils.genKey(board, platform)
		if key in self.board_type_list_dict:
			type_list = self.board_type_list_dict[key]
		return type_list

	def getBoardItemList(self, platform, board, board_type):
		item_list = []
		board_key = utils.genKey(board, platform)
		type_key = utils.genKey(board_type, board_key)
		if type_key in self.board_item_list_dict:
			item_list = self.board_item_list_dict[type_key]
		return item_list

	def getPlatformTypeCaption(self, platform, board_type):
		caption = ''
		key = utils.genKey(board_type, platform)
		if key in self.type_caption_dict:
			caption = self.type_caption_dict[key]
		return caption

	def getProgrammerLists(self, platform):
		programmer_lists = []
		if platform in self.platform_list:
			programmer_lists = self.platform_programmer_lists_dict[platform]
		return programmer_lists

	def getProgrammerFile(self, platform, programmer):
		file_path = ''
		key = utils.genKey(programmer, platform)
		if key in self.programmer_file_dict:
			file_path = self.programmer_file_dict[key]
		return file_path

	def getLibraryLists(self, platform):
		library_lists = []
		if platform in self.platform_list:
			library_lists = self.platform_library_lists_dict[platform]
		return library_lists

	def getLibraryPath(self, platform, library):
		path = ''
		key = utils.genKey(library, platform)
		if key in self.library_path_dict:
			path = self.library_path_dict[key]
		return path

	def getLibraryPathList(self, platform):
		library_lists = self.getLibraryLists(platform)
		library_path_list = []
		for library_list in library_lists:
			for library in library_list:
				library_path = self.getLibraryPath(platform, library)
				if not library_path in library_path_list:
					library_path_list.append(library_path)
		return library_path_list

	def getExampleLists(self, platform):
		example_lists = []
		if platform in self.platform_list:
			example_lists = self.platform_example_lists_dict[platform]
		return example_lists

	def getExamplePath(self, platform, example):
		path = ''
		key = utils.genKey(example, platform)
		if key in self.example_path_dict:
			path = self.example_path_dict[key]
		return path

	def getKeywordList(self, platform):
		keyword_list = []
		if platform in self.platform_list:
			keyword_list = self.platform_keyword_list_dict[platform]
		return keyword_list

	def getKeywordType(self, platform, keyword):
		keyword_type = ''
		key = utils.genKey(keyword, platform)
		if key in self.keyword_type_dict:
			keyword_type = self.keyword_type_dict[key]
		return keyword_type

	def getKeywordRef(self, platform, keyword):
		keyword_ref = ''
		key = utils.genKey(keyword, platform)
		if key in self.keyword_ref_dict:
			keyword_ref = self.keyword_ref_dict[key]
		return keyword_ref

	def getOperatorList(self, platform):
		operator_list = []
		if platform in self.platform_operator_list_dict:
			operator_list = self.platform_operator_list_dict[platform]
		return operator_list

	def getVersion(self):
		return self.version

	def getVersionText(self):
		return self.version_text