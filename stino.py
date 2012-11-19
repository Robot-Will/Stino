#-*- coding: UTF-8 -*-

import sublime, sublime_plugin
import os, sys, stat
import locale, codecs
import math

if sys.platform == 'win32':
	import _winreg

########## Global Setting ##########
ENCODING = codecs.lookup(locale.getpreferredencoding()).name
STINO_ROOT = os.getcwd()
if not isinstance(STINO_ROOT, unicode):
	STINO_ROOT = STINO_ROOT.decode(ENCODING)
TEMPLATE_DIR = os.path.join(STINO_ROOT, 'template')

Setting_File = 'Stino.sublime-settings'
Setting = sublime.load_settings(Setting_File)

Arduino_Ext = ['.ino', '.pde']
########## Functions ##########
## 功能函数 ##
def get_Win_Vol():
	vol_list = []
	for label in xrange(65, 91):
		vol = chr(label) + ':\\'
		if os.path.isdir(vol):
			vol_list.append(vol)
	return vol_list

def get_Key(line):
	line = line.strip()
	if '=' in line:
		index = line.index('=')
		key = line[:index]
	else:
		key = ''
	return key.strip()

def get_Value(line):
	line = line.strip()
	if '=' in line:
		index = line.index('=')
		value = line[(index+1):]
	else:
		value = ''
	return value.strip()

def get_Blocks(lines):
	block_index = 0
	block = []
	blocks = []
	for line in lines:
		line = line.strip()
		if '.name' in line:
			if block_index != 0:
				blocks.append(block)
			block = []
			block_index += 1
		if line:
			if not '###' in line:
				block.append(line)
	blocks.append(block)
	return blocks

def open_Sketch(sketch_folder_path):
	file_name = os.path.split(sketch_folder_path)[1] + '.ino'
	sketch_file_path = os.path.join(sketch_folder_path, file_name)
	sublime.run_command('new_window')
	new_window = sublime.windows()[-1]
	view = new_window.open_file(sketch_file_path)
	view.set_syntax_file('Packages/C++/C++.tmLanguage')

def clean_selection():
	Setting.set('board', '')
	Setting.set('board_name', '')
	Setting.set('processors', [])
	Setting.set('processor', '')

def list_Dir(path, with_files = True):
	file_list = []
	files = os.listdir(path)
	files.sort()

	if not isinstance(path, unicode):
			path = path.decode(ENCODING)

	for f in files:
		is_access = False
		if not isinstance(f, unicode):
			f = f.decode(ENCODING)

		f_path = os.path.join(path, f)
		if os.path.isdir(f_path):
			if not (f[0] == '$' or f[0] == '.'):
				try:
					os.listdir(f_path)
				except:
					is_access = False
				else:
					is_access = True
		else:
			if with_files:
				try:
					test = open(f_path, 'r')
					test.close()
				except:
					is_access = False
				else:
					is_access = True

		if is_access:
			file_list.append(f)
	return file_list

def read_File(file_path):
	f = open(file_path, 'r')
	lines = f.readlines()
	f.close()
	return lines

def write_File(file_path, text, encoding = 'utf-8'):
	text = text.encode(encoding)
	f = open(file_path, 'w')
	f.write(text)
	f.close()

## Initiating Sys Paths ##
def get_Arduino_User_Root():
	if sys.platform == 'win32':
		app_root = os.getenv('appdata')
		arduino_user_root = os.path.join(app_root, 'Arduino')
	elif sys.platform == 'darwin':
		home_root = os.getenv('HOME')
		app_root = os.path.join(home_root, 'Library')
		arduino_user_root = os.path.join(app_root, 'Arduino')
	else:
		home_root = os.getenv('HOME')
		arduino_user_root = os.path.join(home_root, '.arduino')
	if not os.path.exists(arduino_user_root):
		os.mkdir(arduino_user_root)
	Setting.set('arduino_user_root', arduino_user_root)
	sublime.save_settings(Setting_File)

def get_Arduino_Sketch_Root():
	if sys.platform == 'win32':
		key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,\
            	r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',)
		doc_path = _winreg.QueryValueEx(key, 'Personal')[0]
		sketch_root = os.path.join(doc_path, 'Arduino')
	elif sys.platform == 'darwin':
		home_path = os.getenv('HOME')
		doc_path = os.path.join(home_path, 'Documents')
		sketch_root = os.path.join(doc_path, 'Arduino')
	else:
		home_path = os.getenv('HOME')
		sketch_root = os.path.join(home_path, 'sketchbook')
	if not os.path.exists(sketch_root):
		os.mkdir(sketch_root)
	Setting.set('arduino_sketch_root', sketch_root)
	sublime.save_settings(Setting_File)

## Reading Arduino Infos ##
def get_Arduino_Version():
	version = 0.0
	version_txt = ''
	arduino_app_root = Setting.get('arduino_app_root')
	lib_path = os.path.join(arduino_app_root, 'lib')
	ver_path = os.path.join(lib_path, 'version.txt')
	f = open(ver_path, 'r')
	version_txt = f.readline().strip()
	f.close()
	power = 0
	for num in version_txt.split('.'):
		for n in num:
			if not (n in '0123456789'):
				index = num.index(n)
				num = num[:index]
				break
		num = int(num)
		version += num * math.pow(10, power)
		power -= 1
	Setting.set('arduino_version_txt', version_txt)
	Setting.set('arduino_version', version)
	sublime.save_settings(Setting_File)

def get_Arduino_Platforms():
	platforms = []
	arduino_core_paths = []
	arduino_app_root = Setting.get('arduino_app_root')
	hardware_path = os.path.join(arduino_app_root, 'hardware')
	arduino_path = os.path.join(hardware_path, 'arduino')
	dirs = list_Dir(arduino_path, False)

	for d in dirs:
		d_path = os.path.join(arduino_path, d)
		platform_path = os.path.join(d_path, 'platform.txt')
		if os.path.isfile(platform_path):
			f = open(platform_path, 'r')
			for line in f.readlines():
				if 'name' in line:
					platform = get_Value(line)
					break
			platforms.append(platform)
			arduino_core_paths.append(d_path)
	if not platforms:
		platforms.append('Arduino AVR Boards')
		arduino_core_paths.append(arduino_path)
	Setting.set('arduino_platforms', platforms)
	Setting.set('arduino_core_paths', arduino_core_paths)
	sublime.save_settings(Setting_File)

def is_Arduino_App_Root(path):
	state = False
	if os.path.exists(path):
		hardware_path = os.path.join(path, 'hardware')
		lib_path = os.path.join(path, 'lib')
		if os.path.exists(hardware_path) and os.path.exists(lib_path):
			state = True

	if state:
		lib_path = os.path.join(path, 'lib')
		ver_path = os.path.join(lib_path, 'version.txt')
		if not os.path.isfile(ver_path):
			state = False

	if state:
		Setting.set('arduino_app_root', path)
		get_Arduino_Version()
		get_Arduino_Platforms()

		if sys.platform == 'win32':
			posix_root = os.path.join(path, 'hardware\\tools\\avr\\utils\\bin')
		else:
			posix_root = ''
		Setting.set('posix_root', posix_root)
		sublime.save_settings(Setting_File)
	return state

def check_Arduino_App_Root():
	exist = False
	path = Setting.get('arduino_app_root', '')
	if is_Arduino_App_Root(path):
		exist = True
	if not exist:
		paths = ['/Applications/Arduino.app/Contents/Resources/Java', 
			'/usr/share/arduino', '/opt/arduino', '/usr/local/share/arduino']
		for path in paths:
			if is_Arduino_App_Root(path):
				exist = True
				break
	if not exist:
		Setting.set('arduino_app_root', '')
		sublime.save_settings(Setting_File)

## 菜单文字生成 ##
def get_Menu_Text(itemlist, caption, command, checkbox = False):
	text = '{"caption": "%s", "command": "%s"},' % (caption, 'not_enable')

	has_submenu = False
	for sublist in itemlist:
		if len(sublist) > 0:
			has_submenu = True
	
	if has_submenu:
		text = '\t'*3
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

def get_lang():
	lang_path = os.path.join(STINO_ROOT, 'lang')
	files = list_Dir(lang_path)

	languages = []
	lang_files = []
	for f in files:
		f_path = os.path.join(lang_path, f)
		if os.path.isfile(f_path):
			lines = read_File(f_path)
			for line in lines:
				line = line.strip()
				if line and (not '#' in line):
					line = line.decode('utf-8')
					key = get_Key(line)
					value = get_Value(line)
					if 'LANG' in key:
						language = value
						languages.append(language)
						lang_files.append(f_path)
						break

	for language in languages:
		if 'Simplified Chinese' in language:
			zh_CN_txt = language
		if 'English' in language:
			en_txt = language

	cur_lang = Setting.get('language')
	if cur_lang and (cur_lang in languages):
		language = cur_lang
	else:
		l = locale.getdefaultlocale()[0]
		if 'zh_CN' in l:
			language = zh_CN_txt
		else:
			language = en_txt

	display_texts = {}
	index = languages.index(language)
	f_path = lang_files[index]
	lines = read_File(f_path)

	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			line = line.decode('utf-8')
			key = get_Key(line)
			value = get_Value(line)
			display_texts[key] = value

	Setting.set('language', language)
	Setting.set('languages', languages)
	Setting.set('lang_files', lang_files)
	Setting.set('display_texts', display_texts)
	sublime.save_settings(Setting_File)

## 生成Sketchbook菜单 ##
def get_Sketchbook_Menu(): 
	sketch_list = []
	arduino_sketch_root = Setting.get('arduino_sketch_root')
	dirs = list_Dir(arduino_sketch_root, False)
	for d in dirs:
		d_path = os.path.join(arduino_sketch_root, d)
		for ext in Arduino_Ext:
			sketch_name = '%s%s' % (d, ext)
			if os.path.isfile(os.path.join(d_path, sketch_name)):
				sketch_list.append(d)
	display_texts = Setting.get('display_texts')
	caption = display_texts['sketchbook']
	text = get_Menu_Text([sketch_list], caption, 'list_sketch')
	return text

## 生成Import Lib菜单 ##
def get_Import_Lib_Menu():
	lib_dirs = []
	lib_paths = []
	arduino_app_root = Setting.get('arduino_app_root')
	arduino_sketch_root = Setting.get('arduino_sketch_root')
	root_paths = [arduino_app_root, arduino_sketch_root]
	for path in root_paths:
		lib_path = os.path.join(path, 'libraries')
		if os.path.exists(lib_path):
			dir_list = list_Dir(lib_path, False)
			path_list = []
			if dir_list:
				for d in dir_list:
					path = os.path.join(lib_path, d)
					path_list.append(path)
				lib_dirs.append(dir_list)
				lib_paths.append(path_list)
	Setting.set('libraries', lib_paths)
	display_texts = Setting.get('display_texts')
	caption = display_texts['import_lib']
	text = get_Menu_Text(lib_dirs, caption, 'import_lib')
	return text

## 解析boards信息 ##
## Arduino 1.0.x
def parse_Board_1(blocks):
	boards = []
	board_names = []
	mcus = []
	for block in blocks:
		if block:
			board = get_Value(block[0])
			boards.append(board)
			board_names.append([])
			mcus.append([])
	return (boards, board_names, mcus)

## Arduino 1.5
def parse_Board_15(blocks):
	boards = []
	board_names = []
	mcus = []

	for block in blocks:
		if block:
			board = get_Value(block[0])
			cpu = ''
			for line in block:
				if '.cpu' in line:
					cpu = get_Value(line)
				if '.container' in line:
					board_name = board
					board = get_Value(line)
			if not board in boards:
				boards.append(board)
				board_names.append([])
				mcus.append([])
		
			if cpu:
				index = boards.index(board)
				board_names[index].append(board_name)
				mcus[index].append(cpu)
	return (boards, board_names, mcus)

## Arduino 1.5.1
def parse_Board_151(blocks):
	boards = []
	board_names = []
	mcus = []

	for block in blocks:
		if block:
			names = []
			cpus = []
			board = get_Value(block[0])
			read_cpu = False
			for line in block:
				if read_cpu:
					cpu = get_Value(line)
					cpus.append(cpu)
					read_cpu = False
				if '## ' in line:
					board_name = line[3:]
					names.append(board_name)
					read_cpu = True
			boards.append(board)
			board_names.append(names)
			mcus.append(cpus)
	return (boards, board_names, mcus)

## 解析所有的boards.txt文件
def parse_Core_Board_Files():
	platforms = Setting.get('arduino_platforms')
	arduino_core_paths = Setting.get('arduino_core_paths')
	version = Setting.get('arduino_version')

	boards_platform = []
	board_names_platform = []
	board_files_platform = []
	mcus_platform = []
	for platform in platforms:
		boards_platform.append([])
		board_names_platform.append([])
		board_files_platform.append([])
		mcus_platform.append([])

	index = 0
	for core_path in arduino_core_paths:
		board_path = os.path.join(core_path, 'boards.txt')
		lines = read_File(board_path)
		blocks = get_Blocks(lines)
			
		if version < 1.5:
			(boards, board_names, mcus) = parse_Board_1(blocks)
		elif version == 1.5:
			(boards, board_names, mcus) = parse_Board_15(blocks)
		else:
			(boards, board_names, mcus) = parse_Board_151(blocks)

		boards_platform[index].append(boards)
		board_names_platform[index].append(board_names)
		board_files_platform[index].append(board_path)
		mcus_platform[index].append(mcus)
		index += 1
	Setting.set('boards_platform', boards_platform)
	Setting.set('board_names_platform', board_names_platform)
	Setting.set('board_files_platform', board_files_platform)
	Setting.set('mcus_platform', mcus_platform)

def parse_Ext_Board_Files():
	arduino_sketch_root = Setting.get('arduino_sketch_root')
	arduino_platforms = Setting.get('arduino_platforms')
	boards_platform = Setting.get('boards_platform')
	board_names_platform = Setting.get('board_names_platform')
	mcus_platform = Setting.get('mcus_platform')
	board_files_platform = Setting.get('board_files_platform')

	hardware_path = os.path.join(arduino_sketch_root, 'hardware')
	if not os.path.isdir(hardware_path):
		return
	dirs = list_Dir(hardware_path, False)
	for d in dirs:
		d_path = os.path.join(hardware_path, d)
		platform_path = os.path.join(d_path, 'platform.txt')
		if os.path.isfile(platform_path):
			platform_file = open(platform_path, 'r')
			lines = platform_file.readlines()
			platform_file.close()
			for line in lines:
				if '.name' in line:
					platform = get_Value(line)
					break
		else:
			platform = 'Arduino AVR Boards'
		
		version = 1.0
		board_path = os.path.join(d_path, 'boards.txt')
		if os.path.isfile(board_path):
			board_file = open(board_path, 'r')
			all_txt = board_file.read()
			board_file.close()

			if '.container' in all_txt:
				version = 1.5
			elif '## ' in all_txt:
				version = 1.51
			else:
				version = 1.0

			lines = read_File(board_path)
			blocks = get_Blocks(lines)
			if version < 1.5:
				(boards, board_names, mcus) = parse_Board_1(blocks)
			elif version == 1.5:
				(boards, board_names, mcus) = parse_Board_15(blocks)
			else:
				(boards, board_names, mcus) = parse_Board_151(blocks)

			index = arduino_platforms.index(platform)
			boards_platform[index].append(boards)
			board_names_platform[index].append(board_names)
			mcus_platform[index].append(mcus)
			board_files_platform[index].append(board_path)

	Setting.set('boards_platform', boards_platform)
	Setting.set('board_names_platform', board_names_platform)
	Setting.set('mcus_platform', mcus_platform)
	Setting.set('board_files_platform', board_files_platform)
	sublime.save_settings(Setting_File)

## 生成Board菜单 ##
def get_List_Board_Menu():
	parse_Core_Board_Files()
	parse_Ext_Board_Files()
	platforms = Setting.get('arduino_platforms')
	boards_platform = Setting.get('boards_platform')

	text = ''
	index = 0
	menu_index = 0
	display_texts = Setting.get('display_texts')
	for platform in platforms:
		caption = platform.replace('Boards', display_texts['board'])
		text += get_Menu_Text(boards_platform[index], caption, 'list_board', True)
		index += 1
	return text

def  get_List_Processor_Menu():
	processors = Setting.get('processors')
	if processors:
		display_texts = Setting.get('display_texts')
		caption = display_texts['processor']
		text = get_Menu_Text([processors], caption, 'list_processor', True)
	else:
		text = ''
	return text

## 生成Serial Port菜单 ##
def get_Ports():
	display_texts = Setting.get('display_texts')
	refresh_txt = display_texts['refresh']
	ports = [refresh_txt]
	has_ports = False
	if sys.platform == "win32":
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except:
			pass

		if has_ports:
			for i in xrange(20):
				try:
					name,value,type = _winreg.EnumValue(reg,i)
					ports.append(value)
				except:
					pass
	else:
		if sys.platform == 'darwin':
			dev_names = ['tty.usbserial', 'tty.usbmodem']
		else:
			dev_names = ['ttyACM', 'ttyUSB']
		for dev_name in dev_names:
			cmd = 'ls /dev | grep %s' % dev_name
			ports.extend(['/dev/' + f.strip() for f in os.popen(cmd).readlines()]) 
	Setting.set('serial_ports', ports)

def get_List_Serial_Menu():
	get_Ports()
	ports = Setting.get('serial_ports')
	display_texts = Setting.get('display_texts')
	caption = display_texts['serial_port']
	text = get_Menu_Text([ports], caption, 'list_serial', True)
	return text

##　生成Serial Port菜单　##
def get_List_Programmer_Menu():
	programmer_list = []
	programmer_file_list = []
	arduino_core_paths = Setting.get('arduino_core_paths')

	for path in arduino_core_paths:
		programmer_path = os.path.join(path, 'programmers.txt')
		if os.path.exists(programmer_path):
			programmers = []
			programmer_file = open(programmer_path, 'r')
			lines = programmer_file.readlines()
			programmer_file.close()
			blocks = get_Blocks(lines)

			for block in blocks:
				if block:
					programmer = get_Value(block[0])
					programmers.append(programmer)
			if programmers:
				programmer_list.append(programmers)	
				programmer_file_list.append(programmer_path)

	Setting.set('programmers', programmer_list)
	Setting.set('programmer_file', programmer_file_list)

	display_texts = Setting.get('display_texts')
	caption = display_texts['programmer']
	text = get_Menu_Text(programmer_list, caption, 'list_programmer', True)
	return text

def get_List_Example_Menu():
	example_list = []
	example_paths_list = []
	arduino_app_root = Setting.get('arduino_app_root')
	arduino_sketch_root = Setting.get('arduino_sketch_root')
	root_paths = [arduino_app_root, arduino_sketch_root]
	for path in root_paths:
		example_path = os.path.join(path, 'examples')
		if os.path.exists(example_path):
			dirs = list_Dir(example_path, False)
			examples = []
			example_paths =[]
			for d in dirs:
				d_path = os.path.join(example_path, d)
				examples.append(d)
				example_paths.append(d_path)
			example_list.append(examples)
			example_paths_list.append(example_paths)

		lib_path = os.path.join(path, 'libraries')
		if os.path.exists(lib_path):
			examples = []
			example_paths =[]
			dirs = list_Dir(lib_path, False)
			for d in dirs:
				d_path = os.path.join(lib_path, d)
				example_path = os.path.join(d_path, 'examples')
				if os.path.isdir(example_path):
					examples.append(d)
					example_paths.append(example_path)
			example_list.append(examples)
			example_paths_list.append(example_paths)

	display_texts = Setting.get('display_texts')
	caption = display_texts['examples']
	text = get_Menu_Text(example_list, caption, 'list_example')
	Setting.set('example_paths', example_paths_list)
	return text

def get_Arduino_Reference_Url():
	text = 'http://arduino.cc/en/Reference/HomePage'
	arduino_app_root = Setting.get('arduino_app_root')
	ref_path = os.path.join(arduino_app_root, 'reference')
	if os.path.isdir(ref_path):
		ref_path = os.path.join(ref_path, 'index.html')
		ref_path = ref_path.replace(os.path.sep, '/')
		text = ref_path
	return text

def get_Language_Menu():
	languages = Setting.get('languages')
	display_texts = Setting.get('display_texts')
	caption = display_texts['language']
	text = get_Menu_Text([languages], caption, 'list_language', True)
	return text

## 生成菜单 ##
def create_Menu():
	get_lang()
	display_texts = Setting.get('display_texts')
	arduino_app_root = Setting.get('arduino_app_root')
	if arduino_app_root:
		temp_file = 'main_menu'
	else:
		temp_file = 'mini_menu'
	temp_path = os.path.join(TEMPLATE_DIR, temp_file)
	temp_file = open(temp_path, 'r')
	main_menu_txt = temp_file.read()
	temp_file.close()

	language_menu = get_Language_Menu()
	main_menu_txt = main_menu_txt.replace('_list_languages_', language_menu)

	main_menu_txt = main_menu_txt.replace('_building_verbose_', display_texts['building_verbose'])
	main_menu_txt = main_menu_txt.replace('_uploading_verbose_', display_texts['uploading_verbose'])
	main_menu_txt = main_menu_txt.replace('_new_sketch_', display_texts['new_sketch'])
	main_menu_txt = main_menu_txt.replace('_new_file_', display_texts['new_file'])
	main_menu_txt = main_menu_txt.replace('_add_file_', display_texts['add_file'])
	main_menu_txt = main_menu_txt.replace('_show_sketch_folder_', display_texts['show_sketch_folder'])
	main_menu_txt = main_menu_txt.replace('_verify_', display_texts['verify'])
	main_menu_txt = main_menu_txt.replace('_upload_using_programmer_', display_texts['upload_using_programmer'])
	main_menu_txt = main_menu_txt.replace('_upload_', display_texts['upload'])
	main_menu_txt = main_menu_txt.replace('_burn_bootloader_', display_texts['burn_bootloader'])
	main_menu_txt = main_menu_txt.replace('_preferences_', display_texts['preferences'])
	main_menu_txt = main_menu_txt.replace('_set_arduino_path_', display_texts['set_arduino_path'])
	main_menu_txt = main_menu_txt.replace('_reference_', display_texts['reference'])
	main_menu_txt = main_menu_txt.replace('_visit_arduino_', display_texts['visit_arduino'])
	main_menu_txt = main_menu_txt.replace('_about_stino_', display_texts['about_stino'])

	if arduino_app_root:
		sketchbook_menu = get_Sketchbook_Menu()
		import_lib_menu = get_Import_Lib_Menu()
		list_board_menu = get_List_Board_Menu()
		list_processor_menu = get_List_Processor_Menu()
		list_serial_menu = get_List_Serial_Menu()
		list_programmer_menu = get_List_Programmer_Menu()
		list_example_menu = get_List_Example_Menu()
		arduino_reference_url = get_Arduino_Reference_Url()

		main_menu_txt = main_menu_txt.replace('_sketchbook_menu_', sketchbook_menu)
		main_menu_txt = main_menu_txt.replace('_import_lib_menu_', import_lib_menu)
		main_menu_txt = main_menu_txt.replace('_list_board_menu_', list_board_menu)
		main_menu_txt = main_menu_txt.replace('_list_processor_menu_', list_processor_menu)
		main_menu_txt = main_menu_txt.replace('_list_serial_menu_', list_serial_menu)
		main_menu_txt = main_menu_txt.replace('_list_programmer_menu_', list_programmer_menu)
		main_menu_txt = main_menu_txt.replace('_list_example_menu_', list_example_menu)
		main_menu_txt = main_menu_txt.replace('_arduino_reference_url_', arduino_reference_url)

	menu_path = os.path.join(STINO_ROOT, 'Main.sublime-menu')
	write_File(menu_path, main_menu_txt)
	sublime.save_settings(Setting_File)

## 读取信息 ##
def get_Info_Block(blocks, name):
	for block in blocks:
		value = get_Value(block[0])
		if value == name:
			break
	return block

def get_Board_Info_Block_151(block, board_name):
	is_info = True
	info_block = []
	for line in block:
		if '## ' in line:
			if board_name in line:
				is_info = True
			else:
				is_info = False
		if is_info:
			if not '#' in line:
				info_block.append(line)
	return info_block

def read_Board_Info(board_path, board, board_name, processor = ''):
	version = Setting.get('arduino_version')
	lines = read_File(board_path)
	blocks = get_Blocks(lines)

	if version < 1.51:
		block = get_Info_Block(blocks, board_name)
	else:
		block = get_Info_Block(blocks, board)

	if version >= 1.51:
		block = get_Board_Info_Block_151(block, board_name)

	board_info = {}

	for line in block:
		key = get_Key(line)
		value = get_Value(line)

		titles = key.split('.')
		cur_key = titles[-2] + '.' + titles[-1]
		board_info[cur_key] = value
		
	if 'build.vid' in board_info.keys():
		board_info['build.extra_flags'] = board_info['build.extra_flags'].replace('{build.pid}', board_info['build.pid'])
		board_info['build.extra_flags'] = board_info['build.extra_flags'].replace('{build.vid}', board_info['build.vid'])

	Setting.set('board_info', board_info)
	sublime.save_settings(Setting_File)

def read_Programmer_Info(programmer, programmer_path):
	programmer_file = open(programmer_path, 'r')
	lines = programmer_file.readlines()
	programmer_file.close()
	blocks = get_Blocks(lines)
	lines = get_Info_Block(blocks, programmer)

	programmer_info = {}
	programmer_needs_serial = False

	for line in lines:
		key = get_Key(line)
		value = get_Value(line)

		index = key.index('.')
		cur_key = key[(index+1):]
		programmer_info[cur_key] = value

	if 'program.extra_params' in programmer_info.keys():
		if 'speed' in programmer_info.keys():
			programmer_info['program.extra_params'] = programmer_info['program.extra_params'].replace('{program.speed}', programmer_info['speed'])
		if 'serial.port' in programmer_info['program.extra_params']:
			programmer_needs_serial = True

	Setting.set('programmer_info', programmer_info)
	Setting.set('programmer_needs_serial', programmer_needs_serial)
	sublime.save_settings(Setting_File)

## 生成make.def ##
def create_Def_File(file_path, mode = 'all'):
	prj_path = os.path.split(file_path)[0]
	prj_file = os.path.split(file_path)[1]
	prj_name = os.path.splitext(prj_file)[0]

	blank_num = prj_name.count(' ')
	word_count = blank_num + 1

	prj_name = prj_name.replace(' ', '_')

	version_txt = Setting.get('arduino_version_txt')
	arduino_app_root = Setting.get('arduino_app_root')
	arduino_user_root = Setting.get('arduino_user_root')
	platform = Setting.get('platform')
	platforms = Setting.get('arduino_platforms')
	core_paths = Setting.get('arduino_core_paths')
	board_info = Setting.get('board_info', {})
	programmer_info = Setting.get('programmer_info', {})
	serial_port = Setting.get('serial_port', '')
	building_verbose = Setting.get('building_verbose')
	uploading_verbose = Setting.get('uploading_verbose')
	posix_root = Setting.get('posix_root')

# Read platform.txt file
	index = platforms.index(platform)
	core_root = core_paths[index]

	platform_path = os.path.join(core_root, 'platform.txt')
	if not os.path.isfile(platform_path):
		platform_path = os.path.join(TEMPLATE_DIR, 'platform.txt')
	platform_file = open(platform_path, 'r')
	lines = platform_file.readlines()
	platform_file.close()

	compile_info = {}
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			key = get_Key(line)
			value = get_Value(line)
			compile_info[key] = value
	
	CC = compile_info['compiler.c.cmd']
	C_ELF = compile_info['compiler.c.elf.cmd']
	CPP = compile_info['compiler.cpp.cmd']
	AR = compile_info['compiler.ar.cmd']
	OBJCOPY = compile_info['compiler.objcopy.cmd']
	ELF2HEX = compile_info['compiler.elf2hex.cmd']
	SIZE = compile_info['compiler.size.cmd']

	if 'compiler.path' in compile_info.keys():
		gcc_dir = compile_info['compiler.path'].split('/')[-3]
	else:
		gcc_dir = 'avr'
	gcc_root = os.path.join(arduino_app_root, 'hardware/tools/%s/bin' % gcc_dir)
	if sys.platform == 'win32':
		gcc_root = gcc_root.replace('/', os.path.sep)

	if 'AVR' in platform:
		upload_cmd_windows = compile_info['tools.avrdude.cmd.path'].replace('{runtime.ide.path}', arduino_app_root)
		upload_conf_windows = compile_info['tools.avrdude.config.path'].replace('{runtime.ide.path}', arduino_app_root)

		upload_cmd_linux = compile_info['tools.avrdude.cmd.path.linux'].replace('{runtime.ide.path}', arduino_app_root)
		upload_conf_linux = compile_info['tools.avrdude.config.path.linux'].replace('{runtime.ide.path}', arduino_app_root)

		if sys.platform == 'win32':
			upload_cmd = upload_cmd_windows
			upload_conf = upload_conf_windows
		else:
			upload_cmd = upload_cmd_linux
			upload_conf = upload_conf_linux
		uploader_path = os.path.split(upload_cmd)[0]
		upload_cmd = os.path.split(upload_cmd)[1]
		upload_conf = upload_conf.replace(os.path.sep, '/')
	else:
		uploade_cmd = compile_info['tools.bossac.cmd']
		uploader_path = compile_info['tools.bossac.path'].replace('{runtime.ide.path}', arduino_app_root)

#####################################################################
	if sys.platform == 'win32':
		uploader_path = uploader_path.replace('/', os.path.sep)
		text = '@echo off\n'
		text += 'Set Path=%s;%s;%s\n' % (posix_root, gcc_root, uploader_path)
		text += 'make -e -w %s\n' % mode
		bat_path = os.path.join(prj_path, 'build.bat')
		write_File(bat_path, text, ENCODING)
	else:
		gcc_root = gcc_root.replace(' ', '\\ ')
		uploader_path = uploader_path.replace(' ', '\\ ')
		text = '#!/bin/sh\n\n'
		text += 'export PATH=%s:%s:$PATH\n' % (gcc_root, uploader_path)
		text += 'make -e -w %s\n' % mode
		bat_path = os.path.join(prj_path, 'build.sh')
		write_File(bat_path, text, ENCODING)
		cmd = 'chmod +x %s' % bat_path
		os.popen(cmd)
#######################################################################
	platform_dir = os.path.split(core_root)[1]
	core_obj_root = os.path.join(arduino_user_root, platform_dir)
	
	core_root = core_root.replace(os.path.sep, '/')
	core_root = core_root.replace(' ', '\\ ')
	core_obj_root = core_obj_root.replace(os.path.sep, '/')
	core_obj_root = core_obj_root.replace(' ', '\\ ')

	core_source_root = core_root + '/cores/' + board_info['build.core']
	arduino_var_root = core_root + '/variants/' + board_info['build.variant']
	build_system_path = core_root + '/system'

	if 'compiler.libsam.c.flags' in compile_info.keys():
		compile_info['compiler.libsam.c.flags'] = compile_info['compiler.libsam.c.flags'].replace('{build.system.path}', build_system_path)

	if 'AVR' in platform:
		hex_ext = 'hex'
		size_ext = 'hex'
	else:
		hex_ext = 'bin'
		size_ext = 'elf'

	software_name = 'ARDUINO'
	build_path = 'build'
	core_lib_name = 'core.a'

	ext_lib_paths = Setting.get('libraries')
	include_paths = [core_source_root, arduino_var_root]
	for paths in ext_lib_paths:
		include_paths.extend(paths)
	includes = ''
	index = 0
	for path in include_paths:
		if index >= 2:
			path = path.replace(os.path.sep, '/')
			path = path.replace(' ', '\\ ')
		includes += '-I%s ' % path
		index += 1

	if not 'build.extra_flags' in board_info.keys():
		board_info['build.extra_flags'] = ''

	if not 'build.ldscript' in board_info.keys():
		board_info['build.ldscript'] = ''

	if not 'compiler.libsam.c.flags' in compile_info.keys():
		compile_info['compiler.libsam.c.flags'] = ''

	C_FLAGS = compile_info['recipe.c.o.pattern'].replace('"{compiler.path}{compiler.c.cmd}" ', '')
	C_FLAGS = C_FLAGS.replace('{compiler.c.flags}', compile_info['compiler.c.flags'])
	C_FLAGS = C_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
	C_FLAGS = C_FLAGS.replace('{build.f_cpu}', board_info['build.f_cpu'])
	C_FLAGS = C_FLAGS.replace('{software}', software_name)
	C_FLAGS = C_FLAGS.replace('{runtime.ide.version}', version_txt)
	C_FLAGS = C_FLAGS.replace('{build.extra_flags}', board_info['build.extra_flags'])
	C_FLAGS = C_FLAGS.replace('{compiler.libsam.c.flags}', compile_info['compiler.libsam.c.flags'])
	C_FLAGS = C_FLAGS.replace('{includes}', includes)
	C_FLAGS = C_FLAGS.replace(' "{source_file}" -o "{object_file}"', '')
	C_FLAGS = C_FLAGS.replace('"', '')

	CPP_FLAGS = compile_info['recipe.cpp.o.pattern'].replace('"{compiler.path}{compiler.cpp.cmd}" ', '')
	CPP_FLAGS = CPP_FLAGS.replace('{compiler.cpp.flags}', compile_info['compiler.cpp.flags'])
	CPP_FLAGS = CPP_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
	CPP_FLAGS = CPP_FLAGS.replace('{build.f_cpu}', board_info['build.f_cpu'])
	CPP_FLAGS = CPP_FLAGS.replace('{software}', software_name)
	CPP_FLAGS = CPP_FLAGS.replace('{runtime.ide.version}', version_txt)
	CPP_FLAGS = CPP_FLAGS.replace('{build.extra_flags}', board_info['build.extra_flags'])
	CPP_FLAGS = CPP_FLAGS.replace('{compiler.libsam.c.flags}', compile_info['compiler.libsam.c.flags'])
	CPP_FLAGS = CPP_FLAGS.replace('{includes}', includes)
	CPP_FLAGS = CPP_FLAGS.replace(' "{source_file}" -o "{object_file}"', '')
	CPP_FLAGS = CPP_FLAGS.replace('"', '')

	AR_FLAGS = compile_info['recipe.ar.pattern'].replace('"{compiler.path}{compiler.ar.cmd}" ', '')
	AR_FLAGS = AR_FLAGS.replace('{compiler.ar.flags}', compile_info['compiler.ar.flags'])
	AR_FLAGS = AR_FLAGS.replace(' "{build.path}/{archive_file}" "{object_file}"', '')

	C_COMBINE_FLAGS = compile_info['recipe.c.combine.pattern'].replace('"{compiler.path}{compiler.c.elf.cmd}" ', '')
	C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{compiler.c.elf.flags}', compile_info['compiler.c.elf.flags'])
	C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
	if board_info['build.ldscript']:
		C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{build.variant.path}', arduino_var_root)
		C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{build.ldscript}', board_info['build.ldscript'])
		C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{build.variant_system_lib}', board_info['build.variant_system_lib'])
	else:
		C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('-T{build.variant.path}/{build.ldscript}', '')
		C_COMBINE_FLAGS = C_COMBINE_FLAGS.replace('{build.variant.path}/{build.variant_system_lib}', '')

	OBJCOPY_EEP_FLAGS = compile_info['recipe.objcopy.eep.pattern'].replace('"{compiler.path}{compiler.objcopy.cmd}" ', '')
	OBJCOPY_EEP_FLAGS = OBJCOPY_EEP_FLAGS.replace('{compiler.objcopy.eep.flags}', compile_info['compiler.objcopy.eep.flags'])
	OBJCOPY_EEP_FLAGS = OBJCOPY_EEP_FLAGS.replace(' "{build.path}/{build.project_name}.elf" "{build.path}/{build.project_name}.eep"', '')

	OBJCOPY_HEX_FLAGS = compile_info['recipe.objcopy.hex.pattern'].replace('"{compiler.path}{compiler.elf2hex.cmd}" ', '')
	OBJCOPY_HEX_FLAGS = OBJCOPY_HEX_FLAGS.replace('{compiler.elf2hex.flags}', compile_info['compiler.elf2hex.flags'])
	OBJCOPY_HEX_FLAGS = OBJCOPY_HEX_FLAGS.replace(' "{build.path}/{build.project_name}.elf" "{build.path}/{build.project_name}.%s"' % hex_ext, '')

	SIZE_FLAGS = compile_info['recipe.size.pattern'].replace('"{compiler.path}{compiler.size.cmd}" ', '')
	SIZE_FLAGS = SIZE_FLAGS.replace(' "{build.path}/{build.project_name}.%s"' % size_ext, '')

	C_COMBINE_FLAGS_sections = C_COMBINE_FLAGS.split('-o "{build.path}/{build.project_name}.elf"')
	C_COMBINE_FLAGS1 = C_COMBINE_FLAGS_sections[0]
	C_COMBINE_FLAGS_sections = C_COMBINE_FLAGS_sections[1].split('{object_files}')
	C_COMBINE_FLAGS2 = C_COMBINE_FLAGS_sections[0]
	C_COMBINE_FLAGS_sections = C_COMBINE_FLAGS_sections[1].split('"{build.path}/{archive_file}"')
	C_COMBINE_FLAGS3 = C_COMBINE_FLAGS_sections[0]
	C_COMBINE_FLAGS4 = C_COMBINE_FLAGS_sections[1]

	C_COMBINE_FLAGS1 = C_COMBINE_FLAGS1.replace('{build.path}', build_path)
	C_COMBINE_FLAGS1 = C_COMBINE_FLAGS1.replace('{build.project_name}', prj_name)
	C_COMBINE_FLAGS2 = C_COMBINE_FLAGS2.replace('{build.path}', core_obj_root)
	C_COMBINE_FLAGS4 = C_COMBINE_FLAGS4.replace('{build.path}', core_obj_root)
	C_COMBINE_FLAGS1 = C_COMBINE_FLAGS1.replace('"', '')
	C_COMBINE_FLAGS2 = C_COMBINE_FLAGS2.replace('"', '')
	C_COMBINE_FLAGS3 = C_COMBINE_FLAGS3.replace('"', '')
	C_COMBINE_FLAGS4 = C_COMBINE_FLAGS4.replace('"', '')

	if 'AVR' in platform:
		if uploading_verbose:
			upload_verb = compile_info['tools.avrdude.upload.params.verbose']
		else:
			upload_verb = compile_info['tools.avrdude.upload.params.quiet']

		UPLOAD_FLAGS = compile_info['tools.avrdude.upload.pattern'].replace('"{cmd.path}" ', '')
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{config.path}', upload_conf)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{upload.verbose}', upload_verb)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{upload.protocol}', board_info['upload.protocol'])
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{serial.port}', serial_port)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{upload.speed}', board_info['upload.speed'])
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{build.path}', build_path)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{build.project_name}', prj_name)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('"', '')

		if programmer_info:
			if 'program.extra_params' in programmer_info.keys():
				programmer_info['program.extra_params'] = programmer_info['program.extra_params'].replace('{serial.port}', serial_port)
			else:
				programmer_info['program.extra_params'] = ''
			
			PROGRAM_FLAGS = compile_info['tools.avrdude.program.pattern'].replace('"{cmd.path}" ', '')
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{config.path}', upload_conf)
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{program.verbose}', upload_verb)
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{protocol}', programmer_info['protocol'])
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{program.extra_params}', programmer_info['program.extra_params'])
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{build.path}', build_path)
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('{build.project_name}', prj_name)
			PROGRAM_FLAGS = PROGRAM_FLAGS.replace('"', '')

			ERASE_FLAGS = compile_info['tools.avrdude.erase.pattern'].replace('"{cmd.path}" ', '')
			ERASE_FLAGS = ERASE_FLAGS.replace('{config.path}', upload_conf)
			ERASE_FLAGS = ERASE_FLAGS.replace('{erase.verbose}', upload_verb)
			ERASE_FLAGS = ERASE_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{protocol}', programmer_info['protocol'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{program.extra_params}', programmer_info['program.extra_params'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{bootloader.unlock_bits}', board_info['bootloader.unlock_bits'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{bootloader.extended_fuses}', board_info['bootloader.extended_fuses'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{bootloader.high_fuses}', board_info['bootloader.high_fuses'])
			ERASE_FLAGS = ERASE_FLAGS.replace('{bootloader.low_fuses}', board_info['bootloader.low_fuses'])
			ERASE_FLAGS = ERASE_FLAGS.replace('"', '')

			BOOTLOADER_FLAGS = compile_info['tools.avrdude.bootloader.pattern'].replace('"{cmd.path}" ', '')
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{config.path}', upload_conf)
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{bootloader.verbose}', upload_verb)
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{build.mcu}', board_info['build.mcu'])
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{protocol}', programmer_info['protocol'])
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{program.extra_params}', programmer_info['program.extra_params'])
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{runtime.ide.path}', arduino_app_root)
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{bootloader.file}', board_info['bootloader.file'])
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('{bootloader.lock_bits}', board_info['bootloader.lock_bits'])
			BOOTLOADER_FLAGS = BOOTLOADER_FLAGS.replace('"', '')
		else:
			PROGRAM_FLAGS = ''
			ERASE_FLAGS = ''
			BOOTLOADER_FLAGS = ''
	else:
		if uploading_verbose:
			upload_verb = compile_info['tools.bossac.upload.params.verbose']
		else:
			upload_verb = compile_info['tools.bossac.upload.params.quiet']

		UPLOAD_FLAGS = compile_info['tools.bossac.upload.pattern'].replace('"{path}/{cmd}" ', '')
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{upload.verbose}', compile_info['tools.bossac.upload.params.verbose'])
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{serial.port.file}', serial_port)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{upload.native_usb}', board_info['upload.native_usb'])
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{build.path}', build_path)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('{build.project_name}', prj_name)
		UPLOAD_FLAGS = UPLOAD_FLAGS.replace('"', '')
		PROGRAM_FLAGS = ''
		ERASE_FLAGS = ''
		BOOTLOADER_FLAGS = ''

	if building_verbose:
		build_verb = ''
	else:
		build_verb = '@'

	text = ''
	text += ('BUILDING_VERBOSE := %s\n') % build_verb
	text += ('PRJ_NAME := %s\n') % prj_name
	text += ('COUNT := %d\n') % word_count
	text += ('CORE_LIB_NAME := %s\n') % core_lib_name
	text += ('CORE_SOURCE_ROOT := %s\n') % core_source_root
	text += ('CORE_OBJ_ROOT := %s\n\n') % core_obj_root

	text += ('CC := %s\n') % CC
	text += ('CELF := %s\n') % C_ELF
	text += ('CPP := %s\n') % CPP
	text += ('AR := %s\n') % AR
	text += ('OBJCOPY := %s\n') % OBJCOPY
	text += ('ELF2HEX := %s\n') % ELF2HEX
	text += ('SIZE := %s\n\n') % SIZE

	text += ('C_FLAGS := %s\n') % C_FLAGS
	text += ('S_FLAGS := %s\n') % compile_info['compiler.S.flags']
	text += ('CPP_FLAGS := %s\n') % CPP_FLAGS
	text += ('AR_FLAGS := %s\n') % AR_FLAGS
	text += ('C_COMBINE_FLAGS1 := %s\n') % C_COMBINE_FLAGS1
	text += ('C_COMBINE_FLAGS2 := %s\n') % C_COMBINE_FLAGS2
	text += ('C_COMBINE_FLAGS3 := %s\n') % C_COMBINE_FLAGS3
	text += ('C_COMBINE_FLAGS4 := %s\n') % C_COMBINE_FLAGS4
	text += ('OBJCOPY_EEP_FLAGS := %s\n') % OBJCOPY_EEP_FLAGS
	text += ('OBJCOPY_HEX_FLAGS := %s\n') % OBJCOPY_HEX_FLAGS
	text += ('SIZE_FLAGS := %s\n') % SIZE_FLAGS

	text += ('MAX_SIZE := %s\n') % board_info['upload.maximum_size']
	text += ('HEX_EXT := %s\n') % hex_ext
	text += ('SIZE_EXT := %s\n\n') % size_ext

	text += ('UPLOADER := %s\n') % upload_cmd
	text += ('UPLOAD_FLAGS := %s\n') % UPLOAD_FLAGS
	if 'AVR' in platform:
		text += ('PROGRAM_FLAGS := %s\n') % PROGRAM_FLAGS
		text += ('ERASE_FLAGS := %s\n') % ERASE_FLAGS
		text += ('BOOTLOADER_FLAGS := %s\n') % BOOTLOADER_FLAGS

	makefile_path = os.path.join(TEMPLATE_DIR, 'Makefile')
	f = open(makefile_path, 'r')
	text += f.read().decode('utf-8')
	f.close()

	def_name = 'Makefile'
	def_path = os.path.join(prj_path, def_name)
	write_File(def_path, text, ENCODING)
		
def create_Build_File():
	build_file_name = 'Arduino.sublime-build'
	build_file_path = os.path.join(TEMPLATE_DIR, 'sublime_build')
	build_file = open(build_file_path, 'r')
	text = build_file.read()
	build_file.close()

	if sys.platform == 'win32':
		cmd = '"build.bat"'
	else:
		cmd = '"./build.sh"'

	text = text.replace('_cmd_', cmd)
	build_file_path = os.path.join(STINO_ROOT, build_file_name)
	write_File(build_file_path, text)
	return build_file_path

########## Commands ##########
def get_Subpath_List(path, with_files = True, with_parent = True):
	subpath_list = []
	path = os.path.normpath(path)
	files = list_Dir(path, with_files)
	if with_parent:
		files.insert(0, '..')

	for f in files:
		f_path = os.path.join(path, f)
		subpath_list.append(f_path)
	return subpath_list

def get_File_List(path_list):
	file_list = []
	for path in path_list:
		file_name = os.path.split(path)[1]
		if not file_name:
			file_name = path
		file_list.append(file_name)
	return file_list

def enter_Next(index, level, top_path_list, path, with_files = True, with_parent = True):
	if level > 0:
		if index == 0:
			level -= 1
		else:
			level += 1
	else:
		level += 1
	
	if level == 0:
		path_list = top_path_list
	else:
		path_list = get_Subpath_List(path, with_files, with_parent)
	return (level, path_list)

class SetArduinoAppRootCommand(sublime_plugin.WindowCommand):
	""" Get Arduino Path """
	def run(self):
		self.path_list = []
		self.level = 0
		if sys.platform == 'win32':
			self.path_list = get_Win_Vol()
		else:
			Home_Root = os.getenv('HOME')
			if sys.platform == 'darwin':
				self.path_list = get_Subpath_List(Home_Root, False, False)
			else:
				self.path_list = [Home_Root, '/usr/share', '/opt']
		self.top_path_list = self.path_list
		file_list = get_File_List(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if is_Arduino_App_Root(sel_path):
			display_texts = Setting.get('display_texts')
			ver_display_txt = display_texts['version']
			version = Setting.get('arduino_version_txt')
			sublime.message_dialog("Arduino: %s\n%s: %s" 
				% (sel_path, ver_display_txt, version))
			clean_selection()
			create_Menu()
			return
		
		(self.level, self.path_list) = enter_Next(index, self.level, self.top_path_list, sel_path, False)
		file_list = get_File_List(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

class ListLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		language = menu_str
		Setting.set('language', language)
		create_Menu()

	def is_checked(self, menu_str):
		state = False
		language = Setting.get('language')
		if menu_str == language:
			state = True
		return state

class NewSketchCommand(sublime_plugin.WindowCommand):
	""" Create new sketch file from template """
	def run(self):
		display_texts = Setting.get('display_texts')
		txt = display_texts['new_sketch_input']
		self.window.show_input_panel(txt, '', self.on_done, None, self.on_cancel)

	def on_done(self, input_text):
		arduino_sketch_root = Setting.get('arduino_sketch_root')
		is_new = True
		sketch_name = input_text
		if sketch_name:
			if sketch_name[0] in '0123456789':
				sketch_name = '_' + sketch_name
			sketch_name = sketch_name.replace(' ', '_')
			sketch_folder_path = os.path.join(arduino_sketch_root, sketch_name)
			if os.path.exists(sketch_folder_path):
				display_texts = Setting.get('display_texts')
				msg = display_texts['error_msg_2'].replace('_sketch_name', sketch_name)
				is_new = sublime.ok_cancel_dialog(msg)
		else:
			is_new = False

		if is_new:
			if not os.path.exists(sketch_folder_path):
				os.mkdir(sketch_folder_path)
			sketch_file_name = '%s.ino' % sketch_name
			sketch_file_path = os.path.join(sketch_folder_path, sketch_file_name)

			# Write Sketch File
			temp_path = os.path.join(TEMPLATE_DIR, 'sketch')
			temp_file = open(temp_path, 'r')
			sketch = temp_file.read()
			temp_file.close()

			write_File(sketch_file_path, sketch)
			create_Menu()

			#open a new window for new project
			open_Sketch(sketch_folder_path)	
		else:
			display_texts = Setting.get('display_texts')
			txt = display_texts['new_sketch_input']
			self.window.show_input_panel(txt, '', self.on_done, None, self.on_cancel)
	
	def on_cancel(self):
		pass

class ListSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		arduino_sketch_root = Setting.get('arduino_sketch_root')
		sketch_path = os.path.join(arduino_sketch_root, menu_str)
		open_Sketch(sketch_path)

class NewToSketch(sublime_plugin.WindowCommand):
	def run(self):
		display_texts = Setting.get('display_texts')
		txt = display_texts['new_file_input']
		self.window.show_input_panel(txt, '', self.on_done, None, self.on_cancel)

	def on_done(self, input_text):
		is_new = True
		file_name = input_text
		if file_name:
			file_name = file_name.replace(' ', '_')
			active_file = self.window.active_view().file_name()
			sketch_path = os.path.split(active_file)[0]
			file_path = os.path.join(sketch_path, file_name)
			ext = os.path.splitext(file_path)[1]
			for arduino_ext in Arduino_Ext:
				if ext == arduino_ext:
					ext = '.cpp'
					file_path = os.path.splitext(file_path)[0] + ext
					break
			if os.path.exists(file_path):
				display_texts = Setting.get('display_texts')
				msg = display_texts['error_msg_1']
				sublime.message_dialog('%s' % msg)
				is_new = False
		else:
			is_new = False

		if is_new:
			text = '// %s\n\n' % file_name
			write_File(file_path, text)
			view = self.window.open_file(file_path)
			view.set_syntax_file('Packages/C++/C++.tmLanguage')
		else:
			display_texts = Setting.get('display_texts')
			txt = display_texts['new_file_input']
			self.window.show_input_panel(txt, '', self.on_done, None, self.on_cancel)
			
	def on_cancel(self):
		pass

	def is_enabled(self):
		state = False
		active_file = self.window.active_view().file_name()
		if active_file:
			d = os.path.split(active_file)[0]
			if not 'examples' in d:
				ext = os.path.splitext(active_file)[1]
				for arduino_ext in Arduino_Ext:
					if ext == arduino_ext:
						state = True
		return state

class AddToSketch(sublime_plugin.WindowCommand):
	def run(self):
		self.path_list = []
		self.level = 0
		if sys.platform == 'win32':
			self.path_list = get_Win_Vol()
		else:
			home_root = os.getenv('HOME')
			if sys.platform == 'darwin':
				self.path_list = get_Subpath_List(home_root, True, False)
			else:
				arduino_app_root = Setting.get('arduino_app_root')
				self.path_list = [home_root, arduino_app_root]
		self.top_path_list = self.path_list
		file_list = get_File_List(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			sel_dir_path = os.path.split(sel_path)[0]
			sel_file_name = os.path.split(sel_path)[1]
			sel_file_noext = os.path.splitext(sel_file_name)[0]
			sel_file_ext = os.path.splitext(sel_file_name)[1]
			sel_file_noext = sel_file_noext.replace(' ', '_')

			for arduino_ext in Arduino_Ext:
				if sel_file_ext == arduino_ext:
					sel_file_ext = '.cpp'
					sel_file_name = sel_file_noext + sel_file_ext
					break

			sketch_path = self.window.active_view().file_name()
			sketch_dir_path = os.path.split(sketch_path)[0]
			f_path = os.path.join(sketch_dir_path, sel_file_name)

			files = list_Dir(sketch_dir_path)
			is_file = False
			for f in files:
				if(f == sel_file_name):
					is_file = True
					break
			seq = 1
			while is_file:
				name = '%s(%d)%s' % (sel_file_noext, seq, sel_file_ext)
				is_done = True
				for f in files:
					if f == name:
						seq += 1
						is_file = True
						is_done = False
						break
				if is_done:
					is_file = False
					f_path = os.path.join(sketch_dir_path, name)
			
			f = open(sel_path, 'r')
			text = f.read()
			f.close()
			write_File(f_path, text)
			view = self.window.open_file(f_path)
		else:		
			(self.level, self.path_list) = enter_Next(index, self.level, self.top_path_list, sel_path)
			file_list = get_File_List(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

	def is_enabled(self):
		state = False
		active_file = self.window.active_view().file_name()
		if active_file:
			d = os.path.split(active_file)[0]
			if not 'examples' in d:
				ext = os.path.splitext(active_file)[1]
				for arduino_ext in Arduino_Ext:
					if ext == arduino_ext:
						state = True
		return state

class ImportLibCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		libs = Setting.get('libraries')
		index1 = 0
		go_out = False
		for lib in libs:
			index2 = 0
			for lib_item in lib:
				if menu_str in lib_item:
					go_out = True
					break
				index2 += 1
			if go_out:
				break
			index1 += 1
		lib_path = libs[index1][index2]
		headers = []
		files = list_Dir(lib_path)
		for f in files:
			ext = os.path.splitext(f)[1]
			if ext == '.h':
				headers.append(f)
		edit = self.window.active_view().begin_edit()
		pos_txt = 0
		for header in headers:
			text = '#include "%s"\n' % header
			len_txt = self.window.active_view().insert(edit, pos_txt, text)
			pos_txt += len_txt
		self.window.active_view().insert(edit, pos_txt, '\n')
		self.window.active_view().end_edit(edit)

class OpenSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		active_file = self.window.active_view().file_name()
		sketch_path = os.path.split(active_file)[0]
		self.level = 0
		self.top_path_list = get_Subpath_List(sketch_path, True, False)
		self.path_list = self.top_path_list
		file_list = get_File_List(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			view = self.window.open_file(sel_path)
			view.set_syntax_file('Packages/C++/C++.tmLanguage')
		else:		
			(self.level, self.path_list) = enter_Next(index, self.level, self.top_path_list, sel_path)
			file_list = get_File_List(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

	def is_enabled(self):
		state = False
		active_file = self.window.active_view().file_name()
		if active_file:
			ext = os.path.splitext(active_file)[1]
			for arduino_ext in Arduino_Ext:
				if ext == arduino_ext:
					state = True
		return state

class VerifySketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		cur_file = self.window.active_view().file_name()
		create_Def_File(cur_file)
		build_file_path = create_Build_File()
		self.window.run_command('set_build_system', {'file': build_file_path})
		self.window.run_command('build')

	def is_enabled(self):
		state = False
		board = Setting.get('board_name')
		file_path = self.window.active_view().file_name()
		ext = os.path.splitext(file_path)[1]
		if board:
			for arduino_ext in Arduino_Ext:
				if ext == arduino_ext:
					state = True
		return state

class UploadHexCommand(sublime_plugin.WindowCommand):
	def run(self):
		state = True
		platform = Setting.get('platform', '')
		if 'AVR' in platform:
			get_Ports()
			serial_ports = Setting.get('serial_ports')
			if len(serial_ports) < 1:
				state = False	
		if state:
			cur_file = self.window.active_view().file_name()
			create_Def_File(cur_file, 'upload')
			build_file_path = create_Build_File()
			self.window.run_command('set_build_system', {'file': build_file_path})
			self.window.run_command('build')
		else:
			display_texts = Setting.get('display_texts')
			msg = display_texts['error_msg_3']
			sublime.message_dialog('%s' % msg)

	def is_enabled(self):
		platform = Setting.get('platform', '')
		state = False
		serial_port = Setting.get('serial_port')
		serial_ports = Setting.get('serial_ports')
		if serial_port and (len(serial_ports) > 1):
			has_serial = True
		else:
			has_serial = False
		board = Setting.get('board_name')
		file_path = self.window.active_view().file_name()
		ext = os.path.splitext(file_path)[1]
		if board:
			for arduino_ext in Arduino_Ext:
				if ext == arduino_ext:
					state = True
		if 'AVR' in platform:
			if not has_serial:
				state = False
		return state

class UploadByProgrmmerCommand(sublime_plugin.WindowCommand):
	def run(self):
		cur_file = self.window.active_view().file_name()
		create_Def_File(cur_file, 'upload_by_programmer')
		build_file_path = create_Build_File()
		self.window.run_command('set_build_system', {'file': build_file_path})
		self.window.run_command('build')

	def is_enabled(self):
		state = False
		serial_port = Setting.get('serial_port')
		serial_ports = Setting.get('serial_ports')
		if serial_port and (len(serial_ports) > 1):
			has_serial = True
		else:
			has_serial = False
		platform = Setting.get('platform', '')
		if 'AVR' in platform:
			board = Setting.get('board_name')
			programmer = Setting.get('programmer')
			file_path = self.window.active_view().file_name()
			ext = os.path.splitext(file_path)[1]
			if board and programmer:
				for arduino_ext in Arduino_Ext:
					if ext == arduino_ext:
						state = True
				programmer_needs_serial = Setting.get('programmer_needs_serial')
				if programmer_needs_serial:
					if not has_serial:
						state = False
		return state

class ListBoardCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		platforms = Setting.get('arduino_platforms', '')
		boards_platform = Setting.get('boards_platform', '')
		board_names_platform = Setting.get('board_names_platform', '')
		board_files_platform = Setting.get('board_files_platform', '')
		mcus_platform = Setting.get('mcus_platform')
		board = menu_str
		
		go_out = False
		index1 = 0
		for boards_each_platform in boards_platform:
			index2 = 0
			for boards in boards_each_platform:
				if board in boards:
					index3 = boards.index(board)
					go_out = True
					break
				index2 += 1
			if go_out:
				break
			index1 += 1
		processors = mcus_platform[index1][index2][index3]
		board_file = board_files_platform[index1][index2]
		platform = platforms[index1]

		processor = ''
		board_name = ''
		processor_names = []
		if len(processors) == 0:
			board_name = board
			has_processor = False
		else:
			has_processor = True
			processor_names = board_names_platform[index1][index2][index3]

		Setting.set('board', board)
		Setting.set('board_file', board_file)
		Setting.set('board_name', board_name)
		Setting.set('processor_names', processor_names)
		Setting.set('platform', platform)
		Setting.set('processors', processors)
		Setting.set('has_processor', has_processor)
		Setting.set('processor', processor)
		sublime.save_settings(Setting_File)
		create_Menu()

		if not has_processor:
			read_Board_Info(board_file, board, board_name)

	def is_checked(self, menu_str):
		state = False
		board = Setting.get('board')
		if menu_str == board:
			state = True
		return state

class ListProcessorCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		processor = menu_str
		board = Setting.get('board')
		processors = Setting.get('processors')
		processor_names = Setting.get('processor_names')
		board_file = Setting.get('board_file')
		index = processors.index(processor)
		board_name = processor_names[index]
		Setting.set('processor', processor)
		Setting.set('board_name', board_name)
		sublime.save_settings(Setting_File)
		read_Board_Info(board_file, board, board_name, processor)

	def is_checked(self, menu_str):
		state = False
		processor = Setting.get('processor', '')
		if menu_str == processor:
			state = True
		return state

class ListSerialCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		display_texts = Setting.get('display_texts')
		refresh_txt = display_texts['refresh']
		if menu_str == refresh_txt:
			create_Menu()
		else:
			port = menu_str
			Setting.set('serial_port', port)
			sublime.save_settings(Setting_File)

	def is_checked(self, menu_str):
		state = False
		port = Setting.get('serial_port')
		if menu_str == port:
			state = True
		return state

	def is_visible(self, menu_str):
		state = False
		get_Ports()
		ports = Setting.get('serial_ports')
		if menu_str in ports:
			state = True
		return state

class ListProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		programmer = menu_str
		programmer_list = Setting.get('programmers')
		programmer_file_list = Setting.get('programmer_file')

		index = 0
		for programmers in programmer_list:
			if programmer in programmers:
				break
			index += 1
		programmer_file = programmer_file_list[index]

		Setting.set('programmer', programmer)
		sublime.save_settings(Setting_File)
		read_Programmer_Info(programmer, programmer_file)

	def is_checked(self, menu_str):
		state = False
		programmer = Setting.get('programmer')
		if menu_str == programmer:
			state = True
		return state

class BurnBootloaderCommand(sublime_plugin.WindowCommand):
	def run(self):
		cur_file = self.window.active_view().file_name()
		create_Def_File(cur_file, 'burn_bootloader')
		build_file_path = create_Build_File()
		self.window.run_command('set_build_system', {'file': build_file_path})
		self.window.run_command('build')

	def is_enabled(self):
		state = False
		platform = Setting.get('platform', '')
		serial_port = Setting.get('serial_port')
		serial_ports = Setting.get('serial_ports')
		if serial_port and (len(serial_ports) > 1):
			has_serial = True
		else:
			has_serial = False
		if 'AVR' in platform:
			board = Setting.get('board_name')
			programmer = Setting.get('programmer')
			if board and programmer:
				state = True
				programmer_needs_serial = Setting.get('programmer_needs_serial')
				if programmer_needs_serial:
					if not has_serial:
						state = False
		return state

class ListExample(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		example = menu_str
		example_paths = Setting.get('example_paths')
		index1 = 0
		go_out = False
		for paths in example_paths:
			index2 = 0
			for path in paths:
				if example in path:
					go_out = True
					break
				index2 += 1
			if go_out:
				break
			index1 += 1
		example_path = example_paths[index1][index2]
		self.level = 0
		self.top_path_list = get_Subpath_List(example_path, True, False)
		self.path_list = self.top_path_list
		file_list = get_File_List(self.path_list)
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			view = self.window.open_file(sel_path)
			view.set_syntax_file('Packages/C++/C++.tmLanguage')
		else:		
			(self.level, self.path_list) = enter_Next(index, self.level, self.top_path_list, sel_path)
			file_list = get_File_List(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class SetBuildingVerbose(sublime_plugin.WindowCommand):
	def run(self):
		building_verbose = Setting.get('building_verbose')
		building_verbose = not building_verbose
		Setting.set('building_verbose', building_verbose)
		sublime.save_settings(Setting_File)

	def is_checked(self):
		state = False
		building_verbose = Setting.get('building_verbose')
		if building_verbose:
			state = True
		return state

class SetUploadingVerbose(sublime_plugin.WindowCommand):
	def run(self):
		uploading_verbose = Setting.get('uploading_verbose')
		uploading_verbose = not uploading_verbose
		Setting.set('uploading_verbose', uploading_verbose)
		sublime.save_settings(Setting_File)

	def is_checked(self):
		state = False
		uploading_verbose = Setting.get('uploading_verbose')
		if uploading_verbose:
			state = True
		return state

class AboutStino(sublime_plugin.WindowCommand):
	def run(self):
		readme_path = os.path.join(STINO_ROOT, 'readme.txt')
		try:
			f = open(readme_path, 'r')
			text = f.read()
			f.close()
			encoding = detect_Encoding(text)
			if encoding != 'ascii':
				text = text.decode(encoding)
		except:
			text = 'Stino\nVersion: 1.0b1\n\nA Sublime Text 2 Plugin for Arduino\nCopyright (C) 2012 Robot.Will <robot.will.me AT gmail.com>.'
		sublime.message_dialog(text)

class NotEnableCommand(sublime_plugin.WindowCommand):
	def run(self):
		sublime.message_dialog('Just Kidding! :)')

	def is_enabled(self):
		return False

########## Initiation ##########
get_lang()
get_Arduino_User_Root()
get_Arduino_Sketch_Root()
check_Arduino_App_Root()
create_Menu()
########## End ##########