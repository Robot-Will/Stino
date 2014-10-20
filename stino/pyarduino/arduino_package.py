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
from . import arduino_platform


class Package(base.abs_file.Dir):
    def __init__(self, root_id, path):
        super(Package, self).__init__(path)
        self.id = root_id + '.' + self.name
        self.platforms = []
        self.load_platforms()

    def get_id(self):
        return self.id

    def get_platforms(self):
        return self.platforms

    def get_platform(self, platform_id):
        return self.id_platform_dict.get(platform_id, None)

    def load_platforms(self):
        if self.has_file('boards.txt'):
            platform = arduino_platform.Platform(self.id, self.path)
            if platform.is_platform():
                self.platforms.append(platform)
        else:
            sub_dirs = self.list_dirs()
            for sub_dir in sub_dirs:
                if sub_dir.has_file('boards.txt'):
                    platform = arduino_platform.Platform(self.id, sub_dir.path)
                    if platform.is_platform():
                        self.platforms.append(platform)
        platform_ids = [p.id for p in self.platforms]
        self.id_platform_dict = dict(zip(platform_ids, self.platforms))

    def is_package(self):
        return bool(self.platforms)
