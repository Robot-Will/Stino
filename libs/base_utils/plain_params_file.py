#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from . import sys_info
from . import file


def get_key_value(line):
    """."""
    if '=' in line:
        index = line.index('=')
        key = line[:index].strip()
        value = line[index + 1:].strip()
    else:
        key = line.strip()
        value = ''
    return key, value


def get_lines_with_head(lines, head):
    """."""
    block = []
    for line in lines:
        if line.startswith(head):
            block.append(line)
    return block


def value_is_name(line, name):
    """."""
    state = False
    key, value = get_key_value(line)
    if value == name:
        state = True
    return state


def get_names(lines):
    """."""
    names = []
    for line in lines:
        if '.name' in line:
            key, name = get_key_value(line)
            if name not in names:
                names.append(name)
    return names


def get_heads(lines):
    """."""
    heads = []
    for line in lines:
        key, value = get_key_value(line)
        if '.' in key:
            index = key.index('.')
            head = key[:index]
        else:
            head = key
        if head not in heads:
            heads.append(head)
    return heads


def get_lines_with_name(lines, name):
    """."""
    new_lines = []
    for line in lines:
        if value_is_name(line, name):
            head = line.split('.')[0]
            new_lines = get_lines_with_head(lines, head)
            break
    return new_lines


def get_blocks_by_names(lines, names):
        """."""
        for name in names:
            block = get_lines_with_name(lines, name)
            yield block


def get_blocks_by_heads(lines, heads):
        """."""
        for head in heads:
            block = get_lines_with_head(lines, head)
            yield block


def remove_block_head(block, head):
    """."""
    new_block = []
    for line in block:
        if line.startswith(head):
            index = len(head)
            line = line[index:]
            if line.startswith('.'):
                line = line[1:]
        new_block.append(line)
    return new_block


def get_generic_info(block):
    """."""
    generic_info = {}
    generic_block = get_generic_block(block)
    for line in generic_block:
        key, value = get_key_value(line)
        generic_info[key] = value
    return generic_info


def get_generic_block(block):
    """."""
    new_block = []
    for line in block:
        if not line.startswith('menu.'):
            new_block.append(line)
    return new_block


def get_option_block_info(block):
    """."""
    os_name = sys_info.get_os_name()

    block_info = {'names': []}
    heads = get_heads(block)
    item_blocks = get_blocks_by_heads(block, heads)
    for item_block in item_blocks:
        head = get_heads(item_block)[0]
        item_block = remove_block_head(item_block, head)
        item_info = {}
        item_name = ''
        for line in item_block:
            key, value = get_key_value(line)
            if not key:
                item_name = value
            elif key == 'windows':
                if os_name == 'windows':
                    item_name = value
            elif key == 'linux':
                if os_name == 'linux':
                    item_name = value
            elif key == 'macosx':
                if os_name == 'osx':
                    item_name = value
            else:
                item_info[key] = value
        if item_name:
            if item_name not in block_info['names']:
                block_info['names'].append(item_name)
            block_info[item_name] = item_info

    block_info['names'].sort(key=str.lower)
    return block_info


def get_menu_blocks_info(block, menu_info):
    """."""
    blocks_info = {'options': []}
    menu_names = menu_info['sub_menus'].get('names', [])
    for menu_name in menu_names:
        head = menu_info['sub_menus'].get(menu_name)
        option_block = get_lines_with_head(block, head)

        if option_block:
            blocks_info['options'].append(menu_name)
            option_block = remove_block_head(option_block, head)
            block_info = get_option_block_info(option_block)
            blocks_info[menu_name] = block_info
    return blocks_info


class PlainParamsFile(file.File):
    """."""

    def __init__(self, path):
        """."""
        super(PlainParamsFile, self).__init__(path)
        lines = self.read().split('\n')
        lines = (l.strip() for l in lines)
        self._lines = [l for l in lines if l and not l.startswith('#')]
        self._names = get_names(self._lines)
        self._names.sort(key=str.lower)

    def get_info(self):
        """."""
        info = {}
        for line in self._lines:
            key, value = get_key_value(line)
            info[key] = value
        return info


class BoardsFile(PlainParamsFile):
    """."""

    def __init__(self, path):
        """."""
        super(BoardsFile, self).__init__(path)

    def get_menu_info(self):
        """."""
        menu_info = {'sub_menus': {}}
        menu_info['sub_menus']['names'] = []

        lines = get_lines_with_head(self._lines, 'menu.')
        for line in lines:
            key, value = get_key_value(line)
            if value not in menu_info['sub_menus']['names']:
                menu_info['sub_menus']['names'].append(value)
            menu_info['sub_menus'][value] = key
        menu_info['sub_menus']['names'].sort(key=str.lower)
        return menu_info

    def get_boards_info(self):
        """."""
        boards_info = {'boards': {}}
        boards_info['boards']['names'] = self._names

        sub_menu_info = self.get_menu_info()
        boards_info.update(sub_menu_info)

        for name in self._names:
            boards_info['boards'][name] = {}
            block = get_lines_with_name(self._lines, name)
            head = get_heads(block)[0]
            block = remove_block_head(block, head)
            generic_info = get_generic_info(block)
            menu_blocks_info = get_menu_blocks_info(block, sub_menu_info)
            boards_info['boards'][name]['generic'] = generic_info
            boards_info['boards'][name].update(menu_blocks_info)
        return boards_info


class ProgrammersFile(PlainParamsFile):
    """."""

    def __init__(self, path):
        """."""
        super(ProgrammersFile, self).__init__(path)

    def get_programmers_info(self):
        """."""
        programmers_info = {'programmers': {}}
        programmers_info['programmers']['names'] = self._names

        for name in self._names:
            block = get_lines_with_name(self._lines, name)
            head = get_heads(block)[0]
            block = remove_block_head(block, head)
            generic_info = get_generic_info(block)
            programmers_info['programmers'][name] = generic_info
        return programmers_info
