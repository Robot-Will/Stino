#-*- coding: utf-8 -*-
import sublime
import locale, codecs
import os, sys
import re
import serial
import subprocess
import threading
import time, datetime

compile_cmd = {}

if sys.platform == 'win32':
	import _winreg

def getWinVol():
	vol_list = []
	for label in xrange(67, 90):
		vol = chr(label) + ':\\'
		if os.path.isdir(vol):
			vol_list.append(vol)
	return vol_list

def getTopDirList(mode = ''):
	if sys.platform == 'win32':
		dir_list = getWinVol()
	else:
		if mode:
			home_root = os.getenv('HOME')
			dirs = listDir(home_root, with_files = False)
			path_list = [os.path.join(home_root, d) for d in dirs]
			dir_list = path_list
		else:
			dir_list = ['/']
	return dir_list

def getKeyValue(line):
	line = line.strip()
	if '=' in line:
		index = line.index('=')
		key = line[:index].strip()
		value = line[(index+1):].strip()
	else:
		key = ''
		value = ''
	return (key, value)

def genPluginRoot():
	encoding = codecs.lookup(locale.getpreferredencoding()).name
	plugin_root = os.getcwd()
	if not isinstance(plugin_root, unicode):
		plugin_root = plugin_root.decode(encoding, 'replace')
	return plugin_root

def getPluginRoot():
	Setting = sublime.load_settings('Stino.sublime-settings')
	plugin_root = Setting.get('plugin_root')
	return plugin_root

def getBlocks(lines, sep = '.name'):
	block = []
	blocks = []
	block_start = False
	for line in lines:
		line = line.strip()
		(key, value) = getKeyValue(line)
		if '=' in line:
			xwords = key
		else:
			xwords = line
		if sep in xwords and (not 'menu' in xwords):
			if block_start:
				blocks.append(block)
			block = []
			block_start = True
		if block_start and line:
			if not '###' in line:
				if not ('#' in sep and '#' in line):
					block.append(line)
	blocks.append(block)
	return blocks

def readFile(filename, mode = 'all'):
	opened_file = open(filename, 'r')
	text = opened_file.read()
	opened_file.close()

	encoding = codecs.lookup(locale.getpreferredencoding()).name
	if not isinstance(text, unicode):
		text = text.decode(encoding, 'replace')
	lines = text.split('\n')

	if mode == 'lines':
		content = lines
	elif mode == 'blocks':
		content = getBlocks(lines)
	else:
		content = text
	return content

def writeFile(filename, text, encoding = 'utf-8'):
	if sys.platform == 'darwin':
		encoding = 'utf-8'
	text = text.encode(encoding)
	f = open(filename, 'w')
	f.write(text)
	f.close()

def listDir(path, with_files = True):
	file_list = []
	files = os.listdir(path)

	encoding = codecs.lookup(locale.getpreferredencoding()).name
	if not isinstance(path, unicode):
			path = path.decode(encoding, 'replace')

	for f in files:
		is_access = False
		if not isinstance(f, unicode):
			f = f.decode(encoding, 'replace')

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
	file_list.sort(key = unicode.lower)
	return file_list

def getSubpathList(path, with_files = True, with_parent = True):
	subpath_list = []
	path = os.path.normpath(path)
	files = listDir(path, with_files)
	if with_parent:
		files.insert(0, '..')

	for f in files:
		f_path = os.path.join(path, f)
		subpath_list.append(f_path)
	return subpath_list

def getFileList(path_list):
	file_list = []
	for path in path_list:
		file_name = os.path.split(path)[1]
		if not file_name:
			file_name = path
		file_list.append(file_name)
	return file_list

def enterNext(index, level, top_path_list, path, with_files = True, with_parent = True):
	folder = os.path.split(path)[1]
	if level > 0:
		if folder == '..':
			level -= 1
		else:
			level += 1
	else:
		level += 1
	
	if level == 0:
		path_list = top_path_list
	else:
		path_list = getSubpathList(path, with_files, with_parent)
	return (level, path_list)

def removeEmptyItem(org_list):
	cur_list = [item for item in org_list if item]
	if not cur_list:
		cur_list = [[]]
	return cur_list

def getSerialPortList():
	serial_port_list = []
	has_ports = False
	if sys.platform == "win32":
		path = 'HARDWARE\\DEVICEMAP\\SERIALCOMM'
		try:
			reg = _winreg.OpenKey(_winreg.HKEY_LOCAL_MACHINE, path,)
			has_ports = True
		except:
			pass

		if has_ports:
			for i in xrange(128):
				try:
					name,value,type = _winreg.EnumValue(reg,i)
					serial_port_list.append(value)
				except:
					pass
	else:
		if sys.platform == 'darwin':
			dev_names = ['tty.*', 'cu.*']
		else:
			dev_names = ['ttyACM', 'ttyUSB']
		for dev_name in dev_names:
			cmd = 'ls /dev | grep %s' % dev_name
			serial_port_list += ['/dev/' + f.strip() for f in os.popen(cmd).readlines()]
	return serial_port_list

def has_serial_port():
	has_serial_port = False
	serial_port_list = getSerialPortList()
	if serial_port_list:
		has_serial_port = True
	return has_serial_port

def isPortAvailable(port):
	state = False
	ser = None
	try:
		ser = serial.Serial(port)
	except serial.serialutil.SerialException:
		pass
	if ser:
		state = True
		ser.close()
	return state

def openSketch(sketch_folder):
	file_name = os.path.split(sketch_folder)[1] + '.ino'
	sketch_file_path = os.path.join(sketch_folder, file_name)
	if not os.path.isfile(sketch_file_path):
		file_name = os.path.split(sketch_folder)[1] + '.pde'
		sketch_file_path = os.path.join(sketch_folder, file_name)
	sublime.run_command('new_window')
	new_window = sublime.windows()[-1]
	view = new_window.open_file(sketch_file_path)

def getLibHeaderList(lib_folder):
	header_list = []
	files = listDir(lib_folder)
	for cur_file in files:
		ext = os.path.splitext(cur_file)[1]
		if ext == '.h':
			header_list.append(cur_file)
	return header_list

def insertHeadList(view, header_list):
	edit = view.begin_edit()
	pos_txt = 0
	for header in header_list:
		text = '#include <%s>\n' % header
		len_txt = view.insert(edit, pos_txt, text)
		pos_txt += len_txt
	view.insert(edit, pos_txt, '\n')
	view.end_edit(edit)

def regFilename(filename):
	if filename:
		if filename[0] in '0123456789':
			filename = '_' + filename
		filename = filename.replace(' ', '_')
	return filename

def isMainSrc(filename):
	state = False
	has_setup = False
	has_loop = False
	text = genSimpleSrcFile(filename)
	function_list = genFunctionList(text)
	for function in function_list:
		if 'setup' in function:
			has_setup = True
		if 'loop' in function:
			has_loop = True
	if has_setup and has_loop:
		state = True
	return state

def isSketch(filename):
	state = False
	if filename:
		path = os.path.split(filename)[0]
		if not 'examples' in path:
			ext = os.path.splitext(filename)[1]
			if ext == '.ino' or ext == '.pde':
				state = True
			else:
				state = isMainSrc(filename)
	return state

def openUrl(url):
	Setting = sublime.load_settings('Stino.sublime-settings')
	arduino_root = Setting.get('Arduino_root')
	if sys.platform == 'darwin':
		arduino_root = os.path.join(arduino_root, 'Contents/Resources/JAVA')
	reference_dir = os.path.join(arduino_root, 'reference')
	reference_dir = reference_dir.replace(os.path.sep, '/')
	ref_file = '%s/%s.html' % (reference_dir, url)
	sublime.run_command('open_url', {'url': ref_file})

def formatNumber(number):
	length = len(number)
	number_str = number[::-1]
	seq = 1
	new_number = ''
	for digit in number_str:
		if seq % 3 == 0:
			if seq != length:
				digit = ',' + digit
		new_number = digit + new_number
		seq += 1
	return new_number

def genUploadeFiles(mode, cur_lang):
	global compile_cmd
	prj_folder = compile_cmd['prj_folder']
	bin_path = compile_cmd['bin_path']
	programmer = compile_cmd['programmer']

	text = '.PHONY: build\n\n'
	if mode == 'upload':
		text += 'build:\n\t'
		text += '@echo "%s %s..."\n\t' % ('%(Uploading)s', bin_path)
		text += '%s\n\t' % compile_cmd['upload_pattern']
		if 'reboot_pattern' in compile_cmd:
			text += '-%s\n\t' % compile_cmd['reboot_pattern']
		else:
			text += '\n'
	elif mode == 'upload_using_programmer':
		text += 'build:\n\t'
		text += '@echo "%s %s %s %s..."\n\t' % ('%(Uploading)s', bin_path, '%(Using)s', programmer)
		if 'program_pattern' in compile_cmd:
			text += '%s\n\n' % compile_cmd['program_pattern']
		else:
			text += '\n'
	elif mode == 'erase_pattern':
		text += 'build:\n\t'
		text += '@echo "%(Burning_Bootloader)s..."\n\t'
		if 'erase_pattern' in compile_cmd:
			text += '%s\n\t' % compile_cmd['erase_pattern']
			text += '%s\n\n' % compile_cmd['bootloader_pattern']
		else:
			text += '\n'
	new_text = text % cur_lang.getDisplayTextDict()
	file_name = 'makefile'
	file_path = os.path.join(prj_folder, file_name)

	encoding = codecs.lookup(locale.getpreferredencoding()).name
	writeFile(file_path, new_text, encoding)

class runCompile:
	def __init__(self, window, regex, upload_maximum_size, uploader, mode, cur_lang):
		self.window = window
		self.panel = self.window.get_output_panel('arduino_panel')
		self.Settings = sublime.load_settings('Stino.sublime-settings')
		self.output_text = ''
		self.show_text = ''
		self.done_text = '[Arduino - Make process has finished in {1} s.]'
		self.pattern = re.compile(regex)
		self.upload_maximum_size = formatNumber(upload_maximum_size)
		mem_maximum_size = compile_cmd['upload_maximum_ram_size']
		self.mem_maximum_size = formatNumber(mem_maximum_size)
		self.size_line = ''
		self.uploader = uploader
		if sys.platform == 'win32':
			self.uploader += '.exe'
		self.uploader += ':'
		self.interval = 0
		self.mode = mode
		self.cur_lang = cur_lang

	def run(self):
		thread_compile = threading.Thread(target=self.compile)
		thread_display = threading.Thread(target=self.display)
		thread_compile.start()
		thread_display.start()

	def compile(self):
		encoding = codecs.lookup(locale.getpreferredencoding()).name
		if sys.platform == 'darwin':
			encoding = 'utf-8'
		if sys.platform == 'win32':
			cmd = 'build.bat'
		else:
			cmd = './build.sh'
		starttime = datetime.datetime.now()
		if self.mode != 'burn_bootloader':
			self.process = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, bufsize = 1, shell = True)
			self.build_finished = False
			size_info = ''
			mem_size_info = ''
			while self.process.poll() == None:
				line = self.process.stdout.readline()
				if line.strip():
					text = line.decode(encoding, 'replace')
					self.output_text += text
					match = self.pattern.search(line)
					if match:
						self.build_finished = True
						size_info = match.group()
					if self.build_finished:
						if './build' in line and not '"' in line:
							mem_size_info = line
			if self.build_finished:
				words = size_info.split(' ')
				words = [word for word in words if word]
				if words:
					print words[1]
					size = formatNumber(words[1].strip())
				else:
					size = '0'
				self.size_line = 'Binary sketch size: %s bytes (of a %s byte maximum).\n' % (size, self.upload_maximum_size)
				words = mem_size_info.split(' ')
				words = [word for word in words if word]
				if words:
					data = int(words[1])
					bss = int(words[2])
					mem_size = str(data + bss)
					mem_size = formatNumber(mem_size)
				else:
					mem_size = '0'
				self.size_line += 'Estimated memory use: %s bytes (of a %s byte maximum).\n' % (mem_size, self.mem_maximum_size)
				self.output_text += self.size_line
		global compile_cmd
		if self.mode != 'build':
			if self.mode == 'burn_bootloader':
				genUploadeFiles(self.mode, self.cur_lang)
			else:
				if self.build_finished:
					if self.mode == 'upload':
						if 'AVR' in compile_cmd['platform']:
							if 'build_vid' in compile_cmd:
								serial_port_before = compile_cmd['serial_port']
								if serial_port_before != 'serial_port':
									serial_list_before = getSerialPortList()
									ser = serial.Serial()
									ser.port = serial_port_before
									ser.baudrate = 1200
									ser.open()
									time.sleep(0.01)
									ser.close()
									if sys.platform != 'darwin':
										time.sleep(0.5)
									serial_list_after = []
									stime = datetime.datetime.now()
									while(not serial_list_after):
										serial_list_after = getSerialPortList()
										nowtime = datetime.datetime.now()
										interval = (nowtime - stime).seconds
										if interval > 5:
											break
									for port in serial_list_before:
										if port in serial_list_after:
											serial_list_after.remove(port)
									if serial_list_after:
										serial_port = serial_list_after[0]
									else:
										serial_port = 'serial_port'
									compile_cmd['upload_pattern'] = compile_cmd['upload_pattern'].replace(serial_port_before, serial_port)
					genUploadeFiles(self.mode, self.cur_lang)
			self.process = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, bufsize = 1, shell = True)
			while self.process.poll() == None:
				line = self.process.stdout.readline()
				if line.strip():
					text = line.decode(encoding, 'replace')
					self.output_text += text
		self.output_text += self.done_text
		endtime = datetime.datetime.now()
		self.interval = (endtime - starttime).seconds

	def display(self):
		while True:
			self.show_text = self.output_text
			if self.show_text:
				index = len(self.show_text)
				self.output_text = self.output_text[index:]
				sublime.set_timeout(self.update, 0)
				last_line = self.show_text.split('\n')[-1]
				if last_line == self.done_text:
					break
			time.sleep(0.1)
		

	def update(self):
		edit = self.panel.begin_edit()
		lines = self.show_text.split('\n')
		for line in lines:
			verbose_compilation = self.Settings.get('verbose_compilation')
			show_output = False
			line = line.strip()
			if line:
				if '...' in line or 'warning:' in line or 'error:' in line or 'No device' in line \
					or 'make:' in line or self.uploader in line or ': In ' in line or 'wrong' in line \
					or 'exit' in line or 'Binary sketch size' in line or 'not found' in line \
					or 'Unknown' in line or 'Opening Teensy Loader' in line or 'unexpected' in line\
					or 'Estimated memory use' in line:
					show_output = True
				elif self.done_text in line:
					line = line.replace('{1}', str(self.interval))
					show_output = True
				else:
					if verbose_compilation:
						show_output = True
				if show_output:
					line += '\n'
					self.panel.insert(edit, self.panel.size(), line)
		self.panel.end_edit(edit)
		self.panel.show(self.panel.size())
		self.window.run_command("show_panel", {"panel": "output.arduino_panel"})

def runBuild(window, arduino_info, cur_lang, mode = 'build'):
	window.active_view().run_command('save')
	prj_file = window.active_view().file_name()
	createBuildFile(prj_file)
	(main_src_number, prj_path, regex, upload_maximum_size, uploader) = genBuildFiles(prj_file, arduino_info, cur_lang)
	if main_src_number == 1:
		os.chdir(prj_path)
		compilation = runCompile(window, regex, upload_maximum_size, uploader, mode, cur_lang)
		compilation.run()
		state = True
	else:
		if main_src_number == 0:
			msg = 'Error: No main sketch file was found!'
		else:
			msg = 'Error: More than one main sketch file were found!'
		sublime.message_dialog(msg)
		state = False
	return state

def createBuildFile(prj_file):
	working_dir = os.path.split(prj_file)[0]
	working_dir = working_dir.replace(os.path.sep, '/')
	plugin_root = getPluginRoot()
	template_dir = os.path.join(plugin_root, 'template')
	template_file_path = os.path.join(template_dir, 'stino-build')
	text = readFile(template_file_path)
	encoding = codecs.lookup(locale.getpreferredencoding()).name
	if sys.platform == 'darwin':
		encoding = 'utf-8'
	text = text.replace('%(encoding)s', encoding)
	text = text.replace('%(working_dir)s', working_dir)

	build_file_path = os.path.join(plugin_root, 'Arduino.sublime-build')
	writeFile(build_file_path, text)

def getBoardBlock(board_file_path, board, has_processor, processor):
	board_block = []
	board_blocks = readFile(board_file_path, mode = 'blocks')
	text = readFile(board_file_path)
	if '.container=' in text:
		is_selected = False
		for block in board_blocks:
			cur_cpu = ''
			for line in block:
				if '.name=' in line:
					(key, cur_board) = getKeyValue(line)
				if '.container=' in line:
					(key, cur_board) = getKeyValue(line)
					has_processor = True
					break
				if '.cpu=' in line:
					(key, cur_cpu) = getKeyValue(line)
			if cur_board == board:
				if has_processor:
					if cur_cpu == processor:
						is_selected = True
				else:
					is_selected = True
			if is_selected:
				board_block = block
				break
	elif 'menu.usb' in text:
		for block in board_blocks:
			line = block[0]
			(key, value) = getKeyValue(line)
			if value == board:
				board_block = block
				break
		block = []
		usb_type_block = []
		cpu_block = []
		keyboard_block = []
		for line in board_block:
			if not '#' in line:
				if not 'menu' in line:
					line = line.replace('command', 'compiler')
					block.append(line)
				elif 'menu.usb' in line:
					usb_type_block.append(line)
				elif 'menu.speed' in line:
					cpu_block.append(line)
				elif 'menu.keys' in line:
					keyboard_block.append(line)
		board_block = block
		Settings = sublime.load_settings('Stino.sublime-settings')
		usb_type = Settings.get('usb_type')
		keyboard_layout = Settings.get('keyboard_layout')
		is_start = False
		for line in usb_type_block:
			(key, value) = getKeyValue(line)
			if is_start:
				if 'name' in line:
					break
				board_block.append(line)
			if value == usb_type:
				is_start = True
		is_start = False
		for line in cpu_block:
			(key, value) = getKeyValue(line)
			if is_start:
				if speed_id in key:
					board_block.append(line)
					break
			if value == processor:
				speed_id = key.replace('.name', '')
				is_start = True
		is_start = False
		for line in keyboard_block:
			(key, value) = getKeyValue(line)
			if is_start:
				if 'name' in line:
					break
				board_block.append(line)
			if value == keyboard_layout:
				is_start = True
	else:
		for block in board_blocks:
			line = block[0]
			(key, value) = getKeyValue(line)
			if value == board:
				board_block = block
				break

		if has_processor:
			processor_blocks = getBlocks(board_block, '## ')
			for block in processor_blocks:
				line = block[0]
				(key, value) = getKeyValue(line)
				if value == processor:
					processor_block = block
					break
			block = []
			for line in board_block[1:]:
				if '## ' in line:
					break
				block.append(line)
			board_block = block + processor_block[1:]
	return board_block

def getProgrammerBlock(arduino_info, programmer):
	programmer_block = []
	if arduino_info.hasProgrammer():
		programmer_file_path = arduino_info.getProgrammerFile(programmer)
		programmer_blocks = readFile(programmer_file_path, mode = 'blocks')
		for block in programmer_blocks:
			line = block[0]
			(key, value) = getKeyValue(line)
			if value == programmer:
				programmer_block = block[1:]
				break
	return programmer_block

def getPlatformBlock(platform_file_path):
	lines = readFile(platform_file_path, mode = 'lines')
	platform_block = getBlocks(lines, sep = 'name')[0]
	platform_block = platform_block[1:]
	return platform_block

def genCompileInfo(info_block, compile_info):
	dict_key_list = []
	for line in info_block:
		(key, value) = getKeyValue(line)
		id_list = key.split('.')
		if len(id_list) == 2:
			key = id_list[-1]
		else:
			key = '%s_%s' % (id_list[-2], id_list[-1])
		if not key in compile_info:
			compile_info[key] = value
			dict_key_list.append(key)
	if 'build_vid' in compile_info:
		if not 'build_extra_flags' in compile_info:
			compile_info['build_extra_flags'] = '-DUSB_VID={build.vid} -DUSB_PID={build.pid}'
			dict_key_list.append('build_extra_flags')
	return (compile_info, dict_key_list)

def genPlatformInfo(platform_block, compile_info):
	dict_key_list = []
	for line in platform_block:
		if not '#' in line:
			(key, value) = getKeyValue(line)
			if 'tools' in key:
				id_list = key.split('.')[2:]
				key = id_list[0]
				for txt in id_list[1:]:
					if not 'params' in txt:
						key += '_%s' % txt
			key = key.replace('.', '_')
			if not key in compile_info:
				compile_info[key] = value
				dict_key_list.append(key)
	return (compile_info, dict_key_list)

def getHeaderList(prj_file):
	header_list = []
	pattern = re.compile(r'["<]\S+?[>"]')
	lines = readFile(prj_file, mode = 'lines')
	for line in lines:
		if '#include' in line:
			match = pattern.search(line)
			if match:
				header_list.append(match.group()[1:-1])
	return header_list

def getLibList(arduino_info):
	lib_list = []
	for libs in arduino_info.getLibList():
		lib_list += libs
	lib_list = [arduino_info.getLibFolder(lib) for lib in lib_list]
	return lib_list

def getExtLibPaths(header_list, lib_list):
	ext_lib_paths = []
	for header in header_list:
		for lib in lib_list:
			files = listDir(lib)
			if header in files:
				if not lib in ext_lib_paths:
					ext_lib_paths.append(lib)
	ext_lib_paths = [path.replace(os.path.sep, '/') for path in ext_lib_paths]
	return ext_lib_paths

def getIncludes(includes_paths):
	includes = ''
	for path in includes_paths:
		includes += '"-I%s" ' % path
	return includes

def getBlankKeyList(compile_info):
	blank_key_list = []
	pattern = re.compile(r'{\S+?}')
	for key in compile_info:
		line = compile_info[key]
		match = pattern.search(line)
		if match:
			txt_list = pattern.findall(line)
			for org_txt in txt_list:
				txt = org_txt[1:-1]
				txt = txt.replace('.', '_')
				if not txt in compile_info:
					if not txt in blank_key_list:
						blank_key_list.append(txt)
	return blank_key_list
	
def strInfoDict(compile_info, dict_key_list):
	blank_key_list = getBlankKeyList(compile_info)
	for key in blank_key_list:
		compile_info[key] = ''

	pattern = re.compile(r'{\S+?}')
	for key in dict_key_list:
		line = compile_info[key]
		match = pattern.search(line)
		if match:
			txt_list = pattern.findall(line)
			for org_txt in txt_list:
				txt = org_txt[1:-1]
				txt = txt.replace('.', '_')
				txt = '%(' + txt + ')s'
				line = line.replace(org_txt, txt)
			new_line = line % compile_info
			compile_info[key] = new_line
	return compile_info

def findSrcFiles(ext_list, path, is_sketch = False):
	file_list = []
	build_path = os.path.join(path, 'build')
	for (cur_path, sub_dirs, files) in os.walk(path):
		if is_sketch:
			if build_path in cur_path:
				continue
		if 'examples' in cur_path:
			continue
		for f in files:
			cur_ext = os.path.splitext(f)[1]
			if cur_ext in ext_list:
				f_path = os.path.join(cur_path, f)
				if is_sketch:
					f_path = f_path.replace(path, '.')
				f_path = f_path.replace(os.path.sep, '/')
				file_list.append(f_path)
	return file_list

def findAllFiles(path = '.'):
	file_list = []
	build_path = os.path.join(path, 'build')
	for (cur_path, sub_dirs, files) in os.walk(path):
		if cur_path == build_path:
			continue
		file_path_list = [os.path.join(cur_path, f) for f in files if not (f == 'makefile' or f == 'build.bat' or f == 'build.sh')]
		file_list += file_path_list
	return file_list

def extendIncludePaths(src_list, includes_paths):
	for src_path in src_list:
		src_dir_path = os.path.split(src_path)[0]
		if not src_dir_path in includes_paths:
			includes_paths.append(src_dir_path)
	return includes_paths

def genSrcObjDict(src_list, build_path = './build'):
	src_obj_dict = {}
	for src in src_list:
		src_basename = os.path.split(src)[1]
		obj_basename = src_basename + '.o'
		obj_path = os.path.join(build_path, obj_basename)
		obj_path = obj_path.replace(os.path.sep, '/')
		src_obj_dict[src] = obj_path
	return src_obj_dict

def genSimpleSrcFile(prj_file):
	text = ''
	lines = readFile(prj_file, mode = 'lines')
	level = 0
	for line in lines:
		line = line.strip()
		s = '{'
		if s in line:
			if level == 0:
				index = line.index(s)
				text += line[:index+1]
			number = line.count(s)
			level += number
		s = '}'
		if s in line:
			number = line.count(s)
			level -= number
			if level == 0:
				text += '}\n'
		if not ('{' in line or '}' in line):
			if level == 0:
				if line:
					line = line.replace(';', ';\n')
					text += line
					text += ' '
					if '#' in line:
						text += '\n'
	return text

def regFunction(function):
	function = function.replace('\n', ' ')
	function = function.replace('\t', ' ')
	return function

def genFunctionList(text):
	text = '\n' + text
	pattern = re.compile(r'\S+?\s+?\S+?\s*?\([\S\s]*?\)')
	match = pattern.search(text)
	function_list = []
	if match:
		function_list = pattern.findall(text)
	return function_list

def isMainFunction(function):
	state = False
	txt = function.split('(')[0]
	txt_list = txt.split(' ')
	for txt in txt_list:
		txt = txt.strip()
		if txt == 'setup' or txt == 'loop':
			state = True
	return state

def genDeclaration(function_list):
	declaration_list = []
	function_body_list = []
	is_declaration = True
	is_function_body = False
	for function in function_list:
		if isMainFunction(function):
			is_declaration = False
			is_function_body = True
		if is_declaration:
			declaration_list.append(function)
		if is_function_body:
			if not isMainFunction(function):
				function_body_list.append(function)
	declaration_text = ''
	for function in function_body_list:
		if not function in declaration_list:
			declaration_text += function
			declaration_text += ';\n'
	return declaration_text

def getFirstInclude(prj_file):
	first_include_text = ''
	pattern = re.compile(r'#include\s+?["<]\S+?[>"]')
	text = readFile(prj_file)
	match = pattern.search(text)
	if match:
		first_include_text = match.group()
	return first_include_text

def genMainFile(prj_file, main_file_path, arduino_info):
	text = genSimpleSrcFile(prj_file)
	function_list = genFunctionList(text)
	declaration_text = genDeclaration(function_list)
	main_text = readFile(prj_file)
	first_include_text = getFirstInclude(prj_file)
	version = arduino_info.getVersion()
	if version >= 100:
		inc_text = '#include <Arduino.h>\n'
	else:
		inc_text = '#include <WProgram.h>\n'
	if first_include_text:
		text = inc_text + first_include_text
		main_text = main_text.replace(first_include_text, text)
	else:
		main_text = inc_text + main_text
	if declaration_text:
		first_function = function_list[0]
		text = declaration_text + first_function
		main_text = main_text.replace(first_function, text)
	writeFile(main_file_path, main_text)

def genScriptFile(prj_folder, path_list, mode):
	Setting = sublime.load_settings('Stino.sublime-settings')
	arduino_root = Setting.get('Arduino_root')
	if sys.platform == 'darwin':
		arduino_root = os.path.join(arduino_root, 'Contents/Resources/JAVA')
	hardware_dir = os.path.join(arduino_root, 'hardware')
	tools_dir = os.path.join(hardware_dir, 'tools')
	arv_dir = os.path.join(tools_dir, 'avr')
	utils_dir = os.path.join(arv_dir, 'utils')
	posix_root = os.path.join(utils_dir, 'bin')
	
	text = ''
	if sys.platform == 'win32':
		text += '@echo off\n'
		text += 'Set Path=%s' % posix_root
		for path in path_list:
			path = path.replace('/', os.path.sep)
			text += ';%s' % path
		text+= '\n'
	# elif sys.platform == 'darwin':
	# 	text += '#!/bin/sh\n\n'
	# 	text += 'launchctl setenv PATH '
	# 	for path in path_list:
	# 		path = path.replace(' ', '\\ ')
	# 		text += '%s:' % path
	# 	text += '$PATH\n'
	else:
		text += '#!/bin/sh\n\n'
		text += 'export PATH='
		for path in path_list:
			path = path.replace(' ', '\\ ')
			text += '%s:' % path
		text += '$PATH\n'
	text += 'make %s\n' % mode

	if sys.platform == 'win32':
		file_name = 'build.bat'
	else:
		file_name = 'build.sh'
	file_path = os.path.join(prj_folder, file_name)

	encoding = codecs.lookup(locale.getpreferredencoding()).name
	writeFile(file_path, text, encoding)
	if sys.platform != 'win32':
		cmd = 'chmod +x %s' % file_path
		os.popen(cmd)

def findMainSketchPath(filename):
	org_file_folder = os.path.split(filename)[0]
	if isMainSrc(filename):
		main_sketch_path = org_file_folder
	else:
		has_main_sketch = False
		cur_path = filename
		while not has_main_sketch:
			cur_path = os.path.split(cur_path)[0]
			if cur_path[-1] == os.path.sep:
				cur_path = cur_path[:-1]
			if not os.path.sep in cur_path:
				break
			file_list = listDir(cur_path)
			for f in file_list:
				f_path = os.path.join(cur_path, f)
				if os.path.isfile(f_path):
					if isMainSrc(f_path):
						has_main_sketch = True
						break
		if has_main_sketch:
			main_sketch_path = cur_path
		else:
			main_sketch_path = org_file_folder
	return main_sketch_path

def getSketchPath(filename, arduino_info):
	sketchbook_root = arduino_info.getSketchbookRoot()
	org_file_folder = os.path.split(filename)[0]

	file_folder = org_file_folder
	parent_folder = os.path.split(org_file_folder)[0]
	in_sketchbook = True

	while parent_folder != sketchbook_root:
		if not os.path.sep in parent_folder:
			in_sketchbook = False
			break
		file_folder = parent_folder
		parent_folder = os.path.split(file_folder)[0]
		if parent_folder[-1] == os.path.sep:
			parent_folder = parent_folder[:-1]

	if in_sketchbook:
		sketch_path = file_folder
	else:
		sketch_path = findMainSketchPath(filename)
	return sketch_path

def genBuildFiles(prj_file, arduino_info, cur_lang, mode = 'build'):
	plugin_root = getPluginRoot()
	template_dir = os.path.join(plugin_root, 'template')

	sketch_path = getSketchPath(prj_file, arduino_info)
	sketch_name = os.path.split(sketch_path)[1]

	# prj_folder = os.path.split(prj_file)[0]
	# prj_filename = os.path.split(prj_file)[1]
	# prj_name = os.path.splitext(prj_filename)[0]

	prj_folder = sketch_path
	prj_name = sketch_name

	src_ext_list = ['.c', '.cpp', '.ino', '.pde', '.cc', '.cxx']
	prj_src_list = findSrcFiles(src_ext_list, prj_folder, is_sketch = True)
	
	main_src_number = 0
	main_src = ''
	for prj_src in prj_src_list:
		prj_src_path = prj_src.replace('./', prj_folder + os.path.sep)
		prj_src_path = prj_src_path.replace('/', os.path.sep)
		if isMainSrc(prj_src_path):
			main_src_number += 1
			main_src = prj_src
	if main_src_number != 1:
		return (main_src_number, prj_folder, '', 0, 'cmd')
	prj_src_list.remove(main_src)
	main_src_name = os.path.split(main_src)[1]
	main_src_path = main_src.replace('./', prj_folder + os.path.sep)

	build_dir = './build'
	build_path = os.path.join(prj_folder, build_dir)
	main_filename = '%s.cpp' % main_src_name
	main_file = build_dir + '/' + main_filename
	main_file_path = os.path.join(build_path, main_filename)
	core_ar_file = 'core.a'
	core_ar_path = build_dir + '/' + core_ar_file
 
	if not os.path.isdir(build_path):
		os.mkdir(build_path)

	if os.path.isfile(main_file_path):
		os.remove(main_file_path)

	genMainFile(main_src_path, main_file_path, arduino_info)

	Setting = sublime.load_settings('Stino.sublime-settings')
	arduino_root = Setting.get('Arduino_root')
	if sys.platform == 'darwin':
		arduino_root = os.path.join(arduino_root, 'Contents/Resources/JAVA')
	board = Setting.get('board')
	processor = Setting.get('processor', '')
	programmer = Setting.get('programmer', '')
	serial_port = Setting.get('serial_port', '')

	full_compilation = Setting.get('full_compilation')
	verbose_upload = Setting.get('verbose_upload')
	verify_code = Setting.get('verify_code')

	platform = arduino_info.getPlatform(board)

	has_processor = arduino_info.hasProcessor(board)

	core_root = arduino_info.getPlatformFileFolder(platform)
	board_file_path = arduino_info.getBoardFile(board)
	board_dir_path = os.path.split(board_file_path)[0]
	platform_file_path = os.path.join(core_root, 'platform.txt')

	serial_list = getSerialPortList()
	if serial_list:
		if not serial_port in serial_list:
			serial_port = serial_list[0]
			Setting.set('serial_port', serial_port)
			sublime.save_settings('Stino.sublime-settings')
	else:
		serial_port = 'serial_port'
	build_system_path = os.path.join(core_root, 'system')

	board_block = getBoardBlock(board_file_path, board, has_processor, processor)
	programmer_block = getProgrammerBlock(arduino_info, programmer)
	info_block = board_block + programmer_block

	header_list = getHeaderList(prj_file)
	lib_list = getLibList(arduino_info)
	ext_lib_paths = getExtLibPaths(header_list, lib_list)

	dict_key_list = []
	compile_info = {}
	compile_info['serial_port'] = serial_port
	compile_info['serial_port_file'] = serial_port
	compile_info['runtime_ide_path'] = arduino_root.replace(os.path.sep, '/')
	compile_info['build_system_path'] = build_system_path.replace(os.path.sep, '/')
	compile_info['build_project_name'] = prj_name
	compile_info['build_path'] = build_dir
	compile_info['object_file'] = '$@'
	compile_info['object_files'] = '$@'
	compile_info['source_file'] = '$<'
	compile_info['archive_file'] = core_ar_file
	compile_info['software'] = 'ARDUINO'
	compile_info['runtime_ide_version'] = str(int(arduino_info.getVersion()))

	(compile_info, key_list) = genCompileInfo(info_block, compile_info)
	dict_key_list += key_list
	
	if not os.path.isfile(platform_file_path):
		if 'teensy' in platform:
			if compile_info['build_elide_constructors'] == 'true':
				compile_info['build_elide_constructors'] = '-felide-constructors'
			else:
				compile_info['build_elide_constructors'] = ''
			if 'build_architecture' in compile_info:
				compile_info['build_mcu'] = compile_info['build_cpu']
				if compile_info['build_gnu0x'] == 'true':
					compile_info['build_gnu0x'] = '-std=gnu++0x'
				else:
					compile_info['build_gnu0x'] = ''
				platform_file_path = os.path.join(template_dir, 'teensy_arm.txt')
			else:
				if compile_info['build_cpp0x'] == 'true':
					compile_info['build_cpp0x'] = '-std=c++0x'
				else:
					compile_info['build_cpp0x'] = ''
				platform_file_path = os.path.join(template_dir, 'teensy.txt')
		else:
			platform_file_path = os.path.join(template_dir, 'platform.txt')
	platform_block = getPlatformBlock(platform_file_path)
	(compile_info, key_list) = genPlatformInfo(platform_block, compile_info)
	dict_key_list += key_list

	core_dir = os.path.join(core_root, 'cores')
	build_core = compile_info['build_core']
	if ':' in build_core:
		build_core = build_core.split(':')[-1].strip()
	core_source_dir = os.path.join(core_dir, build_core)
	core_source_dir = core_source_dir.replace(os.path.sep, '/')

	variants_dir = os.path.join(board_dir_path, 'variants')
	if 'build_variant' in compile_info:
		variant_dir = os.path.join(variants_dir, compile_info['build_variant'])
		variant_dir = variant_dir.replace(os.path.sep, '/')
	else:
		variant_dir = core_source_dir

	if variant_dir == core_source_dir:
		includes_paths = [core_source_dir] + ext_lib_paths
	else:
		includes_paths = [core_source_dir, variant_dir] + ext_lib_paths
	
	core_src_folder_list = [core_source_dir] + ext_lib_paths
	core_src_list = []
	for core_src_folder in core_src_folder_list:
		core_src_list += findSrcFiles(src_ext_list, core_src_folder)
	
	src_list = prj_src_list + core_src_list
	includes_paths = extendIncludePaths(src_list, includes_paths)
	if not '.' in includes_paths:
		includes_paths.append('.')
	includes = getIncludes(includes_paths)
	compile_info['includes'] = includes
	compile_info['build_variant_path'] = variant_dir

	if not 'compiler_path' in compile_info:
		compiler_path = os.path.join(arduino_root, 'hardware/tools/avr/bin/')
		compiler_path = compiler_path.replace(os.path.sep, '/')
		compile_info['compiler_path'] = compiler_path
	if not verbose_upload:
		for key in compile_info:
			if 'verbose' in key:
				quiet_key = key.replace('verbose', 'quiet')
				compile_info[key] = compile_info[quiet_key]

	if 'cmd_path' in compile_info:
		if 'avrdude' in compile_info['cmd_path']:
			if 'linux' in sys.platform:
				compile_info['cmd_path'] = compile_info['cmd_path_linux']
				compile_info['config_path'] = compile_info['config_path_linux']
			if not verify_code:
				for key in compile_info:
					if 'verbose' in key:
						compile_info[key] += ' -V'

	compile_info['gcc_root'] = compile_info['compiler_path'][:-1]
	compile_info['compiler_path'] = ''
	if 'cmd_path' in compile_info:
		dir_path = os.path.split(compile_info['cmd_path'])[0]
		basename = os.path.split(compile_info['cmd_path'])[1]
		compile_info['uploader_root'] = dir_path
		compile_info['cmd_path'] = basename
	elif 'path' in compile_info:
		compile_info['uploader_root'] = compile_info['path']
		compile_info['upload_pattern'] = compile_info['upload_pattern'].replace('{path}/{cmd}', '{cmd}')
	dict_key_list.append('gcc_root')
	dict_key_list.append('uploader_root')
	compile_info = strInfoDict(compile_info, dict_key_list)
	if 'config_path' in compile_info:
		if not os.path.isfile(compile_info['config_path']):
			compile_info['config_path'] = '/etc/avrdude.conf'
		# compile_info['config_path'] = compile_info['config_path'].replace(' ', '\\ ')
	
	if not main_file in prj_src_list:
		prj_src_list.append(main_file)
	core_src_list = [src.replace(' ', '\\ ') for src in core_src_list]
	prj_src_list = [src.replace(' ', '\\ ') for src in prj_src_list]
	src_list = prj_src_list + core_src_list
	src_obj_dict = genSrcObjDict(src_list)
    
####
	prj_name = prj_name.replace(' ', '\\ ')
	elf_file = '%s.elf' % prj_name
	bin_ext = compile_info['recipe_objcopy_hex_pattern'].split('.')[-1]
	bin_ext = bin_ext[:-1]
	bin_file = '%s.%s' % (prj_name, bin_ext)
	elf_path = '%s/%s' % (build_dir, elf_file)
	bin_path = '%s/%s' % (build_dir, bin_file)

	size_ext = compile_info['recipe_size_pattern'].split('.')[-1]
	size_ext = size_ext[:-1]
	size_file = '%s.%s' % (prj_name, size_ext)
	size_path = '%s/%s' % (build_dir, size_file)

	if compile_info['recipe_objcopy_eep_pattern']:
		eep_file = '%s.eep' % prj_name
		eep_path = '%s/%s' % (build_dir, eep_file)
	else:
		eep_path = ''

	clean_cmd = '"rm" -rf "%s" "%s"' % (bin_path, elf_path)
	if eep_path:
		clean_cmd += ' "%s"' % eep_path
	for prj_src in prj_src_list:
		prj_obj = src_obj_dict[prj_src]
		clean_cmd += ' "%s"' % prj_obj
	if full_compilation:
		clean_cmd += ' "%s"' % core_ar_path
		for core_src in core_src_list:
			core_obj = src_obj_dict[core_src]
			clean_cmd += ' "%s"' % core_obj
	# if verbose_compilation:
	# 	verbose_text = ''
	# else:
	# 	verbose_text = '@'
	
####
	text = ''
	text += '.PHONY: all build clean upload size upload_using_programmer burn_bootloader\n\n'
	text += 'all: build\n\n'
	text += 'build: clean build_msg %s size\n\n' % bin_path
	text += 'build_msg:\n\t'
	text += '@echo "%(Building)s..."\n\n'

	# text += 'upload: build\n\t'
	# text += '@echo "%s %s..."\n\t' % ('%(Uploading)s', bin_path)
	# text += '%s\n\n' % compile_info['upload_pattern']

	# if 'program_pattern' in compile_info:
	# 	text += 'upload_using_programmer: build\n\t'
	# 	text += '@echo "%s %s %s %s..."\n\t' % ('%(Uploading)s', bin_path, '%(Using)s', programmer)
	# 	text += '%s\n\n' % compile_info['program_pattern']

	# if 'erase_pattern' in compile_info:
	# 	text += 'burn_bootloader:\n\t'
	# 	text += '@echo "%(Burning_Bootloader)s..."\n\t'
	# 	text += '%s\n\t' % compile_info['erase_pattern']
	# 	text += '%s\n\n' % compile_info['bootloader_pattern']

	text += 'size: %s\n\t' % size_path
	# text += '@echo "%s %s:"\n\t' % ('%(Size_Information_Of)s', size_path)
	text += '%s\n\t' % compile_info['recipe_size_pattern']
	size_cmd = compile_info['recipe_size_pattern'].replace('-A', '')
	size_cmd = size_cmd.replace('.hex', '.elf')
	text += '%s\n\n' % size_cmd
	# text += '@echo %s: %s %s.\n\n' % ('%(Maximum_Size)s', compile_info['upload_maximum_size'], '%(bytes)s')

	text += 'clean:\n\t'
	text += '@echo "%(Cleaning)s..."\n\t'
	text += '%s\n\n' % clean_cmd

	if eep_path:
		text += '%s: %s %s\n\t' % (bin_path, elf_path, eep_path)
	else:
		text += '%s: %s\n\t' % (bin_path, elf_path)
	text += '@echo "%s %s..."\n\t' % ('%(Creating)s', bin_path)
	text += '%s\n\n' % compile_info['recipe_objcopy_hex_pattern']

	if eep_path:
		text += '%s: %s\n\t' % (eep_path, elf_path)
		text += '@echo "%s %s..."\n\t' % ('%(Creating)s', eep_path)
		text += '%s\n\n' % compile_info['recipe_objcopy_eep_pattern']

	text += '%s:' % elf_path
	text += ' %s' % core_ar_path
	for prj_src in prj_src_list:
		prj_obj = src_obj_dict[prj_src]
		text += ' %s' % prj_obj
	text += '\n\t'
	
	text += '@echo "%s %s..."\n\t' % ('%(Creating)s', elf_path)
	prj_obj_list_text = ''
	for prj_src in prj_src_list:
		prj_obj = src_obj_dict[prj_src]
		prj_obj_list_text += ' "%s"' % prj_obj
	cmd_text = compile_info['recipe_c_combine_pattern'].replace('$@', prj_obj_list_text)
	text += '%s\n\n' % cmd_text

	text += '%s:' % core_ar_path
	for core_src in core_src_list:
		core_obj = src_obj_dict[core_src]
		text += ' %s' % core_obj
	text += '\n\t'

	text += '@echo "%s %s..."\n\t' % ('%(Creating)s', core_ar_path)
	core_obj_list_text = ''
	for core_src in core_src_list:
		core_obj = src_obj_dict[core_src]
		core_obj_list_text += ' "%s"' % core_obj
	cmd_text = compile_info['recipe_ar_pattern'].replace('"$@"', core_obj_list_text)
	text += '%s\n\n' % cmd_text

	for src in src_list:
		ext = os.path.splitext(src)[1]
		if ext == '.c' or ext == '.cc':
			cmd_text = compile_info['recipe_c_o_pattern']
		elif ext == '.cpp' or ext == '.cxx':
			cmd_text = compile_info['recipe_cpp_o_pattern']
		elif ext == '.ino' or ext == '.pde':
			cmd_text = compile_info['recipe_cpp_o_pattern']
			index = cmd_text.index('"-I')
			line_before = cmd_text[:index]
			line_after = cmd_text[index:]
			cmd_text = line_before + '-x c++ ' + line_after
		text += '%s: %s\n\t' % (src_obj_dict[src], src)
		text += '@echo "%s %s..."\n\t' % ('%(Creating)s', src_obj_dict[src])
		text += '%s\n\n' % cmd_text
	new_text = text % cur_lang.getDisplayTextDict()
	file_name = 'makefile'
	file_path = os.path.join(prj_folder, file_name)

	encoding = codecs.lookup(locale.getpreferredencoding()).name
	writeFile(file_path, new_text, encoding)

	path_list = [compile_info['gcc_root']]
	if not compile_info['uploader_root'] in path_list:
		path_list.append(compile_info['uploader_root'])
	compile_info['prj_folder'] = prj_folder
	compile_info['path_list'] = path_list
	genScriptFile(prj_folder, path_list, mode)

	regex = compile_info['recipe_size_regex']
	upload_maximum_size = compile_info['upload_maximum_size']
	if 'cmd_path' in compile_info:
		uploader = compile_info['cmd_path']
	else:
		uploader = compile_info['cmd']

	compile_info['platform'] = platform
	compile_info['bin_path'] = bin_path
	compile_info['programmer'] = programmer

	ram_size_dict = {}
	ram_size_dict['attiny44'] = '256'
	ram_size_dict['attiny45'] = '256'
	ram_size_dict['attiny84'] = '512'
	ram_size_dict['attiny85'] = '512'
	ram_size_dict['atmega8'] = '1024'
	ram_size_dict['atmega168'] = '1024'
	ram_size_dict['atmega328p'] = '1024'
	ram_size_dict['atmega1280'] = '4096'
	ram_size_dict['atmega2560'] = '8196'
	ram_size_dict['atmega32u4'] = '2560'
	ram_size_dict['at90usb162'] = '512'
	ram_size_dict['at90usb646'] = '4096'
	ram_size_dict['at90usb1286'] = '8192'
	ram_size_dict['cortex-m3'] = '98304'
	ram_size_dict['cortex-m4'] = '16384'

	if not 'upload_maximum_ram_size' in compile_info:
		if compile_info['build_mcu'] in ram_size_dict:
			compile_info['upload_maximum_ram_size'] = ram_size_dict[compile_info['build_mcu']]
		else:
			compile_info['upload_maximum_ram_size'] = 'unknown'
	global compile_cmd
	compile_cmd = compile_info
	return (main_src_number, prj_folder, regex, upload_maximum_size, uploader)

def formatCPP(org_text, level = 0):
	patern = re.compile(r'for\s*?\([\S\s]+?\)')
	match = patern.search(org_text)
	org_text = org_text.replace('/*', '\n/*')
	org_text = org_text.replace('*/', '*/\n')
	if '/*' in org_text:
		index_before = org_text.index('/*')
		line_before = org_text[:index_before]
		index_after = org_text.index('*/')
		line_after = org_text[index_after+2:]
		line_middle = org_text[index_before:index_after+2]
		(text_before, level) = formatCPP(line_before, level)
		text_middle = ''
		lines = line_middle.split('\n')
		for line in lines:
			# line = line.strip()
			if '*/' in line:
				level -= 1
			text_middle += '\t' * level
			text_middle += '%s\n' % line
			if '/*' in line:
				level += 1
		text_middle += '\n'
		(text_after, level) = formatCPP(line_after, level)
		text = text_before + text_middle + text_after
	elif '//' in org_text:
		index_before = org_text.index('//')
		line_before = org_text[:index_before]
		org_text = org_text[index_before:]
		index_after = org_text.index('\n')
		line_middle = org_text[:index_after+1]
		line_after = org_text[index_after+1:]
		(text_before, level) = formatCPP(line_before, level)
		
		in_line = True
		line_before_middle = line_before + line_middle
		lines = line_before_middle.split('\n')
		line = lines[-2]
		line = line.strip()
		if line[:2] == '//':
			in_line = False

		if not in_line:
			text_middle = '\t' * level
			text_middle += line_middle
		else:
			text_before = text_before.rstrip() + ' '
			text_middle = line_middle
		(text_after, level) = formatCPP(line_after, level)
		text = text_before + text_middle + text_after
	elif '"' in org_text:
		index_before = org_text.index('"')
		line_before = org_text[:index_before]
		org_text = org_text[index_before+1:]
		index_after = org_text.index('"')
		line_middle = '"'
		while(org_text[index_after-1] == '\\'):
			line_middle += org_text[:index_after+1]
			org_text = org_text[index_after+1:]
			index_after = org_text.index('"')
		line_middle += org_text[:index_after+1]
		line_after = org_text[index_after+1:]

		if '#' in line_before.split('\n')[-1]:
			index = line_after.index('\n')
			line_after = line_after[:index] + '%(auto_format_line_break)s' + line_after[index+1:]

		(text_before, level) = formatCPP(line_before, level)
		(text_after, level) = formatCPP(line_after, level)
		text_middle = line_middle
		text_before = text_before.rstrip()
		if text_before[-1] != '(':
			text_before += ' '
		text_after = text_after.lstrip()
		text = text_before + text_middle + text_after
	elif match:
		sep = match.group()
		length = len(sep)
		index_before = org_text.index(sep)
		index_after = index_before + length
		line_before = org_text[:index_before]
		line_after = org_text[index_after:]
		(text_before, level) = formatCPP(line_before, level)
		(text_after, level) = formatCPP(line_after, level)
		pattern = re.compile(r'\S+')
		letter_list = pattern.findall(sep)
		sep = ''
		for letter in letter_list:
			if letter[0] == '(':
				sep = sep[:-1] + letter
			else:
				sep += letter
			sep += ' '
		sep = sep[:-1]
		if text_after.strip()[0] != '{':
			sep += '\n\t'
		text_middle = '\t' * level
		text_middle += sep
		text = text_before + text_middle + text_after
	else:
		text = ''
		lines = org_text.split('\n')
		for line in lines:
			line = line.strip()
			if line:
				text += line
				text += ' '
		org_text = text
		text = ''
		pattern = re.compile(r'\S+')
		org_text = org_text.replace('{', '\n{\n')
		org_text = org_text.replace('}', '\n}\n')
		org_text = org_text.replace(';', ';\n')
		org_text = org_text.replace('#', '\n#')
		org_text = org_text.replace('(', ' (')
		lines = org_text.split('\n')
		for line in lines:
			line = line.strip()
			if line:
				if '}' in line:
					level -= 1
				if '{' in line:
					text += '\n'
				text += '\t' * level
				letter_list = pattern.findall(line)
				for letter in letter_list:
					if letter[0] == '(':
						text = text[:-1] + '%s ' % letter
					elif letter == ';':
						if len(letter_list) == 1:
							text += '%s ' % letter
						else:
							text = text[:-1] + '%s ' % letter
					else:
						text += '%s ' % letter
				if ';' in line or '#' in line or '{' in line or '}' in line:
					text = text[:-1]
					text += '\n'
				if letter_list[-1] == '}':
					text += '\n'
				if '{' in line:
					level += 1
	return (text, level)

def autoFormat(view):
	edit = view.begin_edit()
	org_text = view.substr(sublime.Region(0, view.size()))
	(text, level) = formatCPP(org_text)
	text = text.replace('%(auto_format_line_break)s ', '\n')
	view.replace(edit, sublime.Region(0, view.size()), text)
	view.end_edit(edit)