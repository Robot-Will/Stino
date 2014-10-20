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

import os

from . import base

non_sketch_dirs = ['hardware', 'examples', 'libraries']


class Sketchbook(base.abs_file.Dir):
    def __init__(self, path):
        super(Sketchbook, self).__init__(path)
        primary_file_name = self.name + '.ino'
        primary_file_path = os.path.join(self.path, primary_file_name)
        self.primary_file = base.abs_file.File(primary_file_path)
        self.sub_sketches = []
        self.load_sub_sketches()

    def load_sub_sketches(self):
        sub_dirs = self.list_dirs()
        sub_dirs = [d for d in sub_dirs
                    if not d.name.lower() in non_sketch_dirs]
        sub_sketches = [Sketchbook(d.path) for d in sub_dirs]
        self.sub_sketches = [s for s in sub_sketches if s.is_sketch()]

    def is_sketch(self):
        return (self.sub_sketches or self.primary_file.is_file())

    def get_sub_sketches(self):
        return self.sub_sketches

    def set_name(self, name):
        self.name = name
