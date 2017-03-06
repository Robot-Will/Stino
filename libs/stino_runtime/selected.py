#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os


def get_package_names(pkgs_info):
    """."""
    package_names = pkgs_info.get('names', [])
    return package_names


def get_package_info(pkgs_info, pkg_name):
    """."""
    package_info = pkgs_info.get(pkg_name, {})
    return package_info


def get_platform_names(pkgs_info, pkg_name):
    """."""
    package_info = get_package_info(pkgs_info, pkg_name)
    platforms_info = package_info.get('platforms', {})
    platform_names = platforms_info.get('names', [])
    return platform_names


def get_platform_arches(pkgs_info, pkg_name):
    """."""
    package_info = get_package_info(pkgs_info, pkg_name)
    platforms_info = package_info.get('platforms', {})
    platform_names = platforms_info.get('arches', [])
    return platform_names


def get_platform_versions_info(pkgs_info, pkg_name, ptfm_name):
    """."""
    package_info = get_package_info(pkgs_info, pkg_name)
    platforms_info = package_info.get('platforms', {})
    ptfm_ver_info = platforms_info.get(ptfm_name, {})
    return ptfm_ver_info


def get_platform_versions(pkgs_info, pkg_name, ptfm_name):
    """."""
    ptfm_ver_info = get_platform_versions_info(pkgs_info, pkg_name, ptfm_name)
    platform_versions = ptfm_ver_info.get('versions', [])
    return platform_versions


def get_platform_info(pkgs_info, pkg_name, ptfm_name, ptfm_ver):
    """."""
    ptfm_ver_info = get_platform_versions_info(pkgs_info, pkg_name, ptfm_name)
    ptfm_info = ptfm_ver_info.get(ptfm_ver, {})
    return ptfm_info


def get_platform_name_by_arch(arduino_info, pkg_name, ptfm_arch):
    """."""
    ptfm_name = ''
    pkgs_info = arduino_info.get('packages', {})
    ptfm_names = get_platform_names(pkgs_info, pkg_name)
    ptfm_arches = get_platform_arches(pkgs_info, pkg_name)
    if ptfm_arch in ptfm_arches:
        index = ptfm_arches.index(ptfm_arch)
        ptfm_name = ptfm_names[index]
    return ptfm_name


def get_sel_platform_info(arduino_info):
    """."""
    pkgs_info = arduino_info.get('packages', {})
    sel_pkg = arduino_info['selected'].get('package')
    sel_ptfm = arduino_info['selected'].get('platform')
    sel_ver = arduino_info['selected'].get('version')
    ptfm_info = get_platform_info(pkgs_info, sel_pkg, sel_ptfm, sel_ver)
    return ptfm_info


def get_sel_board_info(arduino_info):
    """."""
    sel_board = arduino_info['selected'].get('board')
    board_info = arduino_info['boards'].get(sel_board, {})

    sel_board_info = board_info.get('generic', {})
    options = board_info.get('options', [])
    for option in options:
        key = 'option_%s' % option
        sel_value_name = arduino_info['selected'].get(key, '')
        values_info = board_info.get(option, {})
        value_info = values_info.get(sel_value_name, {})
        sel_board_info.update(value_info)
    return sel_board_info


def get_sel_programmer_info(arduino_info):
    """."""
    sel_programmer = arduino_info['selected'].get('programmer')
    programmer_info = arduino_info['programmers'].get(sel_programmer, {})
    return programmer_info


def get_sel_platform_path(arduino_info):
    """."""
    platform_path = ''
    sel_pkg = arduino_info['selected'].get('package')
    sel_ver = arduino_info['selected'].get('version')
    if sel_pkg and sel_ver:
        platform_info = get_sel_platform_info(arduino_info)
        arch = platform_info.get('architecture')

        arduino_app_path = arduino_info['arduino_app_path']
        packages_path = os.path.join(arduino_app_path, 'packages')
        package_path = os.path.join(packages_path, sel_pkg)
        hardware_path = os.path.join(package_path, 'hardware')
        platforms_path = os.path.join(hardware_path, arch)
        platform_path = os.path.join(platforms_path, sel_ver)
    return platform_path
