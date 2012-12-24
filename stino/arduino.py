#-*- coding: utf-8 -*-
import sublime
import os, sys
from stino import utils

if sys.platform == 'win32':
	import _winreg

def isArduinoFolder(path):
	state = False
	if path and os.path.exists(path):
		hardware_path = os.path.join(path, 'hardware')
		lib_path = os.path.join(path, 'lib')
		if os.path.isdir(hardware_path) and os.path.isdir(lib_path):
			state = True

	if state:
		lib_path = os.path.join(path, 'lib')
		ver_file = os.path.join(lib_path, 'version.txt')
		if not os.path.isfile(ver_file):
			state = False
	return state

def isCoreFolder(path):
	state = False
	if os.path.exists(path):
		variants_path = os.path.join(path, 'variants')
		boards_file = os.path.join(path, 'boards.txt')
		if os.path.isdir(variants_path) and os.path.isfile(boards_file):
			state = True
	return state

def isSketchFolder(path):
	state = False
	cur_dir = os.path.split(path)[1]
	sketch_name = '%s.ino' % cur_dir
	ino_sketch_path = os.path.join(path, sketch_name)
	sketch_name = '%s.pde' % cur_dir
	pde_sketch_path = os.path.join(path, sketch_name)
	if os.path.isfile(ino_sketch_path) or os.path.isfile(pde_sketch_path):
		state = True
	return state

def getSketchList(path):
	sketch_list = []
	sketch_file_dict = {}
	if os.path.isdir(path):
		dirs = utils.listDir(path, with_files = False)
		for cur_dir in dirs:
			cur_dir_path = os.path.join(path, cur_dir)
			if isSketchFolder(cur_dir_path):
				sketch_list.append(cur_dir)
				sketch_file_dict[cur_dir] = cur_dir_path
	return (sketch_list, sketch_file_dict)

def getLibList(path):
	lib_list = []
	lib_file_dict = {}
	lib_root = os.path.join(path, 'libraries')
	if os.path.isdir(lib_root):
		dirs = utils.listDir(lib_root, with_files = False)
		for cur_dir in dirs:
			cur_dir_path = os.path.join(lib_root, cur_dir)
			lib_list.append(cur_dir)
			lib_file_dict[cur_dir] = cur_dir_path
	return (lib_list, lib_file_dict)

def getExampleList(path):
	example_list = []
	example_file_dict = {}
	example_root = os.path.join(path, 'examples')
	if os.path.isdir(example_root):
		dirs = utils.listDir(example_root, with_files = False)
		for cur_dir in dirs:
			cur_dir_path = os.path.join(example_root, cur_dir)
			example_list.append(cur_dir)
			example_file_dict[cur_dir] = cur_dir_path
	return (example_list, example_file_dict)

def getLibExampleList(path):
	example_list = []
	example_file_dict = {}
	lib_root = os.path.join(path, 'libraries')
	if os.path.isdir(lib_root):
		dirs = utils.listDir(lib_root, with_files = False)
		for cur_dir in dirs:
			cur_dir_path = os.path.join(lib_root, cur_dir)
			example_dir_path = os.path.join(cur_dir_path, 'examples')
			if os.path.isdir(example_dir_path):
				example_list.append(cur_dir)
				example_file_dict[cur_dir] = example_dir_path
	return (example_list, example_file_dict)

def getProgrammerList(path):
	programmer_list = []
	programmer_file_dict = {}
	info_file = os.path.join(path, 'programmers.txt')
	if os.path.isfile(info_file):
		blocks = utils.readFile(info_file, mode = 'blocks')
		for block in blocks:
			if block:
				line = block[0]
				(key, value) = utils.getKeyValue(line)
				programmer_list.append(value)
				programmer_file_dict[value] = info_file
	return (programmer_list, programmer_file_dict)

def getPlatform(path):
	platform = 'Arduino AVR Boards'
	info_file = os.path.join(path, 'platform.txt')
	if os.path.isfile(info_file):
		lines = utils.readFile(info_file, mode = 'lines')
		for line in lines:
			(key, value) = utils.getKeyValue(line)
			if key == 'name':
				platform = value
				break
	return platform

def getBoardList(path):
	board_list = []
	board_file_dict = {}
	processors_of_board = {}
	info_file = os.path.join(path, 'boards.txt')
	if os.path.isfile(info_file):
		blocks = utils.readFile(info_file, mode = 'blocks')
		for block in blocks:
			if block:
				line = block[0]
				(key, board) = utils.getKeyValue(line)
				board_list.append(board)

				processor_list = []
				processor_blocks = utils.getBlocks(block, sep = '## ')
				for processor_block in processor_blocks:
					if processor_block:
						processor_line = processor_block[0]
						(key, processor) = utils.getKeyValue(processor_line)
						processor_list.append(processor)
				processors_of_board[board] = processor_list
				board_file_dict[board] = info_file
	return (board_list, board_file_dict, processors_of_board)

def getKeywordList(path):
	keyword_list = []
	keyword_type_dict = {}
	keyword_ref_dict = {}
	keyword_file = os.path.join(path, 'keywords.txt')
	if os.path.isfile(keyword_file):
		lines = utils.readFile(keyword_file, mode = 'lines')
		for line in lines:
			line = line.strip()
			if line and (not '#' in line):
				line = line.replace('\t', ' ')
				word_list = line.split(' ')
				while len(word_list) < 3:
					word_list.append('')
				keyword = word_list[0]
				keyword_list.append(keyword)
				if 'KEYWORD' in word_list[2]:
					keyword_type_dict[keyword] = word_list[2]
					keyword_ref_dict[keyword] = ''
				else:
					keyword_type_dict[keyword] = word_list[1]
					keyword_ref_dict[keyword] = word_list[2]
				if ('{}' in keyword) or ('[]' in keyword) or ('()' in keyword):
					for letter in keyword:
						keyword_list.append(letter)
						keyword_type_dict[letter] = keyword_type_dict[keyword]
						keyword_ref_dict[letter] = keyword_ref_dict[keyword]
	return (keyword_list, keyword_type_dict, keyword_ref_dict)

def genVersion(arduino_root):
	version_txt = 'unknown'
	version = 0
	lib_dir = os.path.join(arduino_root, 'lib')
	if os.path.isdir(lib_dir):
		version_file_path = os.path.join(lib_dir, 'version.txt')
		if os.path.isfile(version_file_path):
			f = open(version_file_path, 'r')
			version_txt = f.readlines()[0].strip()
			f.close()

			if not '.' in version_txt:
				version = int(version_txt)
			else:
				number_list = version_txt.split('.')
				power = 0
				for number in number_list:
					for n in number:
						if not (n in '0123456789'):
							index = number.index(n)
							number = number[:index]
							break
					number = int(number)
					version += number * (10 ** power)
					power -= 1
				version *= 100
	return (version_txt, version)

class ArduinoInfo:
	def __init__(self):
		self.Settings = sublime.load_settings('Stino.sublime-settings')
		self.sketchbook_root = self.Settings.get('sketchbook_root')
		if not (self.sketchbook_root and os.path.isdir(self.sketchbook_root)):
			self.getDefaultSketchbookFolder()
		self.core_folder_list = []
		self.platform_list = []
		self.platform_file_dict = {}
		self.platform_folder_dict = {}
		self.platform_board_dict = {}
		self.board_file_dict = {}
		self.processors_of_board = {}
		self.board_platform_dict = {}
		self.sketch_list = []
		self.sketch_file_dict = {}
		self.lib_list = []
		self.lib_file_dict = {}
		self.programmer_list = []
		self.programmer_file_dict = {}
		self.example_list = []
		self.example_file_dict = {}
		self.version_txt = 'unknown'
		self.version = 0
		self.update()

	def update(self):
		self.arduino_root = self.Settings.get('Arduino_root')
		if not isArduinoFolder(self.arduino_root):
			return
		(self.version_txt, self.version) = genVersion(self.arduino_root)
		self.sketchbookUpdate()
		self.genBoardList()
		self.boardUpdate()
		
	def sketchbookUpdate(self):
		self.sketchbook_root = self.Settings.get('sketchbook_root')
		if not (self.sketchbook_root and os.path.isdir(self.sketchbook_root)):
			self.getDefaultSketchbookFolder()
		lib_path = os.path.join(self.sketchbook_root, 'libraries')
		if not os.path.exists(lib_path):
			os.mkdir(lib_path)
		hardware_path = os.path.join(self.sketchbook_root, 'hardware')
		if not os.path.exists(hardware_path):
			os.mkdir(hardware_path)
		self.genSketchList()

	def boardUpdate(self):
		self.board = self.Settings.get('board')
		if not self.isBoard(self.board):
			self.board = self.getDefaultBoard()
			self.Settings.set('board', self.board)
			sublime.save_settings('Stino.sublime-settings')
		self.genLibList()
		self.genProgrammerList()
		self.genExampleList()
		self.genKeywordList()

	def getDefaultSketchbookFolder(self):
		if sys.platform == 'win32':
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,\
	            	r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
			doc_path = _winreg.QueryValueEx(key, 'Personal')[0]
			sketchbook_root = os.path.join(doc_path, 'Arduino')
		elif sys.platform == 'darwin':
			home_path = os.getenv('HOME')
			doc_path = os.path.join(home_path, 'Documents')
			sketchbook_root = os.path.join(doc_path, 'Arduino')
		else:
			home_path = os.getenv('HOME')
			sketchbook_root = os.path.join(home_path, 'sketchbook')
		if not os.path.exists(sketchbook_root):
			os.mkdir(sketchbook_root)
		self.sketchbook_root = sketchbook_root

	def genCoreFolderList(self):
		core_folder_list = []
		hardware_path_list = [os.path.join(self.arduino_root, 'hardware')]
		hardware_path_list.append(os.path.join(self.sketchbook_root, 'hardware'))
		for hardware_path in hardware_path_list:
			if os.path.isdir(hardware_path):
				dirs = utils.listDir(hardware_path, with_files = False)
				for cur_dir in dirs:
					if 'tools' in cur_dir:
						continue
					cur_dir_path = os.path.join(hardware_path, cur_dir)
					if isCoreFolder(cur_dir_path):
						core_folder_list.append(cur_dir_path)
					else:
						subdirs = utils.listDir(cur_dir_path, with_files = False)
						for cur_subdir in subdirs:
							cur_subdir_path = os.path.join(cur_dir_path, cur_subdir)
							if isCoreFolder(cur_subdir_path):
								core_folder_list.append(cur_subdir_path)
		self.core_folder_list = core_folder_list

	def genPlatformList(self):
		self.genCoreFolderList()
		self.platform_list = []
		self.platform_folder_dict = {}
		for core_folder in self.core_folder_list:
			platform = getPlatform(core_folder).decode('utf-8', 'replace')
			if not platform in self.platform_folder_dict:
				self.platform_folder_dict[platform] = [core_folder]
				self.platform_list.append(platform)
				self.platform_file_dict[platform] = core_folder
			else:
				self.platform_folder_dict[platform].append(core_folder)
		self.platform_list.sort(key = unicode.lower)
	
	def genBoardList(self):
		self.genPlatformList()
		self.platform_board_dict = {}
		self.board_file_dict = {}
		self.processors_of_board = {}
		self.board_platform_dict = {}
		for platform in self.platform_folder_dict:
			self.platform_board_dict[platform] = []
			for core_folder in self.platform_folder_dict[platform]:
				(board_list, board_file_dict, processors_of_board) = getBoardList(core_folder)
				for board in board_list:
					self.board_platform_dict[board] = platform
				self.platform_board_dict[platform].append(board_list)
				self.board_file_dict = dict(self.board_file_dict, **board_file_dict)
				self.processors_of_board = dict(self.processors_of_board, **processors_of_board)
			self.platform_board_dict[platform] = utils.removeEmptyItem(self.platform_board_dict[platform])

	def genSketchList(self):
		self.sketch_list = []
		self.sketch_file_dict = {}
		(sketch_list, sketch_file_dict) = getSketchList(self.sketchbook_root)
		self.sketch_list.append(sketch_list)
		self.sketch_file_dict = dict(self.sketch_file_dict, **sketch_file_dict)

	def getLibFolderList(self):
		platform = self.getPlatform(self.board)
		core_folder_list = self.getPlatformFolderList(platform)

		lib_folder_list = [self.arduino_root, self.sketchbook_root]
		lib_folder_list += core_folder_list
		return lib_folder_list

	def genLibList(self):
		self.lib_list = []
		self.lib_file_dict = {}

		lib_folder_list = self.getLibFolderList()
		for lib_folder in lib_folder_list:
			(lib_list, lib_file_dict) = getLibList(lib_folder)
			self.lib_list.append(lib_list)
			self.lib_file_dict = dict(self.lib_file_dict, **lib_file_dict)
		self.lib_list = utils.removeEmptyItem(self.lib_list)

	def genProgrammerList(self):
		self.programmer_list = []
		self.programmer_file_dict = {}

		platform = self.getPlatform(self.board)
		core_folder_list = self.getPlatformFolderList(platform)
		
		for core_folder in core_folder_list:
			(programmer_list, programmer_file_dict) = getProgrammerList(core_folder)
			self.programmer_list.append(programmer_list)
			self.programmer_file_dict = dict(self.programmer_file_dict, **programmer_file_dict)
		self.programmer_list = utils.removeEmptyItem(self.programmer_list)

	def genExampleList(self):
		self.example_list = []
		self.example_file_dict = {}

		folder_list = [self.arduino_root, self.sketchbook_root]
		lib_folder_list = self.getLibFolderList()

		for folder in folder_list:
			(example_list, example_file_dict) = getExampleList(folder)
			self.example_list.append(example_list)
			self.example_file_dict = dict(self.example_file_dict, **example_file_dict)

		for folder in lib_folder_list:
			(example_list, example_file_dict) = getLibExampleList(folder)
			self.example_list.append(example_list)
			self.example_file_dict = dict(self.example_file_dict, **example_file_dict)

	def genKeywordList(self):
		self.keyword_list = []
		self.keyword_type_dict = {}
		self.keyword_ref_dict = {}

		path_list = [os.path.join(self.arduino_root, 'lib')]
		lib_list = self.getLibList()
		for libs in lib_list:
			for lib in libs:
				path = self.lib_file_dict[lib]
				path_list.append(path)
		for path in path_list:
			(keyword_list, keyword_type_dict, keyword_ref_dict) = getKeywordList(path)
			self.keyword_list += keyword_list
			self.keyword_type_dict = dict(self.keyword_type_dict, **keyword_type_dict)
			self.keyword_ref_dict = dict(self.keyword_ref_dict, **keyword_ref_dict)

	def getPlatformList(self):
		return self.platform_list

	def getPlatformFolderList(self, platform):
		return self.platform_folder_dict[platform]

	def getPlatformFileFolder(self, platform):
		return self.platform_file_dict[platform]

	def getBoardList(self, platform):
		return self.platform_board_dict[platform]

	def getDefaultPlatform(self):
		return 'Arduino AVR Boards'

	def getDefaultBoard(self):
		platform = self.getDefaultPlatform()
		board_list = self.getBoardList(platform)
		board = board_list[0][0]
		return board

	def isBoard(self, board):
		state = False
		if board:
			platform_list = self.getPlatformList()
			for platform in platform_list:
				board_list = self.getBoardList(platform)
				for boards in board_list:
					if board in boards:
						state = True
		return state

	def getPlatform(self, board):
		return self.board_platform_dict[board]

	def getBoardFile(self, board):
		return self.board_file_dict[board]

	def getProcessorList(self, board = ''):
		if not board:
			board = self.board
		return self.processors_of_board[board]

	def getSketchList(self):
		return self.sketch_list

	def getSketchFolder(self, sketch):
		return self.sketch_file_dict[sketch]

	def getProgrammerList(self):
		return self.programmer_list

	def getProgrammerFile(self, programmer):
		return self.programmer_file_dict[programmer]

	def getLibList(self):
		return self.lib_list

	def getLibFolder(self, lib):
		return self.lib_file_dict[lib]

	def getExampleList(self):
		return self.example_list

	def getExampleFolder(self, example):
		return self.example_file_dict[example]

	def getSketchbookRoot(self):
		return self.sketchbook_root

	def getVersion(self):
		return self.version

	def getVersionText(self):
		return self.version_txt

	def hasProcessor(self, board):
		has_processor = False
		processor_list = self.getProcessorList(board)
		if processor_list:
			has_processor = True
		return has_processor

	def hasProgrammer(self):
		has_programmer = False
		programmer_list = self.getProgrammerList()
		for programmers in programmer_list:
			if programmers:
				has_programmer = True
		return has_programmer

	def getKeywordList(self):
		return self.keyword_list

	def getKeywordType(self, keyword):
		if keyword in self.keyword_list:
			t = self.keyword_type_dict[keyword]
		else:
			t = ''
		return t

	def getKeywordRef(self, keyword):
		if keyword in self.keyword_list:
			ref = self.keyword_ref_dict[keyword]
		else:
			ref = ''
		return ref
	