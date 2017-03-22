#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sublime

from . import file


def get_user_path():
    """."""
    packages_path = sublime.packages_path()
    user_path = os.path.join(packages_path, 'User')
    return user_path


def get_plugin_config_path(plugin_name):
    """."""
    user_path = get_user_path()
    config_path = os.path.join(user_path, plugin_name)
    file.check_dir(config_path)
    return config_path


def get_plugin_menu_path(plugin_name):
    """."""
    config_path = get_plugin_config_path(plugin_name)
    menu_path = os.path.join(config_path, 'menu')
    file.check_dir(menu_path)
    return menu_path
