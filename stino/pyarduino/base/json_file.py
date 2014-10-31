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

import json

from . import abs_file


class JSONFile(abs_file.File):
    def __init__(self, path):
        super(JSONFile, self).__init__(path)
        self.data = {}
        self.load()

    def set_data(self, data):
        self.data = data
        self.save()

    def get_data(self):
        return self.data

    def load(self):
        text = self.read()
        try:
            self.data = json.loads(text)
        except (ValueError):
            print('Error while loading Json file %s.' % self.path)

    def save(self):
        text = json.dumps(self.data, sort_keys=True, indent=4)
        self.write(text)
