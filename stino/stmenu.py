#-*- coding: utf-8 -*-
# stino/stmenu.py

import os

from stino import utils
from stino import const
from stino import osfile
from stino import smonitor

def replaceMenuCaption(menu_caption):
	menu_caption = menu_caption.replace('Boards', '%(Board)s')
	menu_caption = menu_caption.replace('Processor', '%(Processor)s')
	menu_caption = menu_caption.replace('Type', '%(Type)s')
	menu_caption = menu_caption.replace('Speed', '%(Speed)s')
	menu_caption = menu_caption.replace('Keyboard Layout', '%(Keyboard_Layout)s')
	return menu_caption

class STMenu:
	def __init__(self, language, arduino_info):
		self.language = language
		self.arduino_info = arduino_info

		self.plugin_root = const.plugin_root
		self.template_root = const.template_root

		self.main_menu_file = os.path.join(self.plugin_root, 'Main.sublime-menu')
		self.commands_file = os.path.join(self.plugin_root, 'Stino.sublime-commands')
		self.completions_file = os.path.join(self.plugin_root, 'Stino.sublime-completions')
		self.syntax_file = os.path.join(self.plugin_root, 'Arduino.tmLanguage')

		self.original_menu_text = ''
		self.full_menu_text = ''
		self.commands_text = ''
		self.completions_text = ''
		self.syntax_text = ''
		self.fullUpdate()

	def commandUpdate(self):
		self.genCommandsText()
		self.writeCommandsFile()

	def update(self):
		self.genOriginalMenuText()
		self.genFullMenuText()
		self.writeMainMenuFile()
		self.commandUpdate()
		
	def fullUpdate(self):
		self.update()
		self.genCompletionsText()
		self.writeCompletionsFile()
		self.genSyntaxText()
		self.writeSyntaxFile()

	def languageUpdate(self):
		self.writeMainMenuFile()
		self.writeCommandsFile()
		self.writeCompletionsFile()
		self.writeSyntaxFile()

	def genOriginalMenuText(self):
		show_arduino_menu = const.settings.get('show_arduino_menu')
		show_serial_monitor_menu = const.settings.get('show_serial_monitor_menu')

		preference_menu_file = os.path.join(self.template_root, 'menu_preference')
		serial_monitor_menu_file = os.path.join(self.template_root, 'menu_serial')
		menu_text = osfile.readFileText(preference_menu_file)

		if show_arduino_menu:
			if self.arduino_info.isReady():
				arduino_menu_file_name = 'menu_full'
			else:
				arduino_menu_file_name = 'menu_mini'
			arduino_menu_file = os.path.join(self.template_root, arduino_menu_file_name)
			menu_text += ',\n'
			menu_text += osfile.readFileText(arduino_menu_file)

		if show_serial_monitor_menu:
			menu_text += ',\n'
			menu_text += osfile.readFileText(serial_monitor_menu_file)

		menu_text += '\n]'
		self.original_menu_text = menu_text

	def genSubMenuBlock(self, menu_caption, item_lists, command, menu_base = None, checkbox = False):
		submenu_text = '{"caption": "%s", "command": "not_enabled"},' % menu_caption
		if item_lists:
			submenu_text = ''
			submenu_text += '{\n'
			submenu_text += '\t'*4
			submenu_text += '"caption": "%s",\n' % menu_caption
			submenu_text += '\t'*4
			submenu_text += '"id": "%s",\n' % command
			submenu_text += '\t'*4
			submenu_text += '"children":\n'
			submenu_text += '\t'*4
			submenu_text += '[\n'
			for item_list in item_lists:
				for item in item_list:
					if menu_base:
						menu_str = utils.genKey(item, menu_base)
					else:
						menu_str = item
					submenu_text += '\t'*5
					submenu_text += '{"caption": "%s", "command": "%s", "args": {"menu_str": "%s"}' \
						% (item, command, menu_str)
					if checkbox:
						submenu_text += ', "checkbox": true'
					submenu_text += '},\n'
				submenu_text += '\t'*5
				submenu_text += '{"caption": "-"},\n'
			submenu_text = submenu_text[:-2] + '\n'
			submenu_text += '\t'*4
			submenu_text += ']\n'
			submenu_text += '\t'*3
			submenu_text += '},\n'
		return submenu_text

	def genDictBlock(self, info_list, description):
		dict_text = ''
		if info_list:
			dict_text += '\t' * 2
			dict_text += '<dict>\n'
			dict_text += '\t' * 3
			dict_text += '<key>match</key>\n'
			dict_text += '\t' * 3
			dict_text += '<string>\\b('
			for item in info_list:
				dict_text += item
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
			dict_text += '</dict>'
		return dict_text

	def genSketchbookMenuText(self):
		sketch_list = self.arduino_info.getSketchList()
		menu_caption = '%(Sketchbook)s'
		command = 'open_sketch'
		menu_text = self.genSubMenuBlock(menu_caption, [sketch_list], command)
		return menu_text

	def genLibraryMenuText(self):
		platform = self.getPlatform()
		library_lists = self.arduino_info.getLibraryLists(platform)
		menu_caption = '%(Import_Library...)s'
		command = 'import_library'
		menu_text = self.genSubMenuBlock(menu_caption, library_lists, command, menu_base = platform)
		return menu_text

	def genBoardMenuText(self):
		menu_text = ''
		command = 'select_board'
		platform_list = self.arduino_info.getPlatformList()
		for platform in platform_list:
			board_lists = self.arduino_info.getBoardLists(platform)
			menu_caption = replaceMenuCaption(platform)
			menu_text += self.genSubMenuBlock(menu_caption, board_lists, command, menu_base = platform, checkbox = True)
		return menu_text

	def genBoardOptionMenuText(self):
		menu_text = ''
		command = 'select_board_type'
		platform = self.getPlatform()
		board = self.getBoard()
		board_type_list = self.arduino_info.getBoardTypeList(platform, board)
		for board_type in board_type_list:
			item_list = self.arduino_info.getBoardItemList(platform, board, board_type)
			type_caption = self.arduino_info.getPlatformTypeCaption(platform, board_type)
			menu_caption = replaceMenuCaption(type_caption)
			board_key = utils.genKey(board, platform)
			type_key = utils.genKey(board_type, board_key)
			menu_text += self.genSubMenuBlock(menu_caption, [item_list], command, menu_base = type_key, checkbox = True)

			type_value = const.settings.get(type_caption)
			if not type_value in item_list:
				type_value = item_list[0]
				const.settings.set(type_caption, type_value)
		return menu_text

	def genSerialMenuText(self):
		serial_port_list = smonitor.genSerialPortList()
		menu_caption = '%(Serial_Port)s'
		command = 'select_serial_port'
		serial_port_lists = []
		if serial_port_list:
			serial_port_lists.append(serial_port_list)
		menu_text = self.genSubMenuBlock(menu_caption, serial_port_lists, command, checkbox = True)
		serial_port = const.settings.get('serial_port')
		if not serial_port in serial_port_list:
			if serial_port_list:
				serial_port = serial_port_list[0]
			else:
				serial_port = ''
			const.settings.set('serial_port', serial_port)
		return menu_text

	def genBaudrateMenuText(self):
		baudrate_list = smonitor.getBaudrateList()
		menu_caption = '%(Baudrate)s'
		command = 'select_baudrate'
		menu_text = self.genSubMenuBlock(menu_caption, [baudrate_list], command, checkbox = True)
		baudrate = const.settings.get('baudrate')
		if not baudrate in baudrate_list:
			baudrate = '9600'
			const.settings.set('baudrate', baudrate)
		return menu_text

	def genProgrammerMenuText(self):
		platform = self.getPlatform()
		programmer_lists = self.arduino_info.getProgrammerLists(platform)
		menu_caption = '%(Programmer)s'
		command = 'select_programmer'
		menu_text = self.genSubMenuBlock(menu_caption, programmer_lists, command, menu_base = platform, checkbox = True)
		if programmer_lists:
			all_programer_list = utils.simplifyLists(programmer_lists)
			programmer = const.settings.get('programmer')
			if not programmer in all_programer_list:
				programmer = all_programer_list[0]
				const.settings.set('programmer', programmer)
		else:
			const.settings.set('programmer', '')
		return menu_text

	def genLanguageMenuText(self):
		language_list = self.language.getLanguageTextList()
		menu_caption = '%(Language)s'
		command = 'select_language'
		menu_text = self.genSubMenuBlock(menu_caption, [language_list], command, checkbox = True)
		return menu_text

	def genExampleMenuText(self):
		platform = self.getPlatform()
		example_lists = self.arduino_info.getExampleLists(platform)
		menu_caption = '%(Examples)s'
		command = 'select_example'
		menu_text = self.genSubMenuBlock(menu_caption, example_lists, command, menu_base = platform)
		return menu_text

	def genFullMenuText(self):
		self.full_menu_text = self.getOriginMenuText()

		language_menu_text = self.genLanguageMenuText()
		serial_menu_text = self.genSerialMenuText()
		baudrate_menu_text = self.genBaudrateMenuText()
		sketchbook_menu_text = self.genSketchbookMenuText()

		self.full_menu_text = self.full_menu_text.replace('{"caption": "Sketchbook->"},', sketchbook_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Serial_Port->"},', serial_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Baudrate->"},', baudrate_menu_text)
		self.full_menu_text = self.full_menu_text.replace('{"caption": "Language->"},', language_menu_text)

		if self.arduino_info.isReady():
			library_menu_text = self.genLibraryMenuText()
			board_menu_text = self.genBoardMenuText()
			board_option_menu_text = self.genBoardOptionMenuText()
			programmer_menu_text = self.genProgrammerMenuText()
			example_menu_text = self.genExampleMenuText()

			self.full_menu_text = self.full_menu_text.replace('{"caption": "Import_Library->"},', library_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Board->"},', board_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Board_Option->"},', board_option_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Programmer->"},', programmer_menu_text)
			self.full_menu_text = self.full_menu_text.replace('{"caption": "Examples->"},', example_menu_text)

	def writeMainMenuFile(self):
		menu_text = self.getFullMneuText() % self.language.getTransDict()
		osfile.writeFile(self.main_menu_file, menu_text)

	def genSelectItemText(self, caption, command, parent_mod, list_func, parameter1 = '', parameter2 = '', parameter3 = ''):
		command_text = '    { "caption": "Stino: %s", "command": "select_item", "args": {"command": "%s", "parent_mod": "%s", "list_func": "%s", "parameter1": "%s", "parameter2": "%s", "parameter3": "%s"}},\n' \
			% (caption, command, parent_mod, list_func, parameter1, parameter2, parameter3)
		return command_text

	def genOpenSketchCommandText(self):
		command_text = ''
		sketch_list = self.arduino_info.getSketchList()
		if sketch_list:
			command_caption = '%(Open)s %(Sketch)s'
			command = 'open_sketch'
			parent_mod = 'arduino_info'
			list_func = 'getSketchList'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func)
		return command_text

	def genImportLibraryCommandText(self):
		command_text = ''
		platform = self.getPlatform()
		library_lists = self.arduino_info.getLibraryLists(platform)
		if library_lists:
			command_caption = '%(Import_Library...)s'
			command = 'import_library'
			parent_mod = 'arduino_info'
			list_func = 'getLibraryLists'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func, parameter1 = platform)
		return command_text

	def genSelectBoardCommandText(self):
		command_text = ''
		command = 'select_board'
		parent_mod = 'arduino_info'
		list_func = 'getBoardLists'
		platform_list = self.arduino_info.getPlatformList()
		for platform in platform_list:
			command_caption = '%(Select)s ' + replaceMenuCaption(platform)
			command_text += self.genSelectItemText(command_caption, command, parent_mod, list_func, parameter1 = platform)
		return command_text

	def genSelectBoardTypeCommandText(self):
		command_text = ''
		command = 'select_board_type'
		parent_mod = 'arduino_info'
		list_func = 'getBoardItemList'

		platform = self.getPlatform()
		board = self.getBoard()
		board_type_list = self.arduino_info.getBoardTypeList(platform, board)
		for board_type in board_type_list:
			board_type_caption = self.arduino_info.getPlatformTypeCaption(platform, board_type)
			board_type_caption = replaceMenuCaption(board_type_caption)
			command_caption = '%(Select)s ' + board_type_caption
			command_text += self.genSelectItemText(command_caption, command, parent_mod, list_func, parameter1 = platform, parameter2 = board, parameter3 = board_type)
		return command_text

	def genSelectSerialPortCommandText(self):
		command_text = ''
		serial_port_list = smonitor.genSerialPortList()
		if serial_port_list:
			command_caption = '%(Select)s ' + '%(Serial_Port)s'
			command = 'select_serial_port'
			parent_mod = 'smonitor'
			list_func = 'genSerialPortList'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func)
		return command_text

	def genSelectBaudrateCommandText(self):
		command_caption = '%(Select)s ' + '%(Baudrate)s'
		command = 'select_baudrate'
		parent_mod = 'smonitor'
		list_func = 'getBaudrateList'
		command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func)
		return command_text

	def genSelectProgrammerCommandText(self):
		command_text = ''
		platform = self.getPlatform()
		programmer_lists = self.arduino_info.getProgrammerLists(platform)
		if programmer_lists:
			command_caption = '%(Select)s ' + '%(Programmer)s'
			command = 'select_programmer'
			parent_mod = 'arduino_info'
			list_func = 'getProgrammerLists'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func, parameter1 = platform)
		return command_text

	def genSelectLanguageCommandText(self):
		command_text = ''
		language_list = self.language.getLanguageTextList()
		if language_list:
			command_caption = '%(Select)s ' + '%(Language)s'
			command = 'select_language'
			parent_mod = 'cur_language'
			list_func = 'getLanguageTextList'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func)
		return command_text

	def genSelectExampleCommandText(self):
		command_text = ''
		platform = self.getPlatform()
		example_lists = self.arduino_info.getExampleLists(platform)
		if example_lists:
			command_caption = '%(Open)s ' + '%(Examples)s'
			command = 'select_example'
			parent_mod = 'arduino_info'
			list_func = 'getExampleLists'
			command_text = self.genSelectItemText(command_caption, command, parent_mod, list_func, parameter1 = platform)
		return command_text

	def genToggleCommandText(self, caption, setting_text):
		state = const.settings.get(setting_text)
		if state:
			state_text = '%(OFF)s'
		else:
			state_text = '%(ON)s'
		command = 'toggle_' + setting_text
		command_caption = '%(Toggle)s ' + caption
		command_text = '	{ "caption": "Stino: %s %s", "command": "%s" },\n' % (command_caption, state_text, command)
		return command_text

	def genSelectCommandsText(self):
		text = self.genOpenSketchCommandText()
		text += self.genImportLibraryCommandText()
		text += self.genSelectBoardCommandText()
		text += self.genSelectBoardTypeCommandText()
		text += self.genSelectSerialPortCommandText()
		text += self.genSelectBaudrateCommandText()
		text += self.genSelectProgrammerCommandText()
		text += self.genSelectLanguageCommandText()
		text += self.genSelectExampleCommandText()
		text += self.genToggleCommandText('%(Full_Compilation)s', 'full_compilation')
		text += self.genToggleCommandText('%(Show_Verbose_Output)s-%(Compilation)s', 'verbose_compilation')
		text += self.genToggleCommandText('%(Show_Verbose_Output)s-%(Upload)s', 'verbose_upload')
		text += self.genToggleCommandText('%(Verify_code_after_upload)s', 'verify_code')
		return text

	def genCommandsText(self):
		temp_filename = 'commands_mini'
		if self.arduino_info.isReady():
			show_arduino_menu = const.settings.get('show_arduino_menu')
			if show_arduino_menu:
				temp_filename = 'commands_full'
			
		temp_file_path = os.path.join(self.template_root, temp_filename)
		temp_file_text = osfile.readFileText(temp_file_path)

		if temp_filename == 'commands_full':
			select_commands_text = self.genSelectCommandsText()
			temp_file_text = temp_file_text.replace('(_$item$_)', select_commands_text)
		self.commands_text = temp_file_text

	def writeCommandsFile(self):
		commands_text = self.getCommandsText() % self.language.getTransDict()
		osfile.writeFile(self.commands_file, commands_text)

	def genCompletionsText(self):
		self.completions_text = '{\n'
		self.completions_text += '\t"scope": "source.arduino",\n'
		self.completions_text += '\t"completions":\n'
		self.completions_text += '\t[\n'
		if self.arduino_info.isReady():
			platform = self.getPlatform()
			for keyword in self.arduino_info.getKeywordList(platform):
				if self.arduino_info.getKeywordType(platform, keyword):
					self.completions_text += '\t\t"%s",\n' % keyword
			self.completions_text = self.completions_text[:-2] + '\n'
		self.completions_text += '\t]\n'
		self.completions_text += '}'

	def writeCompletionsFile(self):
		completions_text = self.getCompletionsText() % self.language.getTransDict()
		osfile.writeFile(self.completions_file, completions_text)

	def genSyntaxText(self):
		constant_list = []
		keyword_list = []
		function_list = []
		if self.arduino_info.isReady():
			platform = self.getPlatform()
			for keyword in self.arduino_info.getKeywordList(platform):
				if len(keyword) > 1:
					keyword_type = self.arduino_info.getKeywordType(platform, keyword)
					if keyword_type:
						if 'LITERAL' in keyword_type:
							constant_list.append(keyword)
						elif keyword_type == 'KEYWORD1':
							keyword_list.append(keyword)
						else:
							function_list.append(keyword)

		text = ''
		text += self.genDictBlock(constant_list, 'constant.arduino')
		text += self.genDictBlock(keyword_list, 'keyword.arduino')
		text += self.genDictBlock(function_list, 'entity.name.function.arduino')

		temp_file = os.path.join(self.template_root, 'syntax')
		self.syntax_text = osfile.readFileText(temp_file)
		self.syntax_text = self.syntax_text.replace('(_$dict$_)', text)

	def writeSyntaxFile(self):
		syntax_text = self.getSyntaxText() % self.language.getTransDict()
		osfile.writeFile(self.syntax_file, syntax_text)

	def getPlatform(self):
		platform = const.settings.get('platform')
		platform_list = self.arduino_info.getPlatformList()
		if not platform in platform_list:
			platform = platform_list[0]
			const.settings.set('platform', platform)
		return platform

	def getBoard(self):
		board = const.settings.get('board')
		platform = self.getPlatform()
		board_lists = self.arduino_info.getBoardLists(platform)
		all_board_list = utils.simplifyLists(board_lists)
		if not board in all_board_list:
			board = all_board_list[0]
			const.settings.set('board', board)
		return board

	def getOriginMenuText(self):
		if not self.original_menu_text:
			self.genOriginalMenuText()
		return self.original_menu_text

	def getFullMneuText(self):
		if not self.full_menu_text:
			self.genFullMenuText()
		return self.full_menu_text

	def getCommandsText(self):
		if not self.commands_text:
			self.genCommandsText()
		return self.commands_text

	def getCompletionsText(self):
		if not self.completions_text:
			self.genCompletionsText()
		return self.completions_text

	def getSyntaxText(self):
		if not self.syntax_text:
			self.genSyntaxText()
		return self.syntax_text