#-*- coding: utf-8 -*-
# stino/menu.py

import os
import json

from . import constant
from . import fileutil
from . import serial

class MainMenu:
	def __init__(self, language, arduino_info, file_name):
		self.language = language
		self.file = os.path.join(constant.stino_root, file_name)
		self.arduino_info = arduino_info
		self.menu = MenuItem('Main Menu')
		self.refresh()

	def getMenu(self):
		return self.menu

	def printMenu(self):
		printMenu(self.menu)

	def buildMenu(self):
		self.menu = buildMainMenu(self.language, self.arduino_info)

	def genFile(self):
		data = convertMenuToData(self.menu)
		text = json.dumps(data, indent = 4)
		# opened_file = open(self.file, 'w')
		# opened_file.write(text)
		# opened_file.close()
		fileutil.writeFile(self.file, text)

	def refresh(self):
		self.buildMenu()
		self.genFile()

class MenuItem:
	def __init__(self, caption = '-'):
		self.caption = caption
		self.id = caption.lower()
		self.mnemonic = None
		self.children = []
		self.command = None
		self.checkbox = False
		self.args = None

	def hasSubmenu(self):
		state = False
		if self.children:
			state = True
		return state

	def getCaption(self):
		return self.caption

	def getMnemonic(self):
		return self.mnemonic

	def getId(self):
		return self.id

	def getCommand(self):
		return self.command

	def getCheckbox(self):
		return self.checkbox

	def getArgs(self):
		return self.args

	def getSubmenu(self):
		return self.children

	def addMenuItem(self, menu_item):
		self.children.append(menu_item)

	def addMenuGroup(self, menu_group):
		if self.hasSubmenu():
			seperator = MenuItem()
			self.addMenuItem(seperator)
		self.children += menu_group.getGroup()

	def setCaption(self, caption):
		self.caption = caption

	def setMnemonic(self, mnemonic):
		self.mnemonic = mnemonic

	def setId(self, ID):
		self.id = ID

	def setCommand(self, command):
		self.command = command

	def setCheckbox(self):
		self.checkbox = True

	def setArgs(self, args):
		self.args = args

	def getSubmenuItem(caption):
		subitem = None
		for item in self.children:
			if item.getCaption() == caption:
				subitem = item
		return subitem

class MenuItemGroup:
	def __init__(self):
		self.group = []

	def clear(self):
		self.group = []

	def hasMenuItem(self):
		state = False
		if self.group:
			state = True
		return state

	def addMenuItem(self, menu_item):
		self.group.append(menu_item)

	def removeMenuItem(self, menu_item):
		if menu_item in self.group:
			self.group.remove(menu_item)

	def getGroup(self):
		return self.group

def printMenu(menu, level = 0):
	caption = menu.getCaption()
	if level > 0:
		caption = '\t' * level + '|__' + caption
	print(caption)

	if menu.hasSubmenu():
		for submenu in menu.getSubmenu():
			printMenu(submenu, level+1)

def buildMenuFromSketch(sketch):
	name = sketch.getName()
	cur_menu = MenuItem(name)
	if sketch.hasSubItem():
		for sub_sketch in sketch.getSubItemList():
			sub_menu_item = buildMenuFromSketch(sub_sketch)
			cur_menu.addMenuItem(sub_menu_item)
	else:
		folder = sketch.getFolder()
		if folder:
			command = 'open_sketch'
			args = {'folder' : folder}
			cur_menu.setCommand(command)
			cur_menu.setArgs(args)
	return cur_menu

def buildSketchbookMenu(language, arduino_info):
	sketchbook = arduino_info.getSketchbook()
	sketchbook.setName(language.translate('Sketchbook'))
	sketchbook_menu = buildMenuFromSketch(sketchbook)
	return sketchbook_menu

def buildLibraryMenu(language, arduino_info):
	library_menu = MenuItem(language.translate('Import Library'))
	platform_list = arduino_info.getPlatformList()
	for platform in platform_list:
		name = platform.getName()
		sub_menu_item = MenuItem(name)
		lib_list = platform.getLibList()
		for lib in lib_list:
			lib_name = lib.getName()
			lib_menu_item = MenuItem(lib_name)
			lib_folder = lib.getFolder()
			command = 'import_library'
			lib_args = {'folder' : lib_folder}
			lib_menu_item.setCommand(command)
			lib_menu_item.setArgs(lib_args)
			sub_menu_item.addMenuItem(lib_menu_item)
		library_menu.addMenuItem(sub_menu_item)
	return library_menu

def buildExampleMenu(language, arduino_info):
	example_menu = MenuItem(language.translate('Examples'))
	platform_list = arduino_info.getPlatformList()
	for platform in platform_list:
		cur_example = platform.getExample()
		sub_menu_item = buildMenuFromSketch(cur_example)
		example_menu.addMenuItem(sub_menu_item)
	return example_menu

def buildBoardMenuList(arduino_info):
	board_menu_list = []
	platform_list = arduino_info.getPlatformList()
	for platform in platform_list:
		platform_id = platform_list.index(platform)
		name = platform.getName()
		board_menu = MenuItem(name)
		board_list = platform.getBoardList()
		if board_list:
			for cur_board in board_list:
				board_id = board_list.index(cur_board)
				board_name = cur_board.getName()
				board_menu_item = MenuItem(board_name)
				command = 'choose_board'
				board_args = {'platform' : platform_id, 'board': board_id}
				board_menu_item.setCommand(command)
				board_menu_item.setArgs(board_args)
				board_menu_item.setCheckbox()
				board_menu.addMenuItem(board_menu_item)
			board_menu_list.append(board_menu)
	return board_menu_list

def buildBoardOptionMenuList(arduino_info):
	board_option_menu_list = []
	platform_id = constant.sketch_settings.get('platform', -1)
	board_id = constant.sketch_settings.get('board', -1)
	if platform_id > -1:
		platform_list = arduino_info.getPlatformList()
		if platform_id < len(platform_list):
			platform = platform_list[platform_id]
			board_list = platform.getBoardList()
			if board_id < len(board_list):
				board = board_list[board_id]
				board_option_list = board.getOptionList()
				for board_option in board_option_list:
					board_option_id = board_option_list.index(board_option)
					board_option_name = board_option.getName()
					board_option_menu = MenuItem(board_option_name)
					board_option_item_list = board_option.getItemList()
					for board_option_item in board_option_item_list:
						board_option_item_id = board_option_item_list.index(board_option_item)
						board_option_item_name = board_option_item.getName()
						board_option_item_menu = MenuItem(board_option_item_name)
						command = 'choose_board_option'
						args = {'board_option' : board_option_id, 'board_option_item' : board_option_item_id}
						board_option_item_menu.setCommand(command)
						board_option_item_menu.setArgs(args)
						board_option_item_menu.setCheckbox()
						board_option_menu.addMenuItem(board_option_item_menu)
					board_option_menu_list.append(board_option_menu)
	return board_option_menu_list

def buildProgrammerMenu(language, arduino_info):
	programmer_menu = MenuItem(language.translate('Programmer'))
	platform_id = chosen_platform = constant.sketch_settings.get('platform', -1)
	if platform_id > -1:
		platform_list = arduino_info.getPlatformList()
		if platform_id < len(platform_list):
			platform = platform_list[platform_id]

			programmer_list = platform.getProgrammerList()
			if programmer_list:
				for cur_programmer in programmer_list:
					programmer_id = programmer_list.index(cur_programmer)
					programmer_name = cur_programmer.getName()
					programmer_menu_item = MenuItem(programmer_name)
					command = 'choose_programmer'
					programmer_args = {'platform' : platform_id, 'programmer': programmer_id}
					programmer_menu_item.setCommand(command)
					programmer_menu_item.setArgs(programmer_args)
					programmer_menu_item.setCheckbox()
					programmer_menu.addMenuItem(programmer_menu_item)
	return programmer_menu

def buildSerialPortMenu(language):
	serial_port_menu = MenuItem(language.translate('Serial Port'))

	serial_port_list = serial.getSerialPortList()
	for serial_port in serial_port_list:
		serial_port_item = MenuItem(serial_port)
		index = serial_port_list.index(serial_port)
		args = {'serial_port' : index}
		serial_port_item.setCommand('choose_serial_port')
		serial_port_item.setArgs(args)
		serial_port_item.setCheckbox()
		serial_port_menu.addMenuItem(serial_port_item)
	return serial_port_menu

def buildLineEndingMenu(language):
	line_ending_menu = MenuItem(language.translate('Line Ending'))
	for line_ending_caption in constant.line_ending_caption_list:
		sub_menu = MenuItem(line_ending_caption)
		line_ending_caption_id = constant.line_ending_caption_list.index(line_ending_caption)
		args = {'line_ending' : line_ending_caption_id}
		sub_menu.setCommand('choose_line_ending')
		sub_menu.setArgs(args)
		sub_menu.setCheckbox()
		line_ending_menu.addMenuItem(sub_menu)
	return line_ending_menu

def buildDisplayModeMenu(language):
	display_mode_menu = MenuItem(language.translate('Display as'))
	for display_mode in constant.display_mode_list:
		sub_menu = MenuItem(display_mode)
		display_mode_id = constant.display_mode_list.index(display_mode)
		args = {'display_mode' : display_mode_id}
		sub_menu.setCommand('choose_display_mode')
		sub_menu.setArgs(args)
		sub_menu.setCheckbox()
		display_mode_menu.addMenuItem(sub_menu)
	return display_mode_menu

def buildBaudrateMenu(language):
	baudrate_menu = MenuItem(language.translate('Baudrate'))
	for baudrate in constant.baudrate_list:
		sub_menu = MenuItem(baudrate)
		baudrate_id = constant.baudrate_list.index(baudrate)
		args = {'baudrate' : baudrate_id}
		sub_menu.setCommand('choose_baudrate')
		sub_menu.setArgs(args)
		sub_menu.setCheckbox()
		baudrate_menu.addMenuItem(sub_menu)
	return baudrate_menu

def buildSerialMonitorMenu(language):
	serial_monitor_menu = MenuItem(language.translate('Serial Monitor'))
	start_menu = MenuItem(language.translate('Start'))
	start_menu.setCommand('start_serial_monitor')
	stop_menu = MenuItem(language.translate('Stop'))
	stop_menu.setCommand('stop_serial_monitor')
	send_menu = MenuItem(language.translate('Send'))
	send_menu.setCommand('send_serial_text')
	line_ending_menu = buildLineEndingMenu(language)
	display_mode_menu = buildDisplayModeMenu(language)
	baudrate_menu = buildBaudrateMenu(language)
	serial_monitor_menu.addMenuItem(start_menu)
	serial_monitor_menu.addMenuItem(stop_menu)
	serial_monitor_menu.addMenuItem(send_menu)
	serial_monitor_menu.addMenuItem(baudrate_menu)
	serial_monitor_menu.addMenuItem(line_ending_menu)
	serial_monitor_menu.addMenuItem(display_mode_menu)
	return serial_monitor_menu

def buildLanguageMenu(language):
	language_menu = MenuItem(language.translate('Language'))

	language_item_list = language.getLanguageItemList()
	for language_item in language_item_list:
		caption = language_item.getCaption()
		language_menu_item = MenuItem(caption)
		index = language_item_list.index(language_item)
		args = {'language' : index}
		language_menu_item.setCommand('choose_language')
		language_menu_item.setArgs(args)
		language_menu_item.setCheckbox()
		language_menu.addMenuItem(language_menu_item)
	return language_menu

def buildSettingMenu(language):
	setting_menu = MenuItem(language.translate('Preferences'))

	select_arduino_folder_menu = MenuItem(language.translate('Select Arduino Application Folder'))
	select_arduino_folder_menu.setCommand('choose_arduino_folder')

	change_sketchbook_folder_menu = MenuItem(language.translate('Change Sketchbook Folder'))
	change_sketchbook_folder_menu.setCommand('change_sketchbook_folder')

	change_build_folder_menu = MenuItem(language.translate('Select Build Folder'))
	change_build_folder_menu.setCommand('choose_build_folder')


	language_menu = buildLanguageMenu(language)

	setting_menu.addMenuItem(select_arduino_folder_menu)
	setting_menu.addMenuItem(change_sketchbook_folder_menu)
	setting_menu.addMenuItem(change_build_folder_menu)
	setting_menu.addMenuItem(language_menu)
	return setting_menu

def buildReferenceMenu(language):
	references_menu = MenuItem(language.translate('References'))
	getting_started_menu = MenuItem(language.translate('Getting Started'))
	getting_started_menu.setCommand('open_ref')
	args = {'url': 'Guide_index'}
	getting_started_menu.setArgs(args)

	troubleshooting_menu = MenuItem(language.translate('Troubleshooting'))
	troubleshooting_menu.setCommand('open_ref')
	args = {'url': 'Guide_Troubleshooting'}
	troubleshooting_menu.setArgs(args)

	ref_menu = MenuItem(language.translate('Reference'))
	ref_menu.setCommand('open_ref')
	args = {'url': 'index'}
	ref_menu.setArgs(args)

	find_menu = MenuItem(language.translate('Find in Reference'))
	find_menu.setCommand('find_in_reference')

	faq_menu = MenuItem(language.translate('Frequently Asked Questions'))
	faq_menu.setCommand('open_ref')
	args = {'url': 'FAQ'}
	faq_menu.setArgs(args)

	website_menu = MenuItem(language.translate('Visit Arduino Website'))
	website_menu.setCommand('open_url')
	args = {'url': 'http://arduino.cc'}
	website_menu.setArgs(args)

	references_menu.addMenuItem(getting_started_menu)
	references_menu.addMenuItem(troubleshooting_menu)
	references_menu.addMenuItem(ref_menu)
	references_menu.addMenuItem(find_menu)
	references_menu.addMenuItem(faq_menu)
	references_menu.addMenuItem(website_menu)
	return references_menu

def buildSketchMenuGroup(language, arduino_info):
	new_sketch_menu = MenuItem(language.translate('New Sketch'))
	new_sketch_menu.setCommand('new_sketch')

	sketch_menu_group = MenuItemGroup()
	sketchbook_menu = buildSketchbookMenu(language, arduino_info)
	examples_menu = buildExampleMenu(language, arduino_info)

	sketch_menu_group.addMenuItem(new_sketch_menu)
	sketch_menu_group.addMenuItem(sketchbook_menu)
	sketch_menu_group.addMenuItem(examples_menu)
	return sketch_menu_group

def buildLibraryMenuGroup(language, arduino_info):
	library_menu_group = MenuItemGroup()
	import_lib_menu = buildLibraryMenu(language, arduino_info)

	show_sketch_folder_menu = MenuItem(language.translate('Show Sketch Folder'))
	show_sketch_folder_menu.setCommand('show_sketch_folder')
	library_menu_group.addMenuItem(import_lib_menu)
	library_menu_group.addMenuItem(show_sketch_folder_menu)
	return library_menu_group

def buildDebugMenuGroup(language):
	debug_menu_group = MenuItemGroup()
	extra_flag_menu = MenuItem(language.translate('Extra Flags'))
	extra_flag_menu.setCommand('set_extra_flag')

	compile_menu = MenuItem(language.translate('Verify/Compile'))
	compile_menu.setCommand('compile_sketch')

	upload_menu = MenuItem(language.translate('Upload'))
	upload_menu.setCommand('upload_sketch')

	programmer_upload_menu = MenuItem(language.translate('Upload by Using Programmer'))
	programmer_upload_menu.setCommand('upload_using_programmer')

	debug_menu_group.addMenuItem(extra_flag_menu)
	debug_menu_group.addMenuItem(compile_menu)
	debug_menu_group.addMenuItem(upload_menu)
	debug_menu_group.addMenuItem(programmer_upload_menu)
	return debug_menu_group

def buildBoardMenuGroup(arduino_info):
	board_menu_group = MenuItemGroup()
	board_menu_list = buildBoardMenuList(arduino_info)
	board_option_menu_list = buildBoardOptionMenuList(arduino_info)
	sub_menu_list = board_menu_list + board_option_menu_list
	for sub_menu in sub_menu_list:
		board_menu_group.addMenuItem(sub_menu)
	return board_menu_group

def buildProgrammerMenuGroup(language, arduino_info):
	programmer_menu_group = MenuItemGroup()
	programmer_menu = buildProgrammerMenu(language, arduino_info)
	programmer_menu_group.addMenuItem(programmer_menu)

	burn_bootloader_menu = MenuItem(language.translate('Burn Bootloader'))
	burn_bootloader_menu.setCommand('burn_bootloader')
	programmer_menu_group.addMenuItem(burn_bootloader_menu)
	return programmer_menu_group

def buildSerialMenuGroup(language):
	serial_menu_group = MenuItemGroup()
	serial_port_menu = buildSerialPortMenu(language)
	serial_monitor_menu = buildSerialMonitorMenu(language)
	serial_menu_group.addMenuItem(serial_port_menu)
	serial_menu_group.addMenuItem(serial_monitor_menu)
	return serial_menu_group

def buildToolsMenuGroup(language):
	tools_menu_group = MenuItemGroup()
	auto_format_menu = MenuItem(language.translate('Auto Format'))
	auto_format_menu.setCommand('auto_format')

	archive_sketch_menu = MenuItem(language.translate('Archive Sketch'))
	archive_sketch_menu.setCommand('archive_sketch')

	tools_menu_group.addMenuItem(auto_format_menu)
	tools_menu_group.addMenuItem(archive_sketch_menu)
	return tools_menu_group

def buildSettingMenuGroup(language):
	setting_menu_group = MenuItemGroup()
	setting_menu = buildSettingMenu(language)

	global_setting_menu = MenuItem(language.translate('Global Setting'))
	global_setting_menu.setCommand('set_global_setting')
	global_setting_menu.setCheckbox()

	full_compilation_menu = MenuItem(language.translate('Full Compilation'))
	full_compilation_menu.setCommand('set_full_compilation')
	full_compilation_menu.setCheckbox()


	bare_gcc_only_menu = MenuItem(language.translate('Bare GCC Build (No Arduino code-munging)'))
	bare_gcc_only_menu.setCommand('set_bare_gcc_only')
	bare_gcc_only_menu.setCheckbox()

	show_compilation_menu = MenuItem(language.translate('Compilation'))
	show_compilation_menu.setCommand('show_compilation_output')
	show_compilation_menu.setCheckbox()

	show_upload_menu = MenuItem(language.translate('Upload'))
	show_upload_menu.setCommand('show_upload_output')
	show_upload_menu.setCheckbox()

	show_verbose_output_menu = MenuItem(language.translate('Show Verbose Output'))
	show_verbose_output_menu.addMenuItem(show_compilation_menu)
	show_verbose_output_menu.addMenuItem(show_upload_menu)

	verify_code_menu = MenuItem(language.translate('Verify Code after Upload'))
	verify_code_menu.setCommand('verify_code')
	verify_code_menu.setCheckbox()

	setting_menu_group.addMenuItem(setting_menu)
	setting_menu_group.addMenuItem(global_setting_menu)
	setting_menu_group.addMenuItem(bare_gcc_only_menu)
	setting_menu_group.addMenuItem(full_compilation_menu)
	setting_menu_group.addMenuItem(show_verbose_output_menu)
	setting_menu_group.addMenuItem(verify_code_menu)
	return setting_menu_group

def buildHelpMenuGroup(language):
	help_menu_group = MenuItemGroup()
	references_menu = buildReferenceMenu(language)
	about_menu = MenuItem(language.translate('About Stino'))
	about_menu.setCommand('about_stino')

	help_menu_group.addMenuItem(references_menu)
	help_menu_group.addMenuItem(about_menu)
	return help_menu_group

# Build Main Menu
def buildPreferenceMenu(language):
	preference_menu = MenuItem('Preferences')
	preference_menu.setMnemonic('n')

	show_arduino_menu = MenuItem(language.translate('Show Arduino Menu'))
	show_arduino_menu.setCommand('show_arduino_menu')
	show_arduino_menu.setCheckbox()


	preference_menu.addMenuItem(show_arduino_menu)
	return preference_menu

def buildArduinoMenu(language, arduino_info):
	arduino_menu = MenuItem('Arduino')
	sketch_menu_group = buildSketchMenuGroup(language, arduino_info)
	library_menu_group = buildLibraryMenuGroup(language, arduino_info)
	debug_menu_group = buildDebugMenuGroup(language)
	board_menu_group = buildBoardMenuGroup(arduino_info)
	programmer_menu_group = buildProgrammerMenuGroup(language, arduino_info)
	serial_menu_group = buildSerialMenuGroup(language)
	tools_menu_group = buildToolsMenuGroup(language)
	setting_menu_group = buildSettingMenuGroup(language)
	help_menu_group = buildHelpMenuGroup(language)

	arduino_menu.addMenuGroup(sketch_menu_group)
	arduino_menu.addMenuGroup(library_menu_group)
	arduino_menu.addMenuGroup(debug_menu_group)
	arduino_menu.addMenuGroup(board_menu_group)
	arduino_menu.addMenuGroup(programmer_menu_group)
	arduino_menu.addMenuGroup(serial_menu_group)
	arduino_menu.addMenuGroup(tools_menu_group)
	arduino_menu.addMenuGroup(setting_menu_group)
	arduino_menu.addMenuGroup(help_menu_group)
	return arduino_menu

def buildMainMenu(language, arduino_info):
	main_menu = MenuItem('Main Menu')

	show_arduino_menu = constant.global_settings.get('show_arduino_menu', True)
	preference_menu = buildPreferenceMenu(language)
	main_menu.addMenuItem(preference_menu)

	if show_arduino_menu:
		arduino_menu = buildArduinoMenu(language, arduino_info)
		main_menu.addMenuItem(arduino_menu)
	return main_menu

def convertMenuToData(cur_menu, level = 0):
	caption = cur_menu.getCaption()
	sub_menu_list = cur_menu.getSubmenu()
	if sub_menu_list:
		sub_data_list = []
		for sub_menu in sub_menu_list:
			sub_data = convertMenuToData(sub_menu, level + 1)
			if sub_data:
				sub_data_list.append(sub_data)
		if level > 0:
			menu_id = cur_menu.getId()
			menu_mnemonic = cur_menu.getMnemonic()
			data = {}
			data['caption'] = caption
			data['id'] = menu_id
			data['mnemonic'] = menu_mnemonic
			data['children'] = sub_data_list
		else:
			data = sub_data_list
	else:
		data = {}
		command = cur_menu.getCommand()
		if command or caption == '-':
			args = cur_menu.getArgs()
			checkbox = cur_menu.getCheckbox()
			data['caption'] = caption
			data['command'] = command
			if args:
				data['args'] = args
			if checkbox:
				data['checkbox'] = checkbox
	return data

