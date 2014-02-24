#-*- coding: utf-8 -*-
# stino/compiler.py

import os
import re
import threading
import subprocess

import sublime

from . import fileutil
from . import textutil
from . import constant
from . import serial
from . import base
from . import preprocess
from . import sketch
from . import console

ram_size_dict = {}
ram_size_dict['attiny44'] = '256'
ram_size_dict['attiny45'] = '256'
ram_size_dict['attiny84'] = '512'
ram_size_dict['attiny85'] = '512'
ram_size_dict['atmega8'] = '1024'
ram_size_dict['atmega168'] = '1024'
ram_size_dict['atmega328p'] = '2048'
ram_size_dict['atmega644'] = '4096'
ram_size_dict['atmega644p'] = '4096'
ram_size_dict['atmega1284'] = '16384'
ram_size_dict['atmega1284p'] = '16384'
ram_size_dict['atmega1280'] = '4096'
ram_size_dict['atmega2560'] = '8196'
ram_size_dict['atmega32u4'] = '2560'
ram_size_dict['at90usb162'] = '512'
ram_size_dict['at90usb646'] = '4096'
ram_size_dict['at90usb1286'] = '8192'
ram_size_dict['cortex-m3'] = '98304'
ram_size_dict['cortex-m4'] = '16384'

class Args:
	def __init__(self, cur_project, arduino_info):
		self.args = getFullArgs(cur_project, arduino_info)

	def getArgs(self):
		return self.args

class Command:
	def __init__(self, command):
		self.in_file = ''
		self.out_file = ''
		self.command = command
		self.calc_size = False
		self.stdout = ''
		self.out_text = ''

	def run(self, output_console):
		output_console.printText(self.out_text)
		if self.out_file:
			message = 'Creating %s...\n' % self.out_file
			output_console.printText(message)

		cur_command = formatCommand(self.command)
		compile_proc = subprocess.Popen(cur_command, stdout = subprocess.PIPE,
			stderr = subprocess.PIPE, shell = True)
		result = compile_proc.communicate()
		return_code = compile_proc.returncode
		stdout = result[0].decode(constant.sys_encoding).replace('\r', '')
		stderr = result[1].decode(constant.sys_encoding).replace('\r', '')
		self.stdout = stdout

		show_compilation_output = constant.sketch_settings.get('show_compilation_output', False)
		if show_compilation_output:
			output_console.printText(self.command)
			output_console.printText('\n')
			output_console.printText(stdout)
		output_console.printText(stderr)
		return return_code

	def isSizeCommand(self):
		return self.calc_size

	def setSizeCommand(self):
		self.calc_size = True

	def getOutFile(self):
		return self.out_file

	def getCommand(self):
		return self.command

	def getStdout(self):
		return self.stdout

	def setInFile(self, in_file):
		self.in_file = in_file

	def setOutFile(self, out_file):
		self.out_file = out_file

	def setCommand(self, command):
		self.command = command

	def setOutputText(self, text):
		self.out_text = text

class Compiler:
	def __init__(self, arduino_info, cur_project, args):
		self.arduino_info = arduino_info
		self.cur_project = cur_project
		self.args = args.getArgs()
		self.output_console = console.Console(cur_project.getName())
		self.no_error = True
		self.is_finished = False
		self.prepare()

	def getOutputConsole(self):
		return self.output_console

	def isFinished(self):
		return self.is_finished

	def noError(self):
		return self.no_error

	def prepare(self):
		self.command_list = []
		if self.args:
			self.command_list = genCommandList(self.args, self.cur_project, self.arduino_info)

	def run(self):
		if self.command_list:
			compilation_thread = threading.Thread(target=self.compile)
			compilation_thread.start()
		else:
			self.no_error = False
			self.is_finished = True
			self.output_console.printText('Please choose the Ardunio Application Folder.')

	def compile(self):
		self.output_console.printText('Compiling %s...\n' % self.cur_project.getName())
		for cur_command in self.command_list:
			return_code = cur_command.run(self.output_console)
			if return_code > 0:
				self.output_console.printText('[Stino - Error %d]\n' % return_code)
				self.no_error = False
				break
			else:
				if cur_command.isSizeCommand():
					stdout = cur_command.getStdout()
					printSizeInfo(self.output_console, stdout, self.args)
		if self.no_error:
			self.output_console.printText('[Stino - Done compiling.]\n')
		self.is_finished = True

def getChosenArgs(arduino_info):
	args = {}
	platform_list = arduino_info.getPlatformList()
	if len(platform_list) > 1:
		platform_id = constant.sketch_settings.get('platform', -1)
		if not ((platform_id > 0) and (platform_id < len(platform_list))):
			platform_id = 1
			cur_platform = platform_list[platform_id]
			platform_name = cur_platform.getName()
			constant.sketch_settings.set('platform', platform_id)
			constant.sketch_settings.set('platform_name', platform_name)
		selected_platform = platform_list[platform_id]
		board_list = selected_platform.getBoardList()
		board_id = constant.sketch_settings.get('board', -1)
		if board_list:
			serial_port = getSelectedSerialPort()
			args['serial.port'] = serial_port

			if not (board_id > -1 or board_id < len(board_list)):
				board_id = 0
				constant.sketch_settings.set('board', board_id)
			selected_board = board_list[board_id]
			args.update(selected_board.getArgs())

			board_option_list = selected_board.getOptionList()
			if board_option_list:
				board_option_key = '%d.%d' % (platform_id, board_id)
				board_option_dict = constant.sketch_settings.get('board_option', {})

				if board_option_key in board_option_dict:
					option_item_id_list = board_option_dict[board_option_key]
					if len(option_item_id_list) < len(board_option_list):
						option_item_id_list = []
				else:
					option_item_id_list = []

				if not option_item_id_list:
					for board_option in board_option_list:
						option_item_id_list.append(0)

				for board_option in board_option_list:
					index = board_option_list.index(board_option)
					option_item_id = option_item_id_list[index]
					option_item_list = board_option.getItemList()
					option_item = option_item_list[option_item_id]
					option_item_args = option_item.getArgs()
					args.update(option_item_args)

			if 'build.vid' in args:
				if not 'build.extra_flags' in args:
					args['build.extra_flags'] = '-DUSB_VID={build.vid} -DUSB_PID={build.pid}'

			if 'bootloader.path' in args:
				bootloader_path = args['bootloader.path']
				if 'bootloader.file' in args:
					bootloader_file = args['bootloader.file']
					bootloader_file = bootloader_path + '/' + bootloader_file
					args['bootloader.file'] = bootloader_file

			programmer_list = selected_platform.getProgrammerList()
			if programmer_list:
				platform_programmer_dict = constant.sketch_settings.get('programmer', {})
				if str(platform_id) in platform_programmer_dict:
					programmer_id = platform_programmer_dict[str(platform_id)]
				else:
					programmer_id = 0
				programmer = programmer_list[programmer_id]
				programmer_args = programmer.getArgs()
				args.update(programmer_args)

			platform_file = getPlatformFile(arduino_info)
			args = addBuildUsbValue(args, platform_file)
			args = replaceAllDictValue(args)

			if not 'upload.maximum_ram_size' in args:
				args['upload.maximum_ram_size'] = '0'
				if 'build.mcu' in args:
					build_mcu = args['build.mcu']
					if build_mcu in ram_size_dict:
						args['upload.maximum_ram_size'] = ram_size_dict[build_mcu]

			if 'build.elide_constructors' in args:
				if args['build.elide_constructors'] == 'true':
					args['build.elide_constructors'] = '-felide-constructors'
				else:
					args['build.elide_constructors'] = ''
			if 'build.cpu' in args:
				args['build.mcu'] = args['build.cpu']
			if 'build.gnu0x' in args:
				if args['build.gnu0x'] == 'true':
					args['build.gnu0x'] = '-std=gnu++0x'
				else:
					args['build.gnu0x'] = ''
			if 'build.cpp0x' in args:
				if args['build.cpp0x'] == 'true':
					args['build.cpp0x'] = '-std=c++0x'
				else:
					args['build.cpp0x'] = ''
	return args

def getSelectedSerialPort():
	serial_port = 'no_serial_port'
	serial_port_list = serial.getSerialPortList()
	if serial_port_list:
		serial_port_id = constant.sketch_settings.get('serial_port', -1)
		if not (serial_port_id > -1 and serial_port_id < len(serial_port_list)):
			serial_port_id = 0
			constant.sketch_settings.set('serial_port', serial_port_id)
		serial_port = serial_port_list[serial_port_id]
	return serial_port

def getReplaceTextList(text):
	pattern_text = r'\{\S+?}'
	pattern = re.compile(pattern_text)
	replace_text_list = pattern.findall(text)
	return replace_text_list

def replaceValueText(value_text, args_dict):
	replace_text_list = getReplaceTextList(value_text)
	for replace_text in replace_text_list:
		key = replace_text[1:-1]
		if key in args_dict:
			value = args_dict[key]
		else:
			value = ''
		value_text = value_text.replace(replace_text, value)
	return value_text

def replaceAllDictValue(args_dict):
	for key in args_dict:
		value_text = args_dict[key]
		value_text = replaceValueText(value_text, args_dict)
		args_dict[key] = value_text
	return args_dict

def addBuildUsbValue(args, platform_file):
	lines = fileutil.readFileLines(platform_file)
	for line in lines:
		line = line.strip()
		if line and not '#' in line:
			(key, value) = textutil.getKeyValue(line)
			if 'extra_flags' in key:
				continue
			if 'build.' in key:
				if 'usb_manufacturer' in key:
					if not value:
						value = 'unknown'
				value = replaceValueText(value, args)

				if constant.sys_platform == 'windows':
					value = value.replace('"', '\\"')
					value = value.replace('\'', '"')
				args[key] = value
	return args

def getDefaultArgs(cur_project, arduino_info):
	core_folder = getCoreFolder(arduino_info)

	arduino_folder = base.getArduinoFolder()
	ide_path = os.path.join(arduino_folder, 'hardware')
	project_name = cur_project.getName()
	serial_port = getSelectedSerialPort()
	archive_file = 'core.a'
	build_system_path = os.path.join(core_folder, 'system')
	arduino_version = arduino_info.getVersion()
	build_folder = getBuildFolder(cur_project)

	args = {}
	args['runtime.ide.path'] = arduino_folder
	args['ide.path'] = ide_path
	args['build.project_name'] = project_name
	args['serial.port.file'] = serial_port
	args['archive_file'] = archive_file
	args['software'] = 'ARDUINO'
	args['runtime.ide.version'] = '%d' % arduino_version
	args['source_file'] = '{source_file}'
	args['object_file'] = '{object_file}'
	args['object_files'] = '{object_files}'
	args['includes'] = '{includes}'
	args['build.path'] = build_folder
	return args

def getBuildFolder(cur_project):
	build_folder = constant.sketch_settings.get('build_folder', '')
	if not (build_folder and os.path.isdir(build_folder)):
		document_folder = fileutil.getDocumentFolder()
		build_folder = os.path.join(document_folder, 'Arduino_Build')
	project_name = cur_project.getName()
	build_folder = os.path.join(build_folder, project_name)
	checkBuildFolder(build_folder)
	return build_folder

def checkBuildFolder(build_folder):
	if os.path.isfile(build_folder):
		os.remove(build_folder)
	if not os.path.exists(build_folder):
		os.makedirs(build_folder)
	file_name_list = fileutil.listDir(build_folder, with_dirs = False)
	for file_name in file_name_list:
		file_ext = os.path.splitext(file_name)[1]
		if file_ext in ['.d']:
			cur_file = os.path.join(build_folder, file_name)
			os.remove(cur_file)

def getDefaultPlatformFile(arduino_info):
	file_name = 'arduino_avr.txt'
	platform_file = ''
	platform_list = arduino_info.getPlatformList()
	platform_id = constant.sketch_settings.get('platform', 1)
	platform = platform_list[platform_id]
	platform_name = platform.getName()

	if 'Arduino ARM' in platform_name:
		file_name = 'arduino_arm.txt'
	elif 'Teensy' in platform_name:
		board_list = platform.getBoardList()
		board_id = constant.sketch_settings.get('board', 0)
		board = board_list[board_id]
		board_name = board.getName()
		board_version = float(board_name.split()[1])
		if board_version >= 3.0:
			file_name = 'teensy_arm.txt'
		else:
			file_name = 'teensy_avr.txt'
	elif 'Zpuino' in platform_name:
		file_name = 'zpuino.txt'
	platform_file = os.path.join(constant.compile_root, file_name)
	return platform_file

def getCoreFolder(arduino_info):
	platform_list = arduino_info.getPlatformList()
	platform_id = constant.sketch_settings.get('platform', -1)
	if not ((platform_id > 0) and (platform_id < len(platform_list))):
		platform_id = 1
		cur_platform = platform_list[platform_id]
		platform_name = cur_platform.getName()
		constant.sketch_settings.set('platform', platform_id)
		constant.sketch_settings.set('platform_name', platform_name)
	platform = platform_list[platform_id]

	core_folder = ''
	core_folder_list = platform.getCoreFolderList()
	for cur_core_folder in core_folder_list:
		platform_file = os.path.join(cur_core_folder, 'platform.txt')
		if os.path.isfile(platform_file):
			core_folder = cur_core_folder
			break
	return core_folder

def getPlatformFile(arduino_info):
	core_folder = getCoreFolder(arduino_info)
	if core_folder:
		platform_file = os.path.join(core_folder, 'platform.txt')
	else:
		platform_file = getDefaultPlatformFile(arduino_info)
	return platform_file

def splitPlatformFile(platform_file):
	text = fileutil.readFile(platform_file)
	index = text.index('recipe.')
	text_header = text[:index]
	text_body = text[index:]
	return (text_header, text_body)

def getPlatformArgs(platform_text, args):
	lines = platform_text.split('\n')

	for line in lines:
		line = line.strip()
		if line and not '#' in line:
			(key, value) = textutil.getKeyValue(line)
			value = replaceValueText(value, args)

			if 'tools.avrdude.' in key:
				key = key.replace('tools.avrdude.', '')
			if 'tools.bossac.' in key:
				key = key.replace('tools.bossac.', '')
			if 'tools.teensy.' in key:
				key = key.replace('tools.teensy.', '')
			if 'params.' in key:
				key = key.replace('params.', '')
			if constant.sys_platform == 'linux':
				if '.linux' in key:
					key = key.replace('.linux', '')

			show_upload_output = constant.sketch_settings.get('show_upload_output', False)
			if not show_upload_output:
				if '.quiet' in key:
					key = key.replace('.quiet', '.verbose')

			if '.verbose' in key:
				verify_code = constant.sketch_settings.get('verify_code', False)
				if verify_code:
					value += ' -V'

			if key == 'build.extra_flags':
				if key in args:
					continue
			args[key] = value
	return args

def getFullArgs(cur_project, arduino_info):
	args = {}
	board_args = getChosenArgs(arduino_info)
	if board_args:
		default_args = getDefaultArgs(cur_project, arduino_info)
		args.update(default_args)
		args.update(board_args)

		platform_file = getPlatformFile(arduino_info)
		(platform_text_header, platform_text_body) = splitPlatformFile(platform_file)
		args = getPlatformArgs(platform_text_header, args)

		variant_folder = args['build.variants_folder']
		cores_folder = args['build.cores_folder']
		build_core = args['build.core']
		build_core_folder = os.path.join(cores_folder, build_core)
		args['build.core_folder'] = build_core_folder

		if 'build.variant' in args:
			build_variant = args['build.variant']
			build_variant_folder = os.path.join(variant_folder, build_variant)
			args['build.variant.path'] = build_variant_folder
		else:
			args['build.variant.path'] = build_core_folder

		if 'compiler.path' in args:
			compiler_path = args['compiler.path']
		else:
			runtime_ide_path = args['runtime.ide.path']
			compiler_path = runtime_ide_path + '/hardware/tools/avr/bin/'
		compiler_c_cmd = args['compiler.c.cmd']
		if constant.sys_platform == 'windows':
			compiler_c_cmd += '.exe'
		compiler_c_cmd_file = os.path.join(compiler_path, compiler_c_cmd)
		if os.path.isfile(compiler_c_cmd_file):
			args['compiler.path'] = compiler_path
		else:
			args['compiler.path'] = ''

		extra_flags = constant.sketch_settings.get('extra_flag', '')
		if 'build.extra_flags' in args:
			build_extra_flags = args['build.extra_flags']
		else:
			build_extra_flags = ''
		if extra_flags:
			build_extra_flags += ' '
			build_extra_flags += extra_flags
		args['build.extra_flags'] = build_extra_flags

		args = getPlatformArgs(platform_text_body, args)
	return args

def getLibFolderListFromProject(cur_project, arduino_info):
	lib_folder_list = []

	platform_list = arduino_info.getPlatformList()
	platform_id = constant.sketch_settings.get('platform', 1)
	general_platform = platform_list[0]
	selected_platform = platform_list[platform_id]
	general_h_lib_dict = general_platform.getHLibDict()
	selected_h_lib_dict = selected_platform.getHLibDict()

	ino_src_file_list = cur_project.getInoSrcFileList()
	c_src_file_list = cur_project.getCSrcFileList()
	h_list = preprocess.getHListFromSrcList(ino_src_file_list + c_src_file_list)
	for h in h_list:
		lib_folder = ''
		if h in selected_h_lib_dict:
			lib_folder = selected_h_lib_dict[h]
		elif h in general_h_lib_dict:
			lib_folder = general_h_lib_dict[h]
		if lib_folder:
			if not lib_folder in lib_folder_list:
				lib_folder_list.append(lib_folder)
	return lib_folder_list

def genBuildCppFile(build_folder, cur_project, arduino_info):
	project_name = cur_project.getName()
	cpp_file_name = project_name + '.ino.cpp'
	cpp_file = os.path.join(build_folder, cpp_file_name)
	ino_src_file_list = cur_project.getInoSrcFileList()
	arduino_version = arduino_info.getVersion()

	doMunge = not constant.sketch_settings.get('set_bare_gcc_only', False)
	preprocess.genCppFileFromInoFileList(cpp_file, ino_src_file_list, arduino_version, preprocess=doMunge)

	return cpp_file

def genIncludesPara(build_folder, project_folder, core_folder_list, compiler_include_folder):
	folder_list = sketch.getFolderListFromFolderList(core_folder_list)
	include_folder_list = []
	include_folder_list.append(build_folder)
	include_folder_list.append(project_folder)
	include_folder_list.append(compiler_include_folder)
	include_folder_list += folder_list

	includes = ''
	for include_folder in include_folder_list:
		includes += '"-I%s" ' % include_folder
	return includes

def getCompileCommand(c_file, args, includes_para):
	build_folder = args['build.path']
	file_name = os.path.split(c_file)[1]
	file_ext = os.path.splitext(c_file)[1]

	obj_file_name = file_name + '.o'
	obj_file = os.path.join(build_folder, obj_file_name)

	if file_ext in ['.S']:
		command = args['recipe.S.o.pattern']
	elif file_ext in ['.c']:
		command = args['recipe.c.o.pattern']
	else:
		command = args['recipe.cpp.o.pattern']

	command = command.replace('{includes}', includes_para)
	command = command.replace('{source_file}', c_file)
	command = command.replace('{object_file}', obj_file)

	cur_command = Command(command)
	cur_command.setInFile(c_file)
	cur_command.setOutFile(obj_file)
	return cur_command

def getCompileCommandList(c_file_list, args, includes_para):
	command_list = []
	for c_file in c_file_list:
		cur_command = getCompileCommand(c_file, args, includes_para)
		command_list.append(cur_command)
	return command_list

def getArCommand(args, core_command_list):
	build_folder = args['build.path']
	archive_file_name = args['archive_file']
	archive_file = os.path.join(build_folder, archive_file_name)

	object_files = ''
	for core_command in core_command_list:
		core_obj_file = core_command.getOutFile()
		object_files += '"%s" ' % core_obj_file
	object_files = object_files[:-1]

	command_text = args['recipe.ar.pattern']
	command_text = command_text.replace('"{object_file}"', object_files)
	ar_command = Command(command_text)
	ar_command.setOutFile(archive_file)
	return ar_command

def getElfCommand(args, project_command_list):
	build_folder = args['build.path']
	project_name = args['build.project_name']
	elf_file_name = project_name + '.elf'
	elf_file = os.path.join(build_folder, elf_file_name)

	object_files = ''
	for project_command in project_command_list:
		project_obj_file = project_command.getOutFile()
		object_files += '"%s" ' % project_obj_file
	object_files = object_files[:-1]

	command_text = args['recipe.c.combine.pattern']
	command_text = command_text.replace('{object_files}', object_files)
	elf_command = Command(command_text)
	elf_command.setOutFile(elf_file)
	return elf_command

def getEepCommand(args):
	build_folder = args['build.path']
	project_name = args['build.project_name']
	eep_file_name = project_name + '.eep'
	eep_file = os.path.join(build_folder, eep_file_name)

	command_text = args['recipe.objcopy.eep.pattern']
	eep_command = Command(command_text)
	eep_command.setOutFile(eep_file)
	return eep_command

def getHexCommand(args):
	command_text = args['recipe.objcopy.hex.pattern']
	hex_command = Command(command_text)

	build_folder = args['build.path']
	project_name = args['build.project_name']
	ext = command_text[-5:-1]
	hex_file_name = project_name + ext
	hex_file = os.path.join(build_folder, hex_file_name)
	hex_command.setOutFile(hex_file)
	return hex_command

def getSizeCommand(args):
	command_text = args['recipe.size.pattern']
	command_text = command_text.replace('-A', '')
	command_text = command_text.replace('.hex', '.elf')
	size_command = Command(command_text)
	size_command.setSizeCommand()
	return size_command

def genCommandList(args, cur_project, arduino_info):
	build_folder = args['build.path']
	project_folder = cur_project.getFolder()
	build_cpp_file = genBuildCppFile(build_folder, cur_project, arduino_info)

	build_core_folder = args['build.core_folder']
	build_variant_folder = args['build.variant.path']
	lib_folder_list = getLibFolderListFromProject(cur_project, arduino_info)
	core_folder_list = [build_core_folder, build_variant_folder] + lib_folder_list

	compiler_bin_folder = args['compiler.path']
	compiler_folder = os.path.split(compiler_bin_folder)[0]
	compiler_folder = os.path.split(compiler_folder)[0]
	compiler_name = os.path.split(compiler_folder)[1]
	compiler_folder = os.path.join(compiler_folder, compiler_name)
	compiler_include_folder = os.path.join(compiler_folder, 'include')
	compiler_include_folder = compiler_include_folder.replace('/', os.path.sep)
	# core_folder_list.append(compiler_include_folder)

	includes_para = genIncludesPara(build_folder, project_folder, core_folder_list, compiler_include_folder)
	project_C_file_list = [build_cpp_file] + cur_project.getCSrcFileList()  + cur_project.getAsmSrcFileList()
	core_C_file_list = sketch.getCSrcFileListFromFolderList(core_folder_list) + sketch.getAsmSrcFileListFromFolderList(core_folder_list)

	project_command_list = getCompileCommandList(project_C_file_list, args, includes_para)
	core_command_list = getCompileCommandList(core_C_file_list, args, includes_para)
	ar_command = getArCommand(args, core_command_list)
	elf_command = getElfCommand(args, project_command_list)
	eep_command = getEepCommand(args)
	hex_command = getHexCommand(args)
	size_command = getSizeCommand(args)

	full_compilation = constant.sketch_settings.get('full_compilation', True)
	archive_file_name = args['archive_file']
	archive_file = os.path.join(build_folder, archive_file_name)
	if not os.path.isfile(archive_file):
		full_compilation = True

	command_list = []
	command_list += project_command_list
	if full_compilation:
		if os.path.isfile(archive_file):
			os.remove(archive_file)
		command_list += core_command_list
		command_list.append(ar_command)
	command_list.append(elf_command)
	if args['recipe.objcopy.eep.pattern']:
		command_list.append(eep_command)
	command_list.append(hex_command)
	command_list.append(size_command)
	return command_list

def getCommandList(cur_project, arduino_info):
	command_list = []
	args = getFullArgs(cur_project, arduino_info)
	if args:
		command_list = genCommandList(args, cur_project, arduino_info)
	return command_list

def printSizeInfo(output_console, stdout, args):
	flash_size_key = 'upload.maximum_size'
	ram_size_key = 'upload.maximum_ram_size'
	max_flash_size = int(args[flash_size_key])
	max_ram_size = int(args[ram_size_key])

	size_line = stdout.split('\n')[-2].strip()
	info_list = re.findall(r'\S+', size_line)
	text_size = int(info_list[0])
	data_size = int(info_list[1])
	bss_size = int(info_list[2])


	flash_size = text_size + data_size
	ram_size = data_size + bss_size

	flash_percent = float(flash_size) / max_flash_size * 100
	text = 'Binary sketch size: %d bytes (of a %d byte maximum, %.2f percent).\n' % (flash_size, max_flash_size, flash_percent)
	if max_ram_size > 0:
		ram_percent = float(ram_size) / max_ram_size * 100
		text += 'Estimated memory use: %d bytes (of a %d byte maximum, %.2f percent).\n' % (ram_size, max_ram_size, ram_percent)
	output_console.printText(text)

def formatCommand(command):
	if constant.sys_version < 3:
		if constant.sys_platform == 'windows':
			command = command.replace('/"', '"')
			command = command.replace('/', os.path.sep)
			command = '"' + command + '"'
	if constant.sys_version < 3:
		if isinstance(command, unicode):
			command = command.encode(constant.sys_encoding)
	return command
