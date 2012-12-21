#-*- coding: utf-8 -*-

import sublime, sublime_plugin
import os, zipfile, re
from stino import stmenu, lang, utils, arduino
import threading
import time
import serial

##
Setting_File = 'Stino.sublime-settings'
Settings = sublime.load_settings(Setting_File)
Settings.set('plugin_root', utils.genPluginRoot())
sublime.save_settings(Setting_File)

serial_listen = False
opened_serial_list = []
opened_serial_id_dict = {}
serial_monitor_state_dict = {}

## 
cur_lang = lang.Lang()
arduino_info = arduino.ArduinoInfo()
cur_menu = stmenu.STMenu(arduino_info, cur_lang)
##

def showInfoText(view):
	version_text = arduino_info.getVersionText()
	text = 'Arduino %s' % version_text
	board = Settings.get('board')
	text += ', %s' % board
	has_processor = arduino_info.hasProcessor(board)
	if has_processor:
		processor = Settings.get('processor')
		text += ', %s' % processor
	has_programmer = arduino_info.hasProgrammer()
	if has_programmer:
		programmer = Settings.get('programmer')
		text += ', %s' % programmer
	serial_port_list = utils.getSerialPortList()
	if serial_port_list:
		serial_port = Settings.get('serial_port')
		text += ', %s' % serial_port
	view.set_status('Arduino', text)

class SerialListenerCommand(sublime_plugin.ApplicationCommand):
	def run(self):
		t = threading.Thread(target = self.startListener)
		t.start()

	def startListener(self):
		global serial_listen
		serial_listen = True
		pre_serial_list = utils.getSerialPortList()
		while serial_listen:
			serial_list = utils.getSerialPortList()
			if serial_list != pre_serial_list:
				cur_menu.serialUpdate()
				pre_serial_list = serial_list
			time.sleep(0.5)

class SketchListener(sublime_plugin.EventListener):
	def on_activated(self, view):
		global opened_serial_list
		global serial_listen

		state = False
		file_name = view.file_name()
		state = utils.isSketch(file_name)
		pre_state = Settings.get('show_Arduino_menu')
		pre_serial_menu_state = Settings.get('show_serial_menu')

		serial_menu_state = False
		if 'Serial Monitor' in view.name():
			serial_port = view.name().split('-')[1].strip()
			if serial_port in opened_serial_list:
				serial_menu_state = True
				view.window().run_command('serial_send')
		
		if state != pre_state:
			Settings.set('show_Arduino_menu', state)
			sublime.save_settings(Setting_File)
			cur_menu.update()

		if serial_menu_state != pre_serial_menu_state:
			Settings.set('show_serial_menu', serial_menu_state)
			sublime.save_settings(Setting_File)
			cur_menu.update()

		if state:
			arduino_root = Settings.get('Arduino_root')
			if arduino.isArduinoFolder(arduino_root):
				showInfoText(view)
				sublime.run_command('serial_listener')
			else:
				text = 'Please select Arduino folder'
				view.set_status('Arduino', text)
				serial_listen = False
		else:
			view.erase_status('Arduino')
			serial_listen = False

	def on_close(self, view):
		global serial_monitor_state_dict
		if 'Serial Monitor' in view.name():
			serial_port = view.name().split('-')[1].strip()
			serial_monitor_state_dict[serial_port] = False

class ShowArduinoMenuCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_arduino_menu = not Settings.get('show_Arduino_menu')
		Settings.set('show_Arduino_menu', show_arduino_menu)
		sublime.save_settings(Setting_File)
		cur_menu.update()

	def is_checked(self):
		state = False
		if Settings.get('show_Arduino_menu'):
			state = True
		return state

class NewSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		org_caption = '%(Name_for_new_sketch:)s'
		caption = org_caption % cur_lang.getDisplayTextDict()
		self.window.show_input_panel(caption, '', self.on_done, None, self.on_cancel)

	def on_done(self, input_text):
		sketchbook_root = arduino_info.getSketchbookRoot()
		is_new = True
		sketch_name = utils.regFilename(input_text)
		if sketch_name:
			sketch_folder_path = os.path.join(sketchbook_root, sketch_name)
			if os.path.exists(sketch_folder_path):
				org_msg = '%(Sketch_Exists)s'
				msg = org_msg % cur_lang.getDisplayTextDict()
				is_new = sublime.ok_cancel_dialog(msg)
		else:
			is_new = False

		if is_new:
			if not os.path.exists(sketch_folder_path):
				os.mkdir(sketch_folder_path)
			sketch_file_name = '%s.ino' % sketch_name
			sketch_file_path = os.path.join(sketch_folder_path, sketch_file_name)

			# Write Sketch File
			plugin_root = utils.getPluginRoot()
			template_dir = os.path.join(plugin_root, 'template')
			temp_path = os.path.join(template_dir, 'sketch')
			temp_file = open(temp_path, 'r')
			sketch = temp_file.read()
			temp_file.close()

			utils.writeFile(sketch_file_path, sketch)
			cur_menu.sketchbookUpdate()

			#open a new window for new project
			utils.openSketch(sketch_folder_path)	
		else:
			org_caption = '%(Name_for_new_sketch:)s'
			caption = org_caption % cur_lang.getDisplayTextDict()
			self.window.show_input_panel(caption, '', self.on_done, None, self.on_cancel)
	
	def on_cancel(self):
		pass

class SelectSketchCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		sketch = menu_str
		sketch_folder = arduino_info.getSketchFolder(sketch)
		utils.openSketch(sketch_folder)

class NewToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		org_caption = '%(Name_for_new_file:)s'
		caption = org_caption % cur_lang.getDisplayTextDict()
		self.window.show_input_panel(caption, '', self.on_done, None, self.on_cancel)

	def on_done(self, input_text):
		active_file = self.window.active_view().file_name()
		sketch_folder = os.path.split(active_file)[0]
		is_new = True
		file_name = utils.regFilename(input_text)
		if file_name:
			file_path = os.path.join(sketch_folder, file_name)
			if os.path.exists(file_path):
				is_new = False
		if is_new:
			text = '// %s\n\n' % file_name
			utils.writeFile(file_path, text)
			view = self.window.open_file(file_path)
		else:
			org_msg = '%(File_Exists)s'
			msg = org_msg % cur_lang.getDisplayTextDict()
			is_new = sublime.message_dialog(msg)

	def on_cancel(self):
		pass

class AddToSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.level = 0
		self.top_path_list = utils.getTopDirList()
		self.path_list = self.top_path_list
		self.window.show_quick_panel(self.path_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			active_file = self.window.active_view().file_name()
			sketch_folder = os.path.split(active_file)[0]
			is_new = True
			basename = os.path.split(sel_path)[1]
			basename = utils.regFilename(basename)
			file_path = os.path.join(sketch_folder, basename)
			if os.path.exists(file_path):
				is_new = False
			if is_new:
				content = utils.readFile(sel_path)
				utils.writeFile(file_path, content)
				view = self.window.open_file(file_path)
			else:
				org_msg = '%(File_Exists)s'
				msg = org_msg % cur_lang.getDisplayTextDict()
				is_new = sublime.message_dialog(msg)
		else:		
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path)
			file_list = utils.getFileList(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		self.window.active_view().run_command('save')
		filename = self.window.active_view().file_name()
		header_list_in_file = utils.getHeaderList(filename)
		lib_list = utils.getLibList(arduino_info)
		lib_paths = utils.getExtLibPaths(header_list_in_file, lib_list)
		
		lib = menu_str
		lib_path = arduino_info.getLibFolder(lib)
		if not lib_path.replace(os.path.sep, '/') in lib_paths:
			header_list = utils.getLibHeaderList(lib_path)
			utils.insertHeadList(self.window.active_view(), header_list)

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		active_file = self.window.active_view().file_name()
		folder_path = os.path.split(active_file)[0]
		file_list = utils.listDir(folder_path)

		self.level = 0
		self.top_path_list = [os.path.join(folder_path, cur_file) for cur_file in file_list]
		self.path_list = self.top_path_list
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			view = self.window.open_file(sel_path)
		else:
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path)
			file_list = utils.getFileList(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class CompileSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.runBuild(self.window, arduino_info, cur_lang)
		Settings.set('full_compilation', False)
		sublime.save_settings(Setting_File)

class UploadBinaryCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.runBuild(self.window, arduino_info, cur_lang, mode = 'upload')
		Settings.set('full_compilation', False)
		sublime.save_settings(Setting_File)

class UploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.runBuild(self.window, arduino_info, cur_lang, mode = 'upload_using_programmer')
		Settings.set('full_compilation', False)
		sublime.save_settings(Setting_File)

	def is_enabled(self):
		state = arduino_info.hasProgrammer()
		return state

class SelectBoardCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		board = menu_str
		pre_board = Settings.get('board')
		if board != pre_board:
			Settings.set('board', board)
			Settings.set('full_compilation', True)
			sublime.save_settings(Setting_File)
			cur_menu.boardUpdate()
			showInfoText(self.window.active_view())

	def is_checked(self, menu_str):
		state = False
		board = Settings.get('board')
		if menu_str == board:
			state = True
		return state

class SelectProcessorCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		processor = menu_str
		pre_processor = Settings.get('processor')
		if processor != pre_processor:
			Settings.set('processor', processor)
			sublime.save_settings(Setting_File)
			showInfoText(self.window.active_view())

	def is_checked(self, menu_str):
		state = False
		processor = Settings.get('processor')
		if menu_str == processor:
			state = True
		return state

class NoProcessor(sublime_plugin.WindowCommand):
	def is_visible(self):
		return False

class SelectSerialPortCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		serial_port = menu_str
		pre_serial_port = Settings.get('serial_port')
		if serial_port != pre_serial_port:
			Settings.set('serial_port', serial_port)
			sublime.save_settings(Setting_File)
			showInfoText(self.window.active_view())

	def is_checked(self, menu_str):
		state = False
		serial_port = Settings.get('serial_port')
		if menu_str == serial_port:
			state = True
		return state

class SelectProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		programmer = menu_str
		pre_programmer = Settings.get('programmer')
		if programmer != pre_programmer:
			Settings.set('programmer', programmer)
			sublime.save_settings(Setting_File)
			showInfoText(self.window.active_view())

	def is_checked(self, menu_str):
		state = False
		programmer = Settings.get('programmer')
		if menu_str == programmer:
			state = True
		return state

class BurnBootloaderCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.runBuild(self.window, arduino_info, cur_lang, mode = 'burn_bootloader')

	def is_enabled(self):
		state = arduino_info.hasProgrammer()
		return state

class SelectLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		language = menu_str
		pre_language = Settings.get('language')
		if language != pre_language:
			Settings.set('language', language)
			sublime.save_settings(Setting_File)
			cur_lang.update()
			cur_menu.genFile(cur_lang.getDisplayTextDict())

	def is_checked(self, menu_str):
		state = False
		language = Settings.get('language')
		if menu_str == language:
			state = True
		return state

class SelectArduinoFolderCommand(sublime_plugin.WindowCommand):
	""" Select Arduino Folder """
	def run(self):
		self.level = 0
		self.top_path_list = utils.getTopDirList()
		self.path_list = self.top_path_list
		self.window.show_quick_panel(self.path_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if arduino.isArduinoFolder(sel_path):
			(ver_text, ver) = arduino.genVersion(sel_path)
			text = '%s: %s\n%s: %s' % ('%(Arduino)s', sel_path, '%(Version)s', ver_text)
			msg = text % cur_lang.getDisplayTextDict()
			sublime.message_dialog(msg)

			if ver < 100 or ver == 150:
				text = '%(Version_Not_Supported)s'
				msg = text % cur_lang.getDisplayTextDict()
				sublime.message_dialog(msg)
			else:
				pre_arduino_root = Settings.get('Arduino_root')
				if sel_path != pre_arduino_root:
					Settings.set('Arduino_root', sel_path)
					Settings.set('full_compilation', True)
					sublime.save_settings(Setting_File)
					cur_menu.fullUpdate()
		else:		
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path, False)
			file_list = utils.getFileList(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class AddSketchbookFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.level = 0
		self.top_path_list = utils.getTopDirList(mode = 'sketchbook')
		self.path_list = self.top_path_list
		text = '%(Select_Folder)s'
		msg = text % cur_lang.getDisplayTextDict()
		sublime.message_dialog(msg)
		self.window.show_quick_panel(self.path_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		if self.level > 0 and index == 0:
			pre_sketchbook_root = arduino_info.getSketchbookRoot()
			sketchbook_root = os.path.split(self.path_list[1])[0]
			if not sketchbook_root == pre_sketchbook_root:
				Settings.set('sketchbook_root', sketchbook_root)
				sublime.save_settings(Setting_File)
				cur_menu.fullUpdate()
		else:
			sel_path = self.path_list[index]
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path, False)
			file_list = utils.getFileList(self.path_list)
			if not self.path_list == self.top_path_list:
				text = '%(Select_Current_Folder)s'
				msg = text % cur_lang.getDisplayTextDict()
				self.path_list.insert(0, msg)
				file_list.insert(0, msg)
			self.window.show_quick_panel(file_list, self.on_done)

class ToggleFullCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		full_compilation = not Settings.get('full_compilation')
		Settings.set('full_compilation', full_compilation)
		sublime.save_settings(Setting_File)

	def is_checked(self):
		state = False
		full_compilation = Settings.get('full_compilation')
		if full_compilation:
			state = True
		return state

class ToggleVerboseCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_compilation = not Settings.get('verbose_compilation')
		Settings.set('verbose_compilation', verbose_compilation)
		sublime.save_settings(Setting_File)

	def is_checked(self):
		state = False
		verbose_compilation = Settings.get('verbose_compilation')
		if verbose_compilation:
			state = True
		return state

class ToggleVerboseUploadCommand(sublime_plugin.WindowCommand):
	def run(self):
		verbose_upload = not Settings.get('verbose_upload')
		Settings.set('verbose_upload', verbose_upload)
		sublime.save_settings(Setting_File)

	def is_checked(self):
		state = False
		verbose_upload = Settings.get('verbose_upload')
		if verbose_upload:
			state = True
		return state

class ToggleVerifyCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		verify_code = not Settings.get('verify_code')
		Settings.set('verify_code', verify_code)
		sublime.save_settings(Setting_File)


	def is_checked(self):
		state = False
		verify_code = Settings.get('verify_code')
		if verify_code:
			state = True
		return state

class AutoFormatCommand(sublime_plugin.WindowCommand):
	def run(self):
		utils.autoFormat(self.window.active_view())

class ArchiveSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		file_path = self.window.active_view().file_name()
		file_folder_path = os.path.split(file_path)[0]
		self.file_list = utils.findAllFiles(file_folder_path)
		os.chdir(file_folder_path)
		file_folder_path += os.path.sep
		self.file_list = [f.replace(file_folder_path, '') for f in self.file_list]
		file_basename = os.path.split(file_path)[1]
		file_name = os.path.splitext(file_basename)[0]
		self.zip_file = '%s.zip' % file_name

		self.level = 0
		self.top_path_list = utils.getTopDirList(mode = 'Archive')
		self.path_list = self.top_path_list
		text = '%(Select_Folder)s'
		msg = text % cur_lang.getDisplayTextDict()
		sublime.message_dialog(msg)
		self.window.show_quick_panel(self.path_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		if self.level > 0 and index == 0:
			cur_path = os.path.split(self.path_list[1])[0]
			zip_path = os.path.join(cur_path, self.zip_file)
			opened_zipfile = zipfile.ZipFile(zip_path, 'w' ,zipfile.ZIP_DEFLATED) 
			for file_path in self.file_list:
				opened_zipfile.write(file_path)
			opened_zipfile.close()
		else:
			sel_path = self.path_list[index]
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path, False)
			file_list = utils.getFileList(self.path_list)
			if not self.path_list == self.top_path_list:
				text = '%(Select_Current_Folder)s'
				msg = text % cur_lang.getDisplayTextDict()
				self.path_list.insert(0, msg)
				file_list.insert(0, msg)
			self.window.show_quick_panel(file_list, self.on_done)

class FixEncodingCommand(sublime_plugin.WindowCommand):
	def run(self):
		state = True
		if self.window.active_view().is_dirty():
			text = '%(Discard_All_Changes)s'
			msg = text % cur_lang.getDisplayTextDict()
			state = sublime.ok_cancel_dialog(msg)
	
		if state:
			file_path = self.window.active_view().file_name()
			content = utils.readFile(file_path)
			edit = self.window.active_view().begin_edit()
			self.window.active_view().replace(edit, sublime.Region(0, self.window.active_view().size()), content)
			self.window.active_view().end_edit(edit)

class SelectBaudrateCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		baudrate = menu_str
		Settings.set('baudrate', baudrate)
		sublime.save_settings(Setting_File)

	def is_checked(self, menu_str):
		state = False
		baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
		baudrate = Settings.get('baudrate')
		if not baudrate in baudrate_list:
			baudrate = '9600'
		if menu_str == baudrate:
			state = True
		return state

class SerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		global opened_serial_list
		self.serial_port = Settings.get('serial_port')
		baudrate_list = ['300', '1200', '2400', '4800', '9600', '14400', '19200', '28800', '38400', '57600', '115200']
		self.baudrate = Settings.get('baudrate')
		if not self.baudrate in baudrate_list:
			self.baudrate = '9600'
		
		is_open = False
		view_name = 'Serial Monitor-%s' % self.serial_port
		windows = sublime.windows()
		for window in windows:
			views = window.views()
			for view in views:
				if view.name() == view_name:
					cur_view = view
					window.focus_view(view)
					is_open = True
					break
			if is_open:
				break
		if not is_open:
			cur_view = self.window.new_file()
			cur_view.set_name(view_name)
			Settings.set('show_serial_menu', True)
			sublime.save_settings(Setting_File)
			cur_menu.update()
			cur_view.run_command('toggle_setting', {'setting': 'word_wrap'})
		self.view = cur_view
		
		opened_serial_list.append(self.serial_port)
		self.window.run_command('serial_send')

		self.text_to_add = ''
		t = threading.Thread(target = self.startMonitor)
		t.start()

	def startMonitor(self):
		global opened_serial_list
		global opened_serial_id_dict
		global serial_monitor_state_dict

		ser = serial.Serial()
		ser.port = self.serial_port
		ser.baudrate = int(self.baudrate)
		ser.open()

		opened_serial_id_dict[self.serial_port] = ser
		serial_monitor_state_dict[self.serial_port] = True
		while serial_monitor_state_dict[self.serial_port]:
			number = ser.inWaiting()
			text = ser.read(number)
			self.text_to_add += text
			sublime.set_timeout(self.update, 0)
			time.sleep(0.1)
		ser.close()
		opened_serial_list.remove(self.serial_port)
		opened_serial_id_dict[self.serial_port] = None

	def update(self):
		if len(self.text_to_add):
			if self.view.size() > 10000:
				view_edit = self.view.begin_edit()
				self.view.replace(view_edit, self.view.size(), '')
				self.view.end_edit(view_edit)
			view_edit = self.view.begin_edit()
			self.text_to_add= self.text_to_add.replace('\r', '')
			self.view.insert(view_edit, self.view.size(), self.text_to_add)
			self.view.end_edit(view_edit)
			self.view.show(self.view.size())
			self.text_to_add = ''

	def is_enabled(self):
		state = False
		serial_port = Settings.get('serial_port')
		serial_list = utils.getSerialPortList()
		if serial_list:
			if not serial_port in serial_list:
				serial_port = serial_list[0]
				Settings.set('serial_port', serial_port)
				sublime.save_settings('Stino.sublime-settings')
			if utils.isPortAvailable(serial_port):
				state = True
		return state

class SerialSendCommand(sublime_plugin.WindowCommand):
	def run(self):
		global opened_serial_list
		name = self.window.active_view().name()
		if 'Serial Monitor' in name:
			serial_port = name.split('-')[1].strip()
			if serial_port in opened_serial_list:
				text = '%(Send)s'
				caption = text % cur_lang.getDisplayTextDict()
				self.window.show_input_panel(caption, '', self.on_done, None, self.on_cancel)

	def on_done(self, input_text):
		global opened_serial_list
		global opened_serial_id_dict
		name = self.window.active_view().name()
		if 'Serial Monitor' in name:
			serial_port = name.split('-')[1].strip()
			if serial_port in opened_serial_list:
				if input_text:
					ser = opened_serial_id_dict[serial_port]
					ser.write(input_text)
					text = '\n%s: %s\n' % ('%(Send)s', input_text)
					display_text = text % cur_lang.getDisplayTextDict()
					view = self.window.active_view()
					edit = view.begin_edit()
					view.insert(edit, view.size(), display_text)
					view.end_edit(edit)
					view.show(view.size())
				text = '%(Send)s'
				caption = text % cur_lang.getDisplayTextDict()
				self.window.show_input_panel(caption, '', self.on_done, None, self.on_cancel)

	def on_cancel(self):
		pass

	def is_enabled(self):
		global opened_serial_list
		state = False
		name = self.window.active_view().name()
		if 'Serial Monitor' in name:
			serial_port = name.split('-')[1].strip()
			if serial_port in opened_serial_list:
				state = True
		return state

class SerialStopCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.run_command('close')

	def is_enabled(self):
		global opened_serial_list
		state = False
		name = self.window.active_view().name()
		if 'Serial Monitor' in name:
			serial_port = name.split('-')[1].strip()
			if serial_port in opened_serial_list:
				state = True
		return state

class SelectExampleCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		example = menu_str
		example_path = arduino_info.getExampleFolder(example)
		file_list = utils.listDir(example_path)

		self.level = 0
		self.top_path_list = [os.path.join(example_path, cur_file) for cur_file in file_list]
		self.path_list = self.top_path_list
		self.window.show_quick_panel(file_list, self.on_done)

	def on_done(self, index):
		if index == -1:
			return

		sel_path = self.path_list[index]
		if os.path.isfile(sel_path):
			view = self.window.open_file(sel_path)
		else:
			(self.level, self.path_list) = utils.enterNext(index, self.level, self.top_path_list, sel_path)
			file_list = utils.getFileList(self.path_list)
			self.window.show_quick_panel(file_list, self.on_done)

class OpenRefCommand(sublime_plugin.WindowCommand):
	def run(self, menu_str):
		utils.openUrl(menu_str)

class FindInReferenceCommand(sublime_plugin.WindowCommand):
	def run(self):
		region_list = self.window.active_view().sel()
		for region in region_list:
			operator_list = []
			keyword_list = arduino_info.getKeywordList()
			for keyword in keyword_list:
				keyword_type = arduino_info.getKeywordType(keyword)
				keyword_ref = arduino_info.getKeywordRef(keyword)
				if (not keyword_type) and keyword_ref:
					if (not '[]' in keyword) and (not '()' in keyword) and (not '{}' in keyword):
						operator_list.append(keyword)

			regx_keyword_list = ['.', '^', '$', '*', '+', '?', '{', '[', ']', '\\', '|', '(', ')']
			word_region = self.window.active_view().word(region)
			words = self.window.active_view().substr(word_region)
			pattern_text = r'(\w+'
			for operator in operator_list:
				new_operator = ''
				for letter in operator:
					if letter in regx_keyword_list:
						letter = '\\' + letter
					new_operator += letter
				pattern_text += '|'
				pattern_text += new_operator
			pattern_text += ')'
			pattern = re.compile(pattern_text)
			match = pattern.search(words)
			word_list = []
			if match:
				word_list = pattern.findall(words)
		
			url_list = []
			msg_list = []
			for word in word_list:
				ref = arduino_info.getKeywordRef(word)
				if ref:
					if ref[0].isupper():
						if not ref in url_list:
							url_list.append(ref)
					else:
						msg = '"%s": %s\n' % (word, ref)
						if not msg in msg_list:
							msg_list.append(msg)
						
			msg_text = ''
			for msg in msg_list:
				msg_text += msg
			for url in url_list:
				utils.openUrl(url)
			if msg_text:
				sublime.message_dialog(msg_text)

	def is_enabled(self):
		state = True
		return state

class AboutStinoCommand(sublime_plugin.WindowCommand):
	def run(self):
		plugin_root = utils.getPluginRoot()
		readme_file = os.path.join(plugin_root, 'readme.txt')
		try:
			f = open(readme_file, 'r')
			text = f.read()
			f.close()
			encoding = codecs.lookup(locale.getpreferredencoding()).name
			if not isinstance(text, unicode):
				text = text.decode(encoding)
		except:
			text = '%(Stino_Lic)s'
			msg = text % cur_lang.getDisplayTextDict()
		sublime.message_dialog(msg)

class NotEnableCommand(sublime_plugin.WindowCommand):
	def run(self):
		pass

	def is_enabled(self):
		return False
########## End ##########
