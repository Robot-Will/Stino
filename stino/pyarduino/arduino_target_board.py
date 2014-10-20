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

from . import base


class TargetBoardInfo(object):
    def __init__(self, root_dirs):
        self.target_board = None
        self.target_sub_boards = []
        self.settings = base.settings.get_arduino_settings()
        self.update(root_dirs)

    def update(self, root_dirs):
        self.root_dirs = root_dirs
        self.check_target_board()

    def check_target_board(self):
        boards = load_boards(self.root_dirs)
        if boards:
            board_ids = [board.get_id() for board in boards]
            target_board_id = self.settings.get('target_board_id', '')
            if not target_board_id in board_ids:
                target_board_id = board_ids[0]
                self.settings.set('target_board_id', target_board_id)
            index = board_ids.index(target_board_id)
            self.target_board = boards[index]
            if self.target_board.has_options():
                self.check_target_sub_boards()

    def check_target_sub_boards(self):
        self.target_sub_boards = []
        if self.target_board and self.target_board.has_options():
            target_board_id = self.target_board.get_id()
            board_options = self.target_board.get_options()
            for option_index, option in enumerate(board_options):
                target_sub_board_info = TargetSubBoardInfo(self.target_board,
                                                           option_index)
                target_sub_board = target_sub_board_info.get_target_sub_board()
                self.target_sub_boards.append(target_sub_board)
            target_sub_board_ids = [
                sb.get_id() for sb in self.target_sub_boards]
            self.settings.set(target_board_id, target_sub_board_ids)

    def change_target_board(self, board_id):
        self.settings.set('target_board_id', board_id)
        self.check_target_board()

    def change_target_sub_board(self, option_index, sub_board_id):
        if self.target_board and self.target_board.has_options():
            target_board_id = self.target_board.get_id()
            target_sub_board_ids = self.settings.get(target_board_id)
            target_sub_board_ids[option_index] = sub_board_id
            self.settings.set(target_board_id, target_sub_board_ids)
            self.check_target_sub_boards()

    def get_target_board(self):
        return self.target_board

    def get_target_sub_boards(self):
        return self.target_sub_boards

    def get_target_arch(self):
        target_board_id = self.target_board.get_id()
        ids = target_board_id.split('.')
        target_arch = ids[-2]
        return target_arch

    def get_params(self):
        params = {}
        if self.target_board:
            params.update(self.target_board.get_params())
            for target_sub_board in self.target_sub_boards:
                params.update(target_sub_board.get_params())
        return params


class TargetSubBoardInfo(object):
    def __init__(self, target_board, option_index):
        self.target_sub_board = None
        self.target_board = target_board
        self.option_index = option_index
        self.settings = base.settings.get_arduino_settings()
        self.check_target_sub_board()

    def check_target_sub_board(self):
        if self.target_board:
            target_board_id = self.target_board.get_id()
            target_sub_board_ids = self.settings.get(target_board_id, [])

            if self.option_index < len(target_sub_board_ids):
                target_sub_board_id = target_sub_board_ids[self.option_index]
                options = self.target_board.get_options()
                option = options[self.option_index]
                self.target_sub_board = option.get_item(target_sub_board_id)

            if not self.target_sub_board:
                options = self.target_board.get_options()
                option = options[self.option_index]
                sub_boards = option.get_items()
                self.target_sub_board = sub_boards[0]

    def get_target_sub_board(self):
        return self.target_sub_board

    def get_params(self):
        return self.target_sub_board.get_params()


def load_boards(root_dirs):
    boards = []
    for root_dir in root_dirs:
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                boards += platform.get_boards()
    return boards
