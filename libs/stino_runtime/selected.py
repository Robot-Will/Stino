#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os


def get_sel_platform_path(arduino_info):
    """."""
    arduino_path = arduino_info['arduino_app_path']
    sel_package = arduino_info['selected'].get('package')
    sel_platform = arduino_info['selected'].get('platform')
    sel_version = arduino_info['selected'].get('version')

    package_infos = arduino_info.get('packages', {})
    package_info = package_infos.get(sel_package, {})
    platform_infos = package_info.get('platforms', {})
    platform_info = platform_infos.get(sel_platform, {})
    version_info = platform_info.get(sel_version, [])
    arch = version_info.get('architecture')

    packages_path = os.path.join(arduino_path, 'packages')
    package_path = os.path.join(packages_path, sel_package)
    hardware_path = os.path.join(package_path, 'hardware')
    platforms_path = os.path.join(hardware_path, arch)
    version_path = os.path.join(platforms_path, sel_version)
    return version_path
