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


class TargetProgrammerInfo(object):
    def __init__(self, root_dirs):
        self.target_programmer = None
        self.settings = base.settings.get_arduino_settings()
        self.update(root_dirs)

    def update(self, root_dirs):
        self.root_dirs = root_dirs
        self.check_target_programmer()

    def check_target_programmer(self):
        programmers = load_programmers(self.root_dirs)
        if programmers:
            programmer_ids = [
                programmer.get_id() for programmer in programmers]
            target_programmer_id = self.settings.get(
                'target_programmer_id', '')
            if not target_programmer_id in programmer_ids:
                target_programmer_id = programmer_ids[0]
                self.settings.set('target_programmer_id', target_programmer_id)
            index = programmer_ids.index(target_programmer_id)
            self.target_programmer = programmers[index]

    def change_target_programmer(self, programmer_id):
        self.settings.set('target_programmer_id', programmer_id)
        self.check_target_programmer()

    def get_target_programmer(self):
        return self.target_programmer

    def get_params(self):
        params = {}
        if self.target_programmer:
            params.update(self.target_programmer.get_params())
        return params


def load_programmers(root_dirs):
    programmers = []
    for root_dir in root_dirs:
        for package in root_dir.get_packages():
            for platform in package.get_platforms():
                programmers += platform.get_programmers()
    return programmers
