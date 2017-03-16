#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
import time

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


def get_full_platform_info(arduino_info, pkg, ptfm, ver):
    """."""
    pkgs_info = arduino_info.get('packages', {})
    inst_pkgs_info = arduino_info.get('installed_packages', {})
    inst_ptfm_info = get_platform_info(inst_pkgs_info, pkg, ptfm, ver)

    cur_pkg = inst_ptfm_info.get('package', '')
    cur_arch = inst_ptfm_info.get('architecture', '')
    cur_ver = inst_ptfm_info.get('version', '')
    cur_path = inst_ptfm_info.get('path', '')

    cur_ptfm = get_platform_name_by_arch(arduino_info, cur_pkg,
                                         cur_arch)
    if not cur_ver and cur_ptfm:
        vers = get_platform_versions(pkgs_info, cur_pkg, cur_ptfm)
        cur_ver = vers[-1]

    ptfm_info = get_platform_info(pkgs_info, cur_pkg, cur_ptfm, cur_ver)

    if not ptfm_info:
        ptfm_info = inst_ptfm_info
    else:
        ptfm_info['package'] = cur_pkg
        ptfm_info['path'] = cur_path
    return ptfm_info


def get_sel_platform_info(arduino_info):
    """."""
    sel_pkg = arduino_info['selected'].get('package')
    sel_ptfm = arduino_info['selected'].get('platform')
    sel_ver = arduino_info['selected'].get('version')
    ptfm_info = get_full_platform_info(arduino_info, sel_pkg,
                                       sel_ptfm, sel_ver)
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


def get_sel_platform_path(arduino_info):
    """."""
    ptfm_info = get_sel_platform_info(arduino_info)
    platform_path = ptfm_info.get('path', '')
    return platform_path


def get_alternate_platform_info(arduino_info, pkg, arch):
    """."""
    ptfm_info = {}
    ptfm = get_platform_name_by_arch(arduino_info, pkg, arch)
    if ptfm:
        pkgs_info = arduino_info.get('packages', {})
        vers = get_platform_versions(pkgs_info, pkg, ptfm)
        ver = vers[-1]
        ptfm_info = get_full_platform_info(arduino_info, pkg, ptfm, ver)
    return ptfm_info


def get_build_platform_info(arduino_info):
    """."""
    ptfm_info = get_sel_platform_info(arduino_info)

    board_info = get_sel_board_info(arduino_info)
    build_core = board_info.get('build.core', '')
    if ':' in build_core:
        core_infos = build_core.split(':')
        pkg = core_infos[0].strip()
        arch = ptfm_info.get('architecture', '')
        ptfm_info = get_alternate_platform_info(arduino_info, pkg, arch)
    return ptfm_info


def get_build_platform_path(arduino_info):
    """."""
    ptfm_info = get_build_platform_info(arduino_info)
    platform_path = ptfm_info.get('path', '')
    return platform_path


def get_build_core_src_path(arduino_info):
    """."""
    core_src_path = ''
    platform_path = get_build_platform_path(arduino_info)
    if platform_path:
        board_info = get_sel_board_info(arduino_info)
        build_core = board_info.get('build.core', '')
        if ':' in build_core:
            build_core = build_core.split(':')[-1].strip()
        if build_core:
            cores_path = os.path.join(platform_path, 'cores')
            core_src_path = os.path.join(cores_path, build_core)
    return core_src_path


def get_build_variant_path(arduino_info):
    """."""
    variant_path = ''
    ptfm_info = get_sel_platform_info(arduino_info)
    board_info = get_sel_board_info(arduino_info)
    build_variant = board_info.get('build.variant', '')
    if ':' in build_variant:
        pkg, build_variant = build_variant.split(':')
        pkg = pkg.strip()
        build_variant = build_variant.strip()
        arch = ptfm_info.get('architecture', '')
        ptfm_info = get_alternate_platform_info(arduino_info, pkg, arch)

    platform_path = ptfm_info.get('path', '')
    if platform_path:
        variants_path = os.path.join(platform_path, 'variants')
        variant_path = os.path.join(variants_path, build_variant)
    return variant_path


def get_default_tools_deps(arduino_info):
    """."""
    pkgs_info = arduino_info.get('packages', {})
    pkg_name = 'arduino'
    ptfm_name = 'Arduino AVR Boards'
    ptfm_ver = get_platform_versions(pkgs_info, pkg_name, ptfm_name)[-1]
    ptfm_info = get_platform_info(pkgs_info, pkg_name,
                                  ptfm_name, ptfm_ver)
    tools_deps = ptfm_info.get('toolsDependencies', [])
    return tools_deps


def get_build_tools_info(arduino_info, platform_info):
    """."""
    tools_info = {'names': []}
    arduino_app_path = arduino_info['arduino_app_path']
    packages_path = os.path.join(arduino_app_path, 'packages')
    tools_deps = platform_info.get('toolsDependencies', [])
    ptfm_name = platform_info.get('name', '')

    if ptfm_name and not tools_deps:
        tools_deps = get_default_tools_deps(arduino_info)

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


def get_build_cmds_info(arduino_info):
    """."""
    cmds_info = {}
    platform_path = get_build_platform_path(arduino_info)
    if platform_path:
        cmd_file_path = os.path.join(platform_path, 'platform.txt')
        cmd_file = plain_params_file.PlainParamsFile(cmd_file_path)
        cmds_info = cmd_file.get_info()
    return cmds_info


def get_commands_info(arduino_info, project=None):
    """."""
    cmds_info = {}
    build_platform_path = get_build_platform_path(arduino_info)

    all_cmds_info = get_build_cmds_info(arduino_info)
    board_info = get_sel_board_info(arduino_info)
    programmer_info = get_sel_programmer_info(arduino_info)

    sel_pkg = arduino_info['selected'].get('package', '')
    sel_ptfm = arduino_info['selected'].get('platform', '')

    prj_name = ''
    if project:
        prj_name = project.get_name()
    arduino_app_path = arduino_info['arduino_app_path']
    build_path = os.path.join(arduino_app_path, 'build')
    platform_system_path = os.path.join(build_platform_path, 'system')
    platform_variant_path = get_build_variant_path(arduino_info)

    prj_build_path = os.path.join(build_path, prj_name)
    ser_port = arduino_info['selected'].get('serial_port', '')
    verbose_upload = bool(arduino_info['settings'].get('verbose_upload'))
    verify_code = bool(arduino_info['settings'].get('verify_code'))

    include_paths = arduino_info.get('include_paths', [])
    includes = ['"-I%s"' % p.replace('\\', '/') for p in include_paths]

    all_info = {}
    all_info['extra.time.utc'] = str(int(time.time()))
    all_info['extra.time.local'] = str(int(time.mktime(time.localtime())))
    all_info['extra.time.zone'] = str(int(time.timezone))
    all_info['extra.time.dst'] = str(int(time.daylight))
    all_info['build.project_name'] = prj_name
    all_info['build.path'] = prj_build_path.replace('\\', '/')
    all_info['runtime.platform.path'] = build_platform_path.replace('\\', '/')
    all_info['build.system.path'] = platform_system_path.replace('\\', '/')
    all_info['build.variant.path'] = platform_variant_path.replace('\\', '/')
    all_info['build.arch'] = get_platform_arch_by_name(arduino_info,
                                                       sel_pkg, sel_ptfm)

    ide_pkg_path = os.path.dirname(build_platform_path)
    core_path = get_build_core_src_path(arduino_info)
    all_info['runtime.hardware.path'] = ide_pkg_path.replace('\\', '/')
    all_info['build.core.path'] = core_path.replace('\\', '/')

    ser_port = str(ser_port)
    all_info['serial.port'] = ser_port
    serial_file = serial_port.get_serial_file(ser_port)

    all_info['serial.port.file'] = serial_file
    all_info['runtime.ide.version'] = '20000'

    archive_file_name = 'core.a'
    archive_file_path = os.path.join(prj_build_path, archive_file_name)
    all_info['archive_file'] = archive_file_name
    all_info['archive_file_path'] = archive_file_path
    all_info['includes'] = ' '.join(includes)

    all_info.update(all_cmds_info)
    all_info.update(programmer_info)
    all_info.update(board_info)

    extra_build_flag = arduino_info['settings'].get('extra_build_flag', '')
    extra_flags = all_info.get('build.extra_flags', '')
    all_info['build.extra_flags'] = ' '.join((extra_flags, extra_build_flag))

    if 'arm' in all_info.get('compiler.c.cmd', '') or \
            'arm' in all_info.get('build.command.gcc', ''):
        if 'compiler.c.elf.extra_flags' in all_info:
            all_info['compiler.c.elf.extra_flags'] += ' --specs=nosys.specs'
        elif 'build.flags.libs' in all_info:
            all_info['build.flags.libs'] += ' --specs=nosys.specs'

    build_platform_info = get_build_platform_info(arduino_info)
    tools_info = get_build_tools_info(arduino_info, build_platform_info)
    tool_names = tools_info.get('names', [])
    upload_tool = all_info.get('upload.tool', '')
    if upload_tool not in tool_names:
        tool_names.append(upload_tool)

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
        if key.startswith('recipe.'):
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
