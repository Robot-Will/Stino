#-*- coding: utf-8 -*-
# stino/actions.py

import stino
import zipfile
import os

def changeArduinoRoot(arduino_root):
	pre_arduino_root = stino.const.settings.get('arduino_root')
	stino.arduino_info.setArduinoRoot(arduino_root)
	stino.arduino_info.genVersion()
	version_text = stino.arduino_info.getVersionText()
	display_text = 'Arduino {1} is found at {2}.\n'
	msg = stino.cur_language.translate(display_text)
	msg = msg.replace('{1}', version_text)
	msg = msg.replace('{2}', arduino_root)
	stino.log_panel.addText(msg)

	if arduino_root != pre_arduino_root:
		stino.arduino_info.update()
		stino.const.settings.set('full_compilation', True)
		stino.const.save_settings()
		stino.cur_menu.fullUpdate()
		
def changeSketchbookRoot(sketchbook_root):
	sketchbook_root = stino.utils.getInfoFromKey(sketchbook_root)[1]
	pre_sketchbook_root = stino.const.settings.get('sketchbook_root')
	stino.arduino_info.setSketchbookRoot(sketchbook_root)
	display_text = 'Sketchbook folder has been changed to {1}.\n'
	msg = stino.cur_language.translate(display_text)
	msg = msg.replace('{1}', sketchbook_root)
	stino.log_panel.addText(msg)

	if sketchbook_root != pre_sketchbook_root:
		stino.arduino_info.sketchbookUpdate()
		stino.cur_menu.update()

def updateSerialMenu():
	stino.cur_menu.update()

def getArchiveFolderPath(zip_folder_path, sketch_folder_path):
	base_path = sketch_folder_path + os.path.sep
	all_file_list = stino.osfile.findAllFiles(sketch_folder_path)
	all_file_list = [file_path.replace(base_path, '') for file_path in all_file_list]

	zip_folder_path = stino.utils.getInfoFromKey(zip_folder_path)[1]
	sketch_name = stino.src.getSketchNameFromFolder(sketch_folder_path)
	zip_file_name = sketch_name + '.zip'
	zip_file_path = os.path.join(zip_folder_path, zip_file_name)
	opened_zipfile = zipfile.ZipFile(zip_file_path, 'w' ,zipfile.ZIP_DEFLATED)
	os.chdir(sketch_folder_path)
	for cur_file in all_file_list:
		opened_zipfile.write(cur_file)
	opened_zipfile.close()

	display_text = 'Writing {1} completed.\n'
	msg = stino.cur_language.translate(display_text)
	msg = msg.replace('{1}', zip_file_path)
	stino.log_panel.addText(msg)