#-*- coding: utf-8 -*-
import sublime
import os
from stino import utils, arduino

class STMenu:
	def __init__(self, arduino_info, lang):
		self.Settings = sublime.load_settings('Stino.sublime-settings')
		self.arduino_info = arduino_info
		self.lang = lang
		self.display_text_dict = lang.getDisplayTextDict()
		self.plugin_root = utils.getPluginRoot()

		self.sketchbook_menu_text = ''
		self.import_lib_menu_text = ''
		self.board_menu_text = ''
		self.processor_menu_text = ''
		self.usb_type_menu_text = ''
		self.keyboard_layout_menu_text = ''
		self.serial_port_menu_text = ''
		self.programmer_menu_text = ''
		self.lang_menu_text = ''
		self.examples_menu_text = ''

		self.file = os.path.join(self.plugin_root, 'Main.sublime-menu')
		self.commands_file = os.path.join(self.plugin_root, 'Stino.sublime-commands')
		self.completions_file = os.path.join(self.plugin_root, 'Stino.sublime-completions')
		self.syntax_file = os.path.join(self.plugin_root, 'Arduino.tmLanguage')
		self.template_dir = os.path.join(self.plugin_root, 'template')
		self.update()		

	def update(self):
		arduino_root = self.Settings.get('Arduino_root')
		if arduino.isArduinoFolder(arduino_root):
			self.fullUpdate()
		else:
			self.miniUpdate()

	def miniUpdate(self):
		self.genOriginalMenuText()
		self.genLangMenuText()
		self.genFullMenuText()
		self.genFile(self.display_text_dict)
		self.genCompletionsFile(mode = 'mini')
		self.genSyntexFile(mode = 'mini')
	
	def fullUpdate(self):
		self.arduino_info.update()
		self.genOriginalMenuText()
		self.genSketchbookMenuText()
		self.genImportLibMenuText()
		self.genBoardMenuText()
		self.genProcessorMenuText()
		self.genUSBTypeMenuText()
		self.genKeyboardLayoutMenuText()
		self.genSerialPortMenuText()
		self.genProgrammerMenuText()
		self.genLangMenuText()
		self.genExampleMenuText()
		self.genFullMenuText()
		self.genFile(self.display_text_dict)
		self.genCompletionsFile()
		self.genSyntexFile()

	def sketchbookUpdate(self):
		self.arduino_info.sketchbookUpdate()
		self.genSketchbookMenuText()
		self.genFullMenuText()
		self.genFile(self.display_text_dict)
		self.genCompletionsFile()
		self.genSyntexFile()

	def serialUpdate(self):
		self.genSerialPortMenuText()
		self.genFullMenuText()
		self.genFile(self.display_text_dict)

	def boardUpdate(self):
		self.arduino_info.boardUpdate()
		self.genImportLibMenuText()
		self.genProcessorMenuText()
		self.genUSBTypeMenuText()
		self.genKeyboardLayoutMenuText()
		self.genProgrammerMenuText()
		self.genExampleMenuText()
		self.genFullMenuText()
		self.genFile(self.display_text_dict)
		self.genCompletionsFile()
		self.genSyntexFile()

	def getMenuText(self, itemlist, caption, command, checkbox = False):
		if command == 'select_board' or command == 'select_processor' or command == 'select_usb_type' or command == 'select_keyboard_layout':
			cmd_text = 'no_item'
		else:
			cmd_text = 'not_enable'
		text = '{"caption": "%s", "command": "%s"},' % (caption, cmd_text)

		has_submenu = False
		for sublist in itemlist:
			if len(sublist) > 0:
				has_submenu = True
		
		if has_submenu:
			text = ''
			text += '{\n'
			text += '\t'*4
			text += '"caption": "%s",\n' % caption
			text += '\t'*4
			text += '"id": "%s",\n' % command
			text += '\t'*4
			text += '"children":\n'
			text += '\t'*4
			text += '[\n'
			for sublist in itemlist:
				for item in sublist:
					text += '\t'*5
					text += '{"caption": "%s", "command": "%s", "args": {"menu_str": "%s"}' % (item, command, item)
					if checkbox:
						text += ', "checkbox": true'
					text += '},\n'
				text += '\t'*5
				text += '{"caption": "-"},\n'
			text = text[:-2] + '\n'
			text += '\t'*4
			text += ']\n'
			text += '\t'*3
			text += '},\n'
		return text

	def genOriginalMenuText(self):
		show_arduino_menu = self.Settings.get('show_Arduino_menu')
		show_serial_menu = self.Settings.get('show_serial_menu')
		arduino_root = self.Settings.get('Arduino_root')

		header_menu_file = os.path.join(self.template_dir, 'menu_preference')
		self.genCommandsFile(self.display_text_dict, mode = 'mini')
		text = utils.readFile(header_menu_file)
		if show_arduino_menu:
			text += ',\n'
			if arduino.isArduinoFolder(arduino_root):
				main_menu_file = os.path.join(self.template_dir, 'menu_full')
				self.genCommandsFile(self.display_text_dict)
			else:
				main_menu_file = os.path.join(self.template_dir, 'menu_mini')
			text += utils.readFile(main_menu_file)
		if show_serial_menu:
			text += ',\n'
			menu_file = os.path.join(self.template_dir, 'menu_serial')
			text += utils.readFile(menu_file)
		text += '\n]'
		self.org_menu_text = text

	def genFullMenuText(self):
		self.menu_text = self.org_menu_text
		if self.sketchbook_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Sketchbook)s", "command": "not_enable"},', self.sketchbook_menu_text)
		if self.import_lib_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Import_Library...)s", "command": "not_enable"},', self.import_lib_menu_text)
		if self.board_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Board)s", "command": "not_enable"},', self.board_menu_text)
		if self.processor_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Processor)s", "command": "not_enable"},', self.processor_menu_text)
		if self.usb_type_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(USB_Type)s", "command": "not_enable"},', self.usb_type_menu_text)
		if self.keyboard_layout_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Keyboard_Layout)s", "command": "not_enable"},', self.keyboard_layout_menu_text)
		if self.serial_port_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Serial_Port)s", "command": "not_enable"},', self.serial_port_menu_text)
		if self.programmer_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Programmer)s", "command": "not_enable"},', self.programmer_menu_text)
		if self.lang_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Language)s", "command": "not_enable"},', self.lang_menu_text)
		if self.examples_menu_text:
			self.menu_text = self.menu_text.replace('{"caption": "%(Examples)s", "command": "not_enable"},', self.examples_menu_text)
		
	def genFile(self, display_text_dict):
		self.display_text_dict = display_text_dict
		menu_text = self.menu_text % display_text_dict
		utils.writeFile(self.file, menu_text)

	def genCommandsFile(self, display_text_dict, mode = 'full'):
		if mode == 'full':
			filename = 'commands_full'
		else:
			filename = 'commands_mini'
		template_file_path = os.path.join(self.template_dir, filename)
		temp_text = utils.readFile(template_file_path)
		text = temp_text % display_text_dict
		utils.writeFile(self.commands_file, text)

	def genCompletionsFile(self, mode = 'full'):
		text = '{\n'
		text += '\t"scope": "source.arduino",\n'
		text += '\t"completions":\n'
		text += '\t[\n'
		if mode == 'full':
			for keyword in self.arduino_info.getKeywordList():
				if self.arduino_info.getKeywordType(keyword):
					text += '\t\t"%s",\n' % keyword
			text = text[:-2] + '\n'
		text += '\t]\n'
		text += '}'
		utils.writeFile(self.completions_file, text)

	def genDictText(self, l, description):
		text = ''
		if l:
			text += '\t' * 2
			text += '<dict>\n'
			text += '\t' * 3
			text += '<key>match</key>\n'
			text += '\t' * 3
			text += '<string>\\b('
			for item in l:
				text += item
				text += '|'
			text = text[:-1]
			text += ')\\b</string>\n'
			text += '\t' * 3
			text += '<key>name</key>\n'
			text += '\t' * 3
			text += '<string>'
			text += description
			text += '</string>\n'
			text += '\t' * 2
			text += '</dict>'
		return text

	def genSyntexFile(self, mode = 'full'):
		constant_list = []
		keyword_list = []
		function_list = []
		if mode == 'full':
			for keyword in self.arduino_info.getKeywordList():
				if self.arduino_info.getKeywordType(keyword):
					if 'LITERAL' in self.arduino_info.getKeywordType(keyword):
						constant_list.append(keyword)
					elif self.arduino_info.getKeywordType(keyword) == 'KEYWORD1':
						keyword_list.append(keyword)
					else:
						function_list.append(keyword)

		text = ''
		text += self.genDictText(constant_list, 'constant.arduino')
		text += self.genDictText(keyword_list, 'keyword.arduino')
		text += self.genDictText(function_list, 'entity.name.function.arduino')

		temp_file_path = os.path.join(self.template_dir, 'syntax')
		temp_text = utils.readFile(temp_file_path)
		temp_text = temp_text.replace('%(keyword)s', text)
		utils.writeFile(self.syntax_file, temp_text)
		
	def genSketchbookMenuText(self):
		sketch_list = self.arduino_info.getSketchList()
		self.sketchbook_menu_text = self.getMenuText(sketch_list, '%(Sketchbook)s', 'select_sketch')

	def genImportLibMenuText(self):
		lib_list = self.arduino_info.getLibList()
		self.import_lib_menu_text = self.getMenuText(lib_list, '%(Import_Library...)s', 'import_library')

	def genBoardMenuText(self):
		self.board_menu_text = ''
		platform_list = self.arduino_info.getPlatformList()
		for platform in platform_list:
			caption = platform.replace('Boards', '%(Board)s')
			board_list = self.arduino_info.getBoardList(platform)
			self.board_menu_text += self.getMenuText(board_list, caption, 'select_board', checkbox = True)

	def genProcessorMenuText(self):
		processor_list = self.arduino_info.getProcessorList()
		self.processor_menu_text = self.getMenuText([processor_list], '%(Processor)s', 'select_processor', checkbox = True)
		if processor_list:
			processor = self.Settings.get('processor')
			if not processor in processor_list:
				processor = processor_list[0]
				self.Settings.set('processor', processor)
				sublime.save_settings('Stino.sublime-settings')

	def genUSBTypeMenuText(self):
		usb_type_list = self.arduino_info.getUSBTypeList()
		self.usb_type_menu_text = self.getMenuText([usb_type_list], '%(USB_Type)s', 'select_usb_type', checkbox = True)
		if usb_type_list:
			usb_type = self.Settings.get('usb_type')
			if not usb_type in usb_type_list:
				usb_type = usb_type_list[0]
				self.Settings.set('usb_type', usb_type)
				sublime.save_settings('Stino.sublime-settings')

	def genKeyboardLayoutMenuText(self):
		keyboard_layout_list = self.arduino_info.getKeyboardLayoutList()
		self.keyboard_layout_menu_text = self.getMenuText([keyboard_layout_list], '%(Keyboard_Layout)s', 'select_keyboard_layout', checkbox = True)
		if keyboard_layout_list:
			keyboard_layout = self.Settings.get('keyboard_layout')
			if not keyboard_layout in keyboard_layout_list:
				keyboard_layout = keyboard_layout_list[0]
				self.Settings.set('keyboard_layout', keyboard_layout)
				sublime.save_settings('Stino.sublime-settings')

	def genSerialPortMenuText(self):
		serial_list = utils.getSerialPortList()
		self.serial_port_menu_text = self.getMenuText([serial_list], '%(Serial_Port)s', 'select_serial_port', checkbox = True)

	def genProgrammerMenuText(self):
		programmer_list = self.arduino_info.getProgrammerList()
		self.programmer_menu_text = self.getMenuText(programmer_list, '%(Programmer)s', 'select_programmer', checkbox = True)
		no_programmer = True
		has_programmer = self.arduino_info.hasProgrammer()
		if has_programmer:
			programmer = self.Settings.get('programmer')
			for programmers in programmer_list:
				if programmer in programmers:
					no_programmer = False
					break
			if no_programmer:
				programmer = programmer_list[0][0]
				self.Settings.set('programmer', programmer)
				sublime.save_settings('Stino.sublime-settings')

	def genExampleMenuText(self):
		example_list = self.arduino_info.getExampleList()
		self.examples_menu_text = self.getMenuText(example_list, '%(Examples)s', 'select_example')

	def genLangMenuText(self):
		lang_list = [self.lang.lang_text_dict[language] for language in self.lang.getLangList()]
		lang_list = [lang_list]
		self.lang_menu_text = self.getMenuText(lang_list, '%(Language)s', 'select_language', checkbox = True)
