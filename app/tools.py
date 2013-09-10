#-*- coding: utf-8 -*-
# stino/tools.py

import os
import zipfile

from . import fileutil

def archiveSketch(source_folder, target_file):
	os.chdir(source_folder)
	file_name_list = fileutil.listDir(source_folder, with_dirs = False)
	try:
		opened_zipfile = zipfile.ZipFile(target_file, 'w' ,zipfile.ZIP_DEFLATED)
	except IOError:
		return_code = 1
	else:
		for file_name in file_name_list:
			opened_zipfile.write(file_name)
		opened_zipfile.close()
		return_code = 0
	return return_code
