#-*- coding: utf-8 -*-
# stino/utils.py

import re

info_sep = '$@@$'

def genKey(info, base_info):
	key = info + info_sep + base_info
	return key

def getInfoFromKey(key):
	info_list = key.split(info_sep)
	return info_list

def convertAsciiToUtf8(txt):
	if not isinstance(txt, unicode):
		try:
			txt = txt.decode('utf-8')
		except UnicodeDecodeError:
			from chardet import universaldetector
			detector = universaldetector.UniversalDetector()
			detector.feed(txt)
			detector.close()
			result = detector.result
			encoding = result['encoding']
			if encoding:
				try:
					txt = txt.decode(encoding)
				except UnicodeDecodeError:
					txt = splitTextToConvertToUtf8(txt, encoding)
			else:
				txt = splitTextToConvertToUtf8(txt, 'utf-8')
	return txt

def splitTextToConvertToUtf8(txt, encoding):
	if len(txt) == 1:
		txt = txt.decode(encoding, 'replace')
	else:
		if '\n' in txt:
			lines = convertTextToLines(txt)
			txt = ''
			for line in lines:
				line = convertAsciiToUtf8(line)
				txt += line
				txt += '\n'
		else:
			org_txt = txt
			txt = ''
			for character in org_txt:
				character = convertAsciiToUtf8(character)
				txt += character
	return txt

def convertTextToLines(txt):
	lines = txt.split('\n')
	return lines

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

def splitToBlocks(lines, sep = '.name', none_sep = None, key_length = 0):
	block_list = []
	block = []
	for line in lines:
		line = line.strip()
		if line and (not '#' in line):
			sep_condtion = sep in line
			none_sep_condition = True
			if none_sep:
				none_sep_condition = not none_sep in line
			length_condition = False
			if key_length > 0:
				if '=' in line:
					(key, value) = getKeyValue(line)
					key_list = key.split('.')
					length = len(key_list)
					if length == key_length:
						length_condition = True

			is_new_block = (sep_condtion and none_sep_condition) or length_condition
			if is_new_block:
				block_list.append(block)
				block = [line]
			else:
				block.append(line)
	block_list.append(block)
	block_list.pop(0)
	return block_list

def getTypeInfoBlock(board_info_block, board_type):
	info_block = []
	for line in board_info_block:
		if board_type in line:
			info_block.append(line)
	return info_block

def isLists(lists):
	state = False
	if lists:
		if isinstance(lists[0], list):
			state = True
	return state

def simplifyLists(lists):
	simple_list = []
	for cur_list in lists:
		simple_list += cur_list
	return simple_list

def getSelectedTextFromView(view):
	selected_text = ''
	region_list = view.sel()
	for region in region_list:
		selected_region = view.word(region)
		selected_text += view.substr(selected_region)
		selected_text += '\n'
	return selected_text

def removeRepeatItemFromList(info_list):
	simple_list = []
	for item in info_list:
		if not item in simple_list:
			simple_list.append(item)
	return simple_list

def removeWordsFromText(text, word_list):
	word_list.sort(key = len, reverse = True)
	for word in word_list:
		text = text.replace(word, '')
	text = re.sub(r'\s', '', text)
	return text

def getWordListFromText(text):
	pattern_text = r'\b\w+\b'
	word_list = re.findall(pattern_text, text)
	return word_list

def getOperatorListFromText(text, word_list, keyword_operator_list):
	operator_list = []
	text = removeWordsFromText(text, word_list)
	for operator in keyword_operator_list:
		if operator in text:
			operator_list.append(operator)
	return operator_list

def getKeywordListFromText(text, keyword_operator_list):
	word_list = getWordListFromText(text)
	word_list = removeRepeatItemFromList(word_list)
	operator_list = getOperatorListFromText(text, word_list, keyword_operator_list)
	keyword_list = word_list + operator_list
	return keyword_list

def getRefList(keyword_list, arduino_info, platform):
	ref_list = []
	msg_text = ''
	for keyword in keyword_list:
		if keyword in arduino_info.getKeywordList(platform):
			ref = arduino_info.getKeywordRef(platform, keyword)
			if ref:
				if ref[0].isupper():
					if not ref in ref_list:
						ref_list.append(ref)
				else:
					text = '%s: %s\n' % (keyword, ref)
					msg_text += text
	return (ref_list, msg_text)

