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
    def __init__(self, path, is_top_level=True, is_big_project=False):
        super(Sketchbook, self).__init__(path)
        self.is_big_project = is_big_project
        self.sub_sketches = []
        self.load_sub_sketches(is_top_level)

    def load_sub_sketches(self, is_top_level):
        sub_dirs = []
        if is_top_level:
            sub_dirs = self.list_dirs()
            sub_dirs = [d for d in sub_dirs
                        if not d.name.lower() in non_sketch_dirs]
        if is_top_level and self.is_big_project:
            is_top_level = False
        sub_sketches = [Sketchbook(d.path, is_top_level) for d in sub_dirs]
        self.sub_sketches = [s for s in sub_sketches if s.is_sketch()]

    def has_primary_file(self):
        return has_primary_file(self.path, self.name)

    def is_sketch(self):
        return (self.sub_sketches or self.has_primary_file())

    def get_sub_sketches(self):
        return self.sub_sketches

    def set_name(self, name):
        self.name = name


def has_primary_file(dir_path, project_name):
    state = False
    exts = ['.ino', '.pde', '.cpp', '.c', '.S']
    for ext in exts:
        primary_file_name = project_name + ext
        primary_file_path = os.path.join(dir_path, primary_file_name)
        if os.path.isfile(primary_file_path):
            state = True
            break
    return state
