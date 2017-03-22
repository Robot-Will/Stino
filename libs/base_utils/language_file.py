#!/usr/bin/env python
#-*- coding: utf-8 -*-

# 1. Copyright
# 2. Lisence
# 3. Author

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from . import abs_file


class LanguageFile(abs_file.File):
    def __init__(self, path):
        super(LanguageFile, self).__init__(path)
        text = self.read()
        self.trans_dict = load_trans_dict(text)

    def get_trans_dict(self):
        return self.trans_dict


def load_trans_dict(text):
    trans_dict = {}
    lines = text.split('\n')
    lines = [line.strip() for line in lines if lines if line.strip() and
             not line.strip().startswith('#')]
    blocks = split_lines(lines)
    for block in blocks:
        key, value = load_trans_pair(block)
        trans_dict[key] = value
    return trans_dict


def split_lines(lines):
    blocks = []
    block = []
    for line in lines:
        if line.startswith('msgid'):
            blocks.append(block)
            block = []
        block.append(line)
    blocks.append(block)
    blocks.pop(0)
    return blocks


def load_trans_pair(block):
    is_key = True
    key = ''
    value = ''
    for line in block:
        index = line.index('"')
        cur_str = line[index + 1: -1]
        if line.startswith('msgstr'):
            is_key = False
        if is_key:
            key += cur_str
        else:
            value += cur_str
    return (key, value)
