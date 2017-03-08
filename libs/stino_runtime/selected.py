#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re

from base_utils import serial_port
from base_utils import plain_params_file


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


def get_platform_arch_by_name(arduino_info, pkg_name, ptfm_name):
    """."""
    ptfm_arch = ''
    pkgs_info = arduino_info.get('packages', {})
    ptfm_names = get_platform_names(pkgs_info, pkg_name)
    ptfm_arches = get_platform_arches(pkgs_info, pkg_name)
    if ptfm_name in ptfm_names:
        index = ptfm_names.index(ptfm_name)
        ptfm_arch = ptfm_arches[index]
    return ptfm_arch


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


def get_sel_board_options(arduino_info):
    """."""
    sel_board = arduino_info['selected'].get('board')
    board_info = arduino_info['boards'].get(sel_board, {})
    options = board_info.get('options', [])
    return options


def get_sel_programmer_info(arduino_info):
    """."""
    sel_programmer = arduino_info['selected'].get('programmer')
    programmer_info = arduino_info['programmers'].get(sel_programmer, {})
    return programmer_info


def get_sel_tools_info(arduino_info, platform_info):
    """."""
    tools_info = {'names': []}

    arduino_app_path = arduino_info['arduino_app_path']
    packages_path = os.path.join(arduino_app_path, 'packages')
    tools_deps = platform_info.get('toolsDependencies', [])
    for tool_info in tools_deps:
        package = tool_info.get('packager', '')
        name = tool_info.get('name', '')
        version = tool_info.get('version', '')
        path = ''

        if package and name and version:
            package_path = os.path.join(packages_path, package)
            if os.path.isdir(package_path):
                tools_path = os.path.join(package_path, 'tools')
                tool_path = os.path.join(tools_path, name)
                if os.path.isdir(tool_path):
                    path = os.path.join(tool_path, version)
                    if not os.path.isdir(path):
                        path = ''
        tool_info['path'] = path
        tools_info['names'].append(name)
        tools_info[name] = tool_info
    return tools_info


def get_sel_platform_path(arduino_info):
    """."""
    platform_path = ''
    sel_pkg = arduino_info['selected'].get('package')
    sel_ptfm = arduino_info['selected'].get('platform')
    sel_ver = arduino_info['selected'].get('version')
    if sel_pkg and sel_ver:
        arch = get_platform_arch_by_name(arduino_info, sel_pkg, sel_ptfm)
        arduino_app_path = arduino_info['arduino_app_path']
        packages_path = os.path.join(arduino_app_path, 'packages')
        package_path = os.path.join(packages_path, sel_pkg)
        hardware_path = os.path.join(package_path, 'hardware')
        platforms_path = os.path.join(hardware_path, arch)
        platform_path = os.path.join(platforms_path, sel_ver)
    return platform_path


def get_sel_core_src_path(arduino_info):
    """."""
    core_src_path = ''
    platform_path = get_sel_platform_path(arduino_info)
    if platform_path:
        board_info = get_sel_board_info(arduino_info)
        build_core = board_info.get('build.core', '')
        if ':' in build_core:
            build_core = build_core.split(':')[-1].strip()
        if build_core:
            cores_path = os.path.join(platform_path, 'cores')
            core_src_path = os.path.join(cores_path, build_core)
    return core_src_path


def get_sel_variant_path(arduino_info):
    """."""
    variant_path = ''
    platform_path = get_sel_platform_path(arduino_info)
    if platform_path:
        board_info = get_sel_board_info(arduino_info)
        build_variant = board_info.get('build.variant', '')
        variants_path = os.path.join(platform_path, 'variants')
        variant_path = os.path.join(variants_path, build_variant)
    return variant_path


def get_variants(text):
    """."""
    pattern_text = r'\{\S+?}'
    pattern = re.compile(pattern_text)
    variants = pattern.findall(text)
    return variants


def replace_variants(text, info, prefix=''):
    """."""
    variants = get_variants(text)
    for variant in variants:
        go_replace = False
        key = variant[1:-1]

        if key in info:
            value = info[key]
            go_replace = True
        if prefix:
            prefix_key = prefix + key
            if prefix_key in info:
                value = info[prefix_key]
                go_replace = True

        if go_replace:
            value = replace_variants(value, info, prefix)
            text = text.replace(variant, value)
    return text


def get_commands_info(arduino_info, project=None):
    """."""
    cmds_info = {}
    all_cmds_info = {}
    platform_path = get_sel_platform_path(arduino_info)
    if platform_path:
        cmd_file_path = os.path.join(platform_path, 'platform.txt')
        cmd_file = plain_params_file.PlainParamsFile(cmd_file_path)
        all_cmds_info = cmd_file.get_info()

    platform_info = get_sel_platform_info(arduino_info)
    board_info = get_sel_board_info(arduino_info)
    programmer_info = get_sel_programmer_info(arduino_info)

    prj_name = ''
    if project:
        prj_name = project.get_name()
    arduino_app_path = arduino_info['arduino_app_path']
    build_path = os.path.join(arduino_app_path, 'build')
    platform_system_path = os.path.join(platform_path, 'system')
    platform_variant_path = get_sel_variant_path(arduino_info)

    prj_build_path = os.path.join(build_path, prj_name)
    ser_port = arduino_info['selected'].get('serial_port', '')
    verbose_upload = bool(arduino_info['settings'].get('verbose_upload'))
    verify_code = bool(arduino_info['settings'].get('verify_code'))

    sel_pkg = arduino_info['selected'].get('package')
    sel_ptfm = arduino_info['selected'].get('platform')
    include_paths = arduino_info.get('include_paths', [])
    includes = ['"-I%s"' % p.replace('\\', '/') for p in include_paths]

    all_info = {}
    all_info['build.project_name'] = prj_name
    all_info['build.path'] = prj_build_path.replace('\\', '/')
    all_info['runtime.platform.path'] = platform_path.replace('\\', '/')
    all_info['build.system.path'] = platform_system_path.replace('\\', '/')
    all_info['build.variant.path'] = platform_variant_path.replace('\\', '/')
    all_info['build.arch'] = get_platform_arch_by_name(arduino_info,
                                                       sel_pkg, sel_ptfm)
    ser_port = str(ser_port)
    all_info['serial.port'] = ser_port
    serial_file = serial_port.get_serial_file(ser_port)

    all_info['serial.port.file'] = serial_file
    all_info['runtime.ide.version'] = '20000'
    all_info['archive_file'] = 'core.a'
    all_info['includes'] = ' '.join(includes)

    include_paths = arduino_info.get('include_paths', [])

    all_info.update(all_cmds_info)
    all_info.update(programmer_info)
    all_info.update(board_info)

    extra_build_flag = arduino_info['settings'].get('extra_build_flag', '')
    extra_flags = all_info.get('build.extra_flags', '')
    all_info['build.extra_flags'] = ' '.join((extra_flags, extra_build_flag))

    tools_info = get_sel_tools_info(arduino_info, platform_info)
    tool_names = tools_info.get('names', [])
    for tool_name in tool_names:
        tool_info = tools_info.get(tool_name, {})
        tool_path = tool_info.get('path', '')
        all_info['runtime.tools.%s.path' % tool_name] = \
            tool_path.replace('\\', '/')

        tool_id = 'tools.%s.' % tool_name
        if verbose_upload:
            all_info['%supload.verbose' % tool_id] = \
                all_info.get('%supload.params.verbose', '')
            all_info['%sprogram.verbose' % tool_id] = \
                all_info.get('%sprogram.params.verbose', '')
            all_info['%sbootloader.verbose' % tool_id] = \
                all_info.get('%sbootloader.params.verbose', '')
            all_info['%serase.verbose' % tool_id] = \
                all_info.get('%serase.params.verbose', '')
        else:
            all_info['%supload.verbose' % tool_id] = \
                all_info.get('%supload.params.quiet', '')
            all_info['%sprogram.verbose' % tool_id] = \
                all_info.get('%sprogram.params.quiet', '')
            all_info['%sbootloader.verbose' % tool_id] = \
                all_info.get('%sbootloader.params.quiet', '')
            all_info['%serase.verbose' % tool_id] = \
                all_info.get('%serase.params.quiet', '')

        if ('%supload.verify' % tool_id) not in all_info:
            all_info['%supload.verify' % tool_id] = ''
        if not verify_code:
            all_info['%supload.verify' % tool_id] = \
                all_info.get('%supload.params.noverify', '')
            all_info['%sprogram.verify' % tool_id] = \
                all_info.get('%sprogram.params.noverify', '')

    for key in all_cmds_info:
        if key.startswith('recipe.') or key.startswith('preproc.'):
            cmd = all_cmds_info[key]
            cmd = replace_variants(cmd, all_info)
            cmds_info[key] = cmd
        elif key.startswith('tools.'):
            for tool_name in tool_names:
                tool_id = 'tools.%s.' % tool_name
                tool_rem_id = 'tools.%s_remote.' % tool_name
                if key.startswith(tool_id) and key.endswith('pattern'):
                    cmd = all_cmds_info[key]
                    cmd = replace_variants(cmd, all_info, tool_id)
                    key = key.replace(tool_id, '')
                    cmds_info[key] = cmd
                elif key.startswith(tool_rem_id) and key.endswith('pattern'):
                    cmd = all_cmds_info[key]
                    cmd = replace_variants(cmd, all_info, tool_id)
                    key = key.replace(tool_rem_id, '')
                    key = 'remote.' + key
                    cmds_info[key] = cmd
    return cmds_info
