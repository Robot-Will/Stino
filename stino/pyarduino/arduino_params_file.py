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


def get_key_value(line):
    key, value = '', ''
    if '=' in line:
        index = line.index('=')
        key = line[:index].strip()
        value = line[(index + 1):].strip()
    return (key, value)


class ParamsFile(base.abs_file.File):
    def __init__(self, path):
        super(ParamsFile, self).__init__(path)
        self.param_pairs = []
        self.load_param_pairs()

    def get_params(self):
        return dict(self.param_pairs)

    def load_param_pairs(self):
        text = self.read()
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                params_pair = get_key_value(line)
                self.param_pairs.append(params_pair)
