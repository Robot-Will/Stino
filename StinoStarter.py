#-*- coding: utf-8 -*-
# StinoStarter.py

import os
import sublime
import sublime_plugin

st_version = int(sublime.version())
if st_version < 3000:
	import app
else:
	from . import app

class SketchListener(sublime_plugin.EventListener):
	def on_activated(self, view):
		pre_active_sketch = app.constant.global_settings.get('active_sketch', '')

		if not app.sketch.isInEditor(view):
			return

		app.active_file.setView(view)
		active_sketch = app.active_file.getSketchName()
		app.constant.global_settings.set('active_sketch', active_sketch)

		if app.active_file.isSrcFile():
			app.active_serial_listener.start()
			temp_global = app.constant.global_settings.get('temp_global', False)
			if temp_global:
				app.constant.global_settings.set('global_settings', False)
				app.constant.global_settings.set('temp_global', False)
			global_settings = app.constant.global_settings.get('global_settings', True)
			if not global_settings:
				if not (active_sketch == pre_active_sketch):
					folder = app.active_file.getFolder()
					app.constant.sketch_settings.changeFolder(folder)
					app.arduino_info.refresh()
					app.main_menu.refresh()
		else:
			app.active_serial_listener.stop()
			global_settings = app.constant.global_settings.get('global_settings', True)
			if not global_settings:
				app.constant.global_settings.set('global_settings', True)
				app.constant.global_settings.set('temp_global', True)
				folder = app.constant.stino_root
				app.constant.sketch_settings.changeFolder(folder)
				app.arduino_info.refresh()
				app.main_menu.refresh()

	def on_close(self, view):
		if app.serial_monitor.isMonitorView(view):
			name = view.name()
			serial_port = name.split('-')[1].strip()
			if serial_port in app.constant.serial_in_use_list:
				cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
				cur_serial_monitor.stop()
				app.constant.serial_in_use_list.remove(serial_port)

class ShowArduinoMenuCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_arduino_menu = not app.constant.global_settings.get('show_arduino_menu', True)
		app.constant.global_settings.set('show_arduino_menu', show_arduino_menu)
		app.main_menu.refresh()

	def is_checked(self):
		state = app.constant.global_settings.get('show_arduino_menu', True)
		return state

class NewSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		caption = app.i18n.translate('Name for New Sketch')
		self.window.show_input_panel(caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		sketch_name = input_text
		if sketch_name:
			sketch_file = app.base.newSketch(sketch_name)
			if sketch_file:
				self.window.open_file(sketch_file)
				app.arduino_info.refresh()
				app.main_menu.refresh()
			else:
				app.output_console.printText('A sketch (or folder) named "%s" already exists. Could not create the sketch.\n' % sketch_name)

class OpenSketchCommand(sublime_plugin.WindowCommand):
	def run(self, folder):
		app.sketch.openSketchFolder(folder)

class ImportLibraryCommand(sublime_plugin.WindowCommand):
	def run(self, folder):
		view = app.active_file.getView()
		self.window.active_view().run_command('save')
		app.sketch.importLibrary(view, folder)

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class ShowSketchFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		folder = app.active_file.getFolder()
		url = 'file://' + folder
		sublime.run_command('open_url', {'url': url})

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class SetExtraFlagCommand(sublime_plugin.WindowCommand):
	def run(self):
		extra_flag = app.constant.sketch_settings.get('extra_flag', '')
		caption = app.i18n.translate('Extra compilation flags:')
		self.window.show_input_panel(caption, extra_flag, self.on_done, None, None)

	def on_done(self, input_text):
		extra_flag = input_text
		app.constant.sketch_settings.set('extra_flag', extra_flag)

class CompileSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		cur_folder = app.active_file.getFolder()
		cur_project = app.sketch.Project(cur_folder)

		args = app.compiler.Args(cur_project, app.arduino_info)
		compiler = app.compiler.Compiler(app.arduino_info, cur_project, args)
		compiler.run()

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class UploadSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		cur_folder = app.active_file.getFolder()
		cur_project = app.sketch.Project(cur_folder)

		args = app.compiler.Args(cur_project, app.arduino_info)
		compiler = app.compiler.Compiler(app.arduino_info, cur_project, args)
		compiler.run()
		uploader = app.uploader.Uploader(args, compiler)
		uploader.run()

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class UploadUsingProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.active_view().run_command('save')
		cur_folder = app.active_file.getFolder()
		cur_project = app.sketch.Project(cur_folder)

		args = app.compiler.Args(cur_project, app.arduino_info)
		compiler = app.compiler.Compiler(app.arduino_info, cur_project, args)
		compiler.run()
		uploader = app.uploader.Uploader(args, compiler, mode = 'programmer')
		uploader.run()

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			platform_list = app.arduino_info.getPlatformList()
			platform_id = app.constant.sketch_settings.get('platform', -1)
			if (platform_id > 0) and (platform_id < len(platform_list)):
				platform = platform_list[platform_id]
				programmer_list = platform.getProgrammerList()
				if programmer_list:
					state = True
		return state

class ChooseBoardCommand(sublime_plugin.WindowCommand):
	def run(self, platform, board):
		cur_platform = app.arduino_info.getPlatformList()[platform]
		app.constant.sketch_settings.set('platform', platform)
		app.constant.sketch_settings.set('platform_name', cur_platform.getName())
		app.constant.sketch_settings.set('board', board)
		app.main_menu.refresh()
		app.constant.sketch_settings.set('full_compilation', True)

	def is_checked(self, platform, board):
		state = False
		chosen_platform = app.constant.sketch_settings.get('platform', -1)
		chosen_board = app.constant.sketch_settings.get('board', -1)
		if platform == chosen_platform and board == chosen_board:
			state = True
		return state

class ChooseBoardOptionCommand(sublime_plugin.WindowCommand):
	def run(self, board_option, board_option_item):
		has_setted = False
		chosen_platform = app.constant.sketch_settings.get('platform')
		chosen_board = app.constant.sketch_settings.get('board')
		board_id = str(chosen_platform) + '.' + str(chosen_board)
		board_option_settings = app.constant.sketch_settings.get('board_option', {})
		if board_id in board_option_settings:
			cur_board_option_setting = board_option_settings[board_id]
			if board_option < len(cur_board_option_setting):
				has_setted = True

		if not has_setted:
			platform_list = app.arduino_info.getPlatformList()
			cur_platform = platform_list[chosen_platform]
			board_list = cur_platform.getBoardList()
			cur_board = board_list[chosen_board]
			board_option_list = cur_board.getOptionList()
			board_option_list_number = len(board_option_list)
			cur_board_option_setting = []
			for i in range(board_option_list_number):
				cur_board_option_setting.append(0)

		cur_board_option_setting[board_option] = board_option_item
		board_option_settings[board_id] = cur_board_option_setting
		app.constant.sketch_settings.set('board_option', board_option_settings)
		app.constant.sketch_settings.set('full_compilation', True)

	def is_checked(self, board_option, board_option_item):
		state = False
		chosen_platform = app.constant.sketch_settings.get('platform', -1)
		chosen_board = app.constant.sketch_settings.get('board', -1)
		board_id = str(chosen_platform) + '.' + str(chosen_board)
		board_option_settings = app.constant.sketch_settings.get('board_option', {})
		if board_id in board_option_settings:
			cur_board_option_setting = board_option_settings[board_id]
			if board_option < len(cur_board_option_setting):
				chosen_board_option_item = cur_board_option_setting[board_option]
				if board_option_item == chosen_board_option_item:
					state = True
		return state

class ChooseProgrammerCommand(sublime_plugin.WindowCommand):
	def run(self, platform, programmer):
		programmer_settings = app.constant.sketch_settings.get('programmer', {})
		programmer_settings[str(platform)] = programmer
		app.constant.sketch_settings.set('programmer', programmer_settings)

	def is_checked(self, platform, programmer):
		state = False
		programmer_settings = app.constant.sketch_settings.get('programmer', {})
		if str(platform) in programmer_settings:
			chosen_programmer = programmer_settings[str(platform)]
			if programmer == chosen_programmer:
				state = True
		return state

class BurnBootloaderCommand(sublime_plugin.WindowCommand):
	def run(self):
		cur_folder = app.active_file.getFolder()
		cur_project = app.sketch.Project(cur_folder)

		args = app.compiler.Args(cur_project, app.arduino_info)
		bootloader = app.uploader.Bootloader(cur_project, args)
		bootloader.burn()

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class ChooseSerialPortCommand(sublime_plugin.WindowCommand):
	def run(self, serial_port):
		app.constant.sketch_settings.set('serial_port', serial_port)

	def is_checked(self, serial_port):
		state = False
		chosen_serial_port = app.constant.sketch_settings.get('serial_port', -1)
		if serial_port == chosen_serial_port:
			state = True
		return state

class StartSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
		serial_port_list = app.serial.getSerialPortList()
		serial_port = serial_port_list[serial_port_id]
		if serial_port in app.constant.serial_in_use_list:
			cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
		else:
			cur_serial_monitor = app.serial_monitor.SerialMonitor(serial_port)
			app.constant.serial_in_use_list.append(serial_port)
			app.constant.serial_monitor_dict[serial_port] = cur_serial_monitor
		cur_serial_monitor.start()
		self.window.run_command('send_serial_text')

	def is_enabled(self):
		state = False
		serial_port_list = app.serial.getSerialPortList()
		if serial_port_list:
			serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
			serial_port = serial_port_list[serial_port_id]
			if serial_port in app.constant.serial_in_use_list:
				cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
				if not cur_serial_monitor.isRunning():
					state = True
			else:
				state = True
		return state

class StopSerialMonitorCommand(sublime_plugin.WindowCommand):
	def run(self):
		serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
		serial_port_list = app.serial.getSerialPortList()
		serial_port = serial_port_list[serial_port_id]
		cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
		cur_serial_monitor.stop()

	def is_enabled(self):
		state = False
		serial_port_list = app.serial.getSerialPortList()
		if serial_port_list:
			serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
			serial_port = serial_port_list[serial_port_id]
			if serial_port in app.constant.serial_in_use_list:
				cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
				if cur_serial_monitor.isRunning():
					state = True
		return state

class SendSerialTextCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.caption = 'Send'
		self.window.show_input_panel(self.caption, '', self.on_done, None, None)

	def on_done(self, input_text):
		serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
		serial_port_list = app.serial.getSerialPortList()
		serial_port = serial_port_list[serial_port_id]
		cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
		cur_serial_monitor.send(input_text)
		self.window.show_input_panel(self.caption, '', self.on_done, None, None)

	def is_enabled(self):
		state = False
		serial_port_list = app.serial.getSerialPortList()
		if serial_port_list:
			serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
			serial_port = serial_port_list[serial_port_id]
			if serial_port in app.constant.serial_in_use_list:
				cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
				if cur_serial_monitor.isRunning():
					state = True
		return state

class ChooseLineEndingCommand(sublime_plugin.WindowCommand):
	def run(self, line_ending):
		app.constant.sketch_settings.set('line_ending', line_ending)

	def is_checked(self, line_ending):
		state = False
		chosen_line_ending = app.constant.sketch_settings.get('line_ending', 0)
		if line_ending == chosen_line_ending:
			state = True
		return state

class ChooseDisplayModeCommand(sublime_plugin.WindowCommand):
	def run(self, display_mode):
		app.constant.sketch_settings.set('display_mode', display_mode)

	def is_checked(self, display_mode):
		state = False
		chosen_display_mode = app.constant.sketch_settings.get('display_mode', 0)
		if display_mode == chosen_display_mode:
			state = True
		return state

class ChooseBaudrateCommand(sublime_plugin.WindowCommand):
	def run(self, baudrate):
		app.constant.sketch_settings.set('baudrate', baudrate)

	def is_checked(self, baudrate):
		state = False
		chosen_baudrate = app.constant.sketch_settings.get('baudrate', -1)
		if baudrate == chosen_baudrate:
			state = True
		return state

	def is_enabled(self):
		state = True
		serial_port_list = app.serial.getSerialPortList()
		if serial_port_list:
			serial_port_id = app.constant.sketch_settings.get('serial_port', 0)
			serial_port = serial_port_list[serial_port_id]
			if serial_port in app.constant.serial_in_use_list:
				cur_serial_monitor = app.constant.serial_monitor_dict[serial_port]
				if cur_serial_monitor.isRunning():
					state = False
		return state

class AutoFormatCommand(sublime_plugin.WindowCommand):
	def run(self):
		self.window.run_command('reindent', {'single_line': False})

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class ArchiveSketchCommand(sublime_plugin.WindowCommand):
	def run(self):
		root_list = app.fileutil.getOSRootList()
		self.top_folder_list = root_list
		self.folder_list = self.top_folder_list
		self.level = 0
		self.show_panel()

	def show_panel(self):
		folder_name_list = app.fileutil.getFolderNameList(self.folder_list)
		sublime.set_timeout(lambda: self.window.show_quick_panel(folder_name_list, self.on_done), 10)

	def on_done(self, index):
		is_finished = False
		if index == -1:
			return

		if self.level != 0 and index == 0:
			chosen_folder = self.folder_list[index]
			chosen_folder = chosen_folder.split('(')[1]
			chosen_folder = chosen_folder[:-1]

			source_folder = app.active_file.getFolder()
			sketch_name = app.active_file.getSketchName()
			zip_file_name = sketch_name + '.zip'
			zip_file = os.path.join(chosen_folder, zip_file_name)
			return_code = app.tools.archiveSketch(source_folder, zip_file)
			if return_code == 0:
				app.output_console.printText(app.i18n.translate('Writing {0} done.\n', [zip_file]))
			else:
				app.output_console.printText(app.i18n.translate('Writing {0} failed.\n', [zip_file]))
		else:
			(self.folder_list, self.level) = app.fileutil.enterNextLevel(index, self.folder_list, self.level, self.top_folder_list)
			self.show_panel()

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class ChooseArduinoFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		root_list = app.fileutil.getOSRootList()
		self.top_folder_list = root_list
		self.folder_list = self.top_folder_list
		self.level = 0
		self.show_panel()

	def show_panel(self):
		folder_name_list = app.fileutil.getFolderNameList(self.folder_list)
		sublime.set_timeout(lambda: self.window.show_quick_panel(folder_name_list, self.on_done), 10)

	def on_done(self, index):
		is_finished = False
		if index == -1:
			return

		chosen_folder = self.folder_list[index]
		if app.base.isArduinoFolder(chosen_folder):
			app.output_console.printText(app.i18n.translate('Arduino Application is found at {0}.\n', [chosen_folder]))
			app.constant.sketch_settings.set('arduino_folder', chosen_folder)
			app.arduino_info.refresh()
			app.main_menu.refresh()
			app.output_console.printText('Arduino %s.\n' % app.arduino_info.getVersionText())
			app.constant.sketch_settings.set('full_compilation', True)
		else:
			(self.folder_list, self.level) = app.fileutil.enterNextLevel(index, self.folder_list, self.level, self.top_folder_list)
			self.show_panel()

class ChangeSketchbookFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		root_list = app.fileutil.getOSRootList()
		self.top_folder_list = root_list
		self.folder_list = self.top_folder_list
		self.level = 0
		self.show_panel()

	def show_panel(self):
		folder_name_list = app.fileutil.getFolderNameList(self.folder_list)
		sublime.set_timeout(lambda: self.window.show_quick_panel(folder_name_list, self.on_done), 10)

	def on_done(self, index):
		is_finished = False
		if index == -1:
			return

		if self.level != 0 and index == 0:
			chosen_folder = self.folder_list[index]
			chosen_folder = chosen_folder.split('(')[1]
			chosen_folder = chosen_folder[:-1]
			app.output_console.printText(app.i18n.translate('Sketchbook is changed to {0}.\n', [chosen_folder]))
			app.constant.global_settings.set('sketchbook_folder', chosen_folder)
			app.arduino_info.refresh()
			app.main_menu.refresh()
			app.constant.sketch_settings.set('full_compilation', True)
		else:
			(self.folder_list, self.level) = app.fileutil.enterNextLevel(index, self.folder_list, self.level, self.top_folder_list)
			self.show_panel()

class ChooseBuildFolderCommand(sublime_plugin.WindowCommand):
	def run(self):
		root_list = app.fileutil.getOSRootList()
		self.top_folder_list = root_list
		self.folder_list = self.top_folder_list
		self.level = 0
		self.show_panel()

	def show_panel(self):
		folder_name_list = app.fileutil.getFolderNameList(self.folder_list)
		sublime.set_timeout(lambda: self.window.show_quick_panel(folder_name_list, self.on_done), 10)

	def on_done(self, index):
		is_finished = False
		if index == -1:
			return

		if self.level != 0 and index == 0:
			chosen_folder = self.folder_list[index]
			chosen_folder = chosen_folder.split('(')[1]
			chosen_folder = chosen_folder[:-1]
			app.output_console.printText(app.i18n.translate('Build folder is changed to {0}.\n', [chosen_folder]))
			app.constant.sketch_settings.set('build_folder', chosen_folder)
			app.constant.sketch_settings.set('full_compilation', True)
		else:
			(self.folder_list, self.level) = app.fileutil.enterNextLevel(index, self.folder_list, self.level, self.top_folder_list)
			self.show_panel()

class ChooseLanguageCommand(sublime_plugin.WindowCommand):
	def run(self, language):
		pre_language = app.constant.global_settings.get('language', -1)
		if language != pre_language:
			app.constant.global_settings.set('language', language)
			app.i18n.refresh()
			app.main_menu.refresh()

	def is_checked(self, language):
		state = False
		chosen_language = app.constant.global_settings.get('language', -1)
		if language == chosen_language:
			state = True
		return state

class SetGlobalSettingCommand(sublime_plugin.WindowCommand):
	def run(self):
		if app.active_file.isSrcFile():
			global_settings = not app.constant.global_settings.get('global_settings', True)
			app.constant.global_settings.set('global_settings', global_settings)

			if global_settings:
				folder = app.constant.stino_root
			else:
				folder = app.active_file.getFolder()
			app.constant.sketch_settings.changeFolder(folder)
			app.arduino_info.refresh()
			app.main_menu.refresh()
		else:
			temp_global = not app.constant.global_settings.get('temp_global', False)
			app.constant.global_settings.set('temp_global', temp_global)

	def is_checked(self):
		state = app.constant.global_settings.get('global_settings', True)
		return state

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class SetFullCompilationCommand(sublime_plugin.WindowCommand):
	def run(self):
		full_compilation = not app.constant.sketch_settings.get('full_compilation', True)
		app.constant.sketch_settings.set('full_compilation', full_compilation)

	def is_checked(self):
		state = app.constant.sketch_settings.get('full_compilation', True)
		return state

class ShowCompilationOutputCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_compilation_output = not app.constant.sketch_settings.get('show_compilation_output', False)
		app.constant.sketch_settings.set('show_compilation_output', show_compilation_output)

	def is_checked(self):
		state = app.constant.sketch_settings.get('show_compilation_output', False)
		return state

class ShowUploadOutputCommand(sublime_plugin.WindowCommand):
	def run(self):
		show_upload_output = not app.constant.sketch_settings.get('show_upload_output', False)
		app.constant.sketch_settings.set('show_upload_output', show_upload_output)

	def is_checked(self):
		state = app.constant.sketch_settings.get('show_upload_output', False)
		return state

class SetBareGccOnlyCommand(sublime_plugin.WindowCommand):
	def run(self):
		set_bare_gcc_only = not app.constant.sketch_settings.get('set_bare_gcc_only', False)
		app.constant.sketch_settings.set('set_bare_gcc_only', set_bare_gcc_only)

	def is_checked(self):
		state = app.constant.sketch_settings.get('set_bare_gcc_only', False)
		return state

class VerifyCodeCommand(sublime_plugin.WindowCommand):
	def run(self):
		verify_code = not app.constant.sketch_settings.get('verify_code', False)
		app.constant.sketch_settings.set('verify_code', verify_code)

	def is_checked(self):
		state = app.constant.sketch_settings.get('verify_code', False)
		return state


class OpenRefCommand(sublime_plugin.WindowCommand):
	def run(self, url):
		url = app.base.getUrl(url)
		sublime.run_command('open_url', {'url': url})

class FindInReferenceCommand(sublime_plugin.WindowCommand):
	def run(self):
		ref_list = []
		keyword_ref_dict = app.arduino_info.getKeywordRefDict()
		view = app.active_file.getView()
		selected_word_list = app.base.getSelectedWordList(view)
		for selected_word in selected_word_list:
			if selected_word in keyword_ref_dict:
				ref = keyword_ref_dict[selected_word]
				if not ref in ref_list:
					ref_list.append(ref)
		for ref in ref_list:
			url = app.base.getUrl(ref)
			sublime.run_command('open_url', {'url': url})

	def is_enabled(self):
		state = False
		if app.active_file.isSrcFile():
			state = True
		return state

class AboutStinoCommand(sublime_plugin.WindowCommand):
	def run(self):
		sublime.run_command('open_url', {'url': 'https://github.com/Robot-Will/Stino'})

class PanelOutputCommand(sublime_plugin.TextCommand):
	def run(self, edit, text):
		pos = self.view.size()
		self.view.insert(edit, pos, text)
		self.view.show(pos)

class InsertIncludeCommand(sublime_plugin.TextCommand):
	def run(self, edit, include_text):
		view_size = self.view.size()
		region = sublime.Region(0, view_size)
		src_text = self.view.substr(region)
		include_list = app.preprocess.genIncludeList(src_text)
		if include_list:
			last_include = include_list[-1]
			index = src_text.index(last_include) + len(last_include)
		else:
			index = 0
		self.view.insert(edit, index, include_text)
