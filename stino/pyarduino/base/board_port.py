# Documents
#

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


class BoardPort:
    def __init__(self):
        self.address = ''
        self.protocol = ''
        self.board_name = ''
        self.label = ''
        self.params = {}

    def get_address(self):
        return self.address

    def set_address(self, address):
        self.address = address

    def get_protocol(self):
        return self.protocol

    def set_protocol(self, protocol):
        self.protocol = protocol

    def get_board_name(self):
        return self.board_name

    def set_board_name(self, board_name):
        self.board_name = board_name

    def get_label(self):
        return self.label

    def set_label(self, label):
        self.label = label

    def get_params(self):
        return self.params

    def set_params(self, params):
        self.params = params
