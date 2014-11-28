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


class TargetPlatform(object):
    def __init__(self, root_dirs):
        self.target_platform = None
        self.root_dirs = root_dirs
        self.settings = base.settings.get_arduino_settings()
        self.update()

    def update(self):
        target_board_id = self.settings.get('target_board_id', '')
        if target_board_id:
            ids = target_board_id.split('.')[:-1]
            target_platform_id = '.'.join(ids)

            for root_dir in self.root_dirs:
                for package in root_dir.get_packages():
                    for platform in package.get_platforms():
                        if platform.get_id() == target_platform_id:
                            self.target_platform = platform
                            break
                    if self.target_platform:
                        break
                if self.target_platform:
                    break

    def get_target_platform(self):
        return self.target_platform

    def get_target_platform_file(self):
        return self.target_platform_file
