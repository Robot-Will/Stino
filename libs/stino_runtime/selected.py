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
import glob

from base_utils import sys_info
from base_utils import serial_port
from base_utils import plain_params_file

in_braces_pattern_text = r'\{[^{}]*}'
in_braces_pattern = re.compile(in_braces_pattern_text)

runtime_tools_pattern_text = r'\{runtime.tools.(\S+?).path}'
runtime_tools_pattern = re.compile(runtime_tools_pattern_text)


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
    platform_arches = platforms_info.get('arches', [])
    return platform_arches


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
    ptfm_name = ptfm_arch
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

    if not ptfm_arch:
        pkgs_info = arduino_info.get('installed_packages', {})
        ptfm_names = get_platform_names(pkgs_info, pkg_name)
        if ptfm_name in ptfm_names:
            vers = get_platform_versions(pkgs_info, pkg_name, ptfm_name)
            if vers:
                ver = vers[-1]
                ptfm_info = get_platform_info(pkgs_info, pkg_name,
                                              ptfm_name, ver)
                ptfm_arch = ptfm_info.get('architecture', '').upper()
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
    if not cur_ver:
        vers = get_platform_versions(pkgs_info, cur_pkg, cur_ptfm)
        if vers:
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
    selected = arduino_info['selected']
    platform = selected.get('platform')
    sel_board = selected.get('board@%s' % platform)
    board_info = arduino_info['boards'].get(sel_board, {})

    sel_board_info = board_info.get('generic', {})
    options = board_info.get('options', [])
    for option in options:
        key = 'option_%s@%s' % (option, sel_board)
        sel_value_name = selected.get(key, '')
        values_info = board_info.get(option, {})
        value_info = values_info.get(sel_value_name, {})
        sel_board_info.update(value_info)
    return sel_board_info


def get_sel_board_options(arduino_info):
    """."""
    selected = arduino_info['selected']
    platform = selected.get('platform')
    sel_board = selected.get('board@%s' % platform)
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


def get_refering_platform_info(arduino_info, pkg, arch):
    """."""
    ptfm_info = {}
    ptfm = get_platform_name_by_arch(arduino_info, pkg, arch)
    if ptfm:
        pkgs_info = arduino_info.get('packages', {})
        vers = get_platform_versions(pkgs_info, pkg, ptfm)
        ver = vers[-1]
        ptfm_info = get_full_platform_info(arduino_info, pkg, ptfm, ver)
    return ptfm_info


def get_refering_platform_path(arduino_info, pkg, arch):
    """."""
    ptfm_info = get_refering_platform_info(arduino_info, pkg, arch)
    platform_path = ptfm_info.get('path', '')
    return platform_path


def get_platform_file_params_info(platform_path):
    """."""
    cmds_info = {}
    if platform_path:
        cmd_file_path = os.path.join(platform_path, 'platform.txt')
        cmd_file = plain_params_file.PlainParamsFile(cmd_file_path)
        cmds_info = cmd_file.get_info()

        os_name = sys_info.get_os_name()
        if os_name == 'osx':
            os_name = 'macosx'
        os_name = '.' + os_name
        keys = list(cmds_info.keys())
        for key in keys:
            if key.endswith(os_name):
                value = cmds_info[key]
                key = key.replace(os_name, '')
                cmds_info[key] = value
    return cmds_info


def get_refering_params_info(arduino_info, pkg, arch):
    """."""
    platform_path = get_refering_platform_path(arduino_info, pkg, arch)
    cmds_info = get_platform_file_params_info(platform_path)
    return cmds_info


####################
def find_variants_in_braces(text):
    """."""
    variants = in_braces_pattern.findall(text)
    return variants


def replace_variants_in_braces(text, info, prefix=''):
    """."""
    variants = find_variants_in_braces(text)
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
            value = replace_variants_in_braces(value, info, prefix)
            text = text.replace(variant, value)
    return text


# Build Paths#########
def get_target_platform_info(arduino_info, value):
    """."""
    ptfm_info = get_sel_platform_info(arduino_info)
    if ':' in value:
        core_infos = value.split(':')
        pkg = core_infos[0].strip()
        arch = ptfm_info.get('architecture', '')
        ptfm_info = get_refering_platform_info(arduino_info, pkg, arch)
    return ptfm_info


def get_build_platform_info(arduino_info):
    """."""
    board_info = get_sel_board_info(arduino_info)
    build_core = board_info.get('build.core', '')
    ptfm_info = get_target_platform_info(arduino_info, build_core)
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
        ptfm_info = get_refering_platform_info(arduino_info, pkg, arch)

    platform_path = ptfm_info.get('path', '')
    if platform_path:
        variants_path = os.path.join(platform_path, 'variants')
        variant_path = os.path.join(variants_path, build_variant)
    return variant_path


# Base Infos#########
def get_generic_info():
    """."""
    generic_info = {}
    # Ardunio IDE version > 10000
    generic_info['runtime.ide.version'] = '20000'

    # Time Info
    generic_info['extra.time.utc'] = str(int(time.time()))
    generic_info['extra.time.local'] = str(int(time.mktime(time.localtime())))
    generic_info['extra.time.zone'] = str(int(time.timezone))
    generic_info['extra.time.dst'] = str(int(time.daylight))
    return generic_info


def get_project_info(arduino_info, project=None):
    """."""
    project_info = {}
    # Project Info
    prj_name = ''
    if project:
        prj_name = project.get_name()
    arduino_app_path = arduino_info['arduino_app_path']
    build_path = os.path.join(arduino_app_path, 'build')
    prj_build_path = os.path.join(build_path, prj_name)
    project_info['build.project_name'] = prj_name
    project_info['build.path'] = prj_build_path.replace('\\', '/')

    # core.a Info
    archive_file_name = 'core/core.a'
    archive_file_path = os.path.join(prj_build_path, archive_file_name)
    project_info['archive_file'] = archive_file_name
    project_info['archive_file_path'] = archive_file_path
    return project_info


#################################################################
def get_tools_in_commands(cmds):
    """."""
    runtime_tools = []
    for cmd in cmds:
        tools = runtime_tools_pattern.findall(cmd)
        for tool in tools:
            if tool not in runtime_tools:
                runtime_tools.append(tool)
    return runtime_tools


def get_tool_info(arduino_info, tool_name):
    """."""
    tool_info = {}
    has_tool = False
    sel_pkg = arduino_info['selected'].get('package')
    inst_pkgs_info = arduino_info.get('installed_packages', {})
    inst_pkg_names = inst_pkgs_info.get('names', [])
    pkg_info = get_package_info(inst_pkgs_info, sel_pkg)
    pkg_path = pkg_info.get('path', '')
    tools_path = os.path.join(pkg_path, 'tools')
    tool_path = os.path.join(tools_path, tool_name)
    if os.path.isdir(tool_path):
        has_tool = True
    else:
        for pkg_name in inst_pkg_names:
            pkg_info = get_package_info(inst_pkgs_info, pkg_name)
            pkg_path = pkg_info.get('path', '')
            tools_path = os.path.join(pkg_path, 'tools')
            tool_path = os.path.join(tools_path, tool_name)
            if os.path.isdir(tool_path):
                has_tool = True
                break

    has_bin = False
    if has_tool:
        sub_paths = glob.glob(tool_path + '/*')[::-1]
        for sub_path in sub_paths:
            if os.path.isfile(sub_path):
                has_bin = True
                break

        if not has_bin:
            for sub_path in sub_paths:
                bin_path = os.path.join(sub_path, 'bin')
                if os.path.isdir(bin_path):
                    has_bin = True
                else:
                    s_sub_paths = glob.glob(sub_path + '/*')
                    for s_sub_path in s_sub_paths:
                        if os.path.isfile(s_sub_path):
                            has_bin = True
                            break
                if has_bin:
                    tool_path = sub_path
                    break
    if not has_bin:
        tool_path = ''
        avial_pkgs_info = arduino_info.get('packages', {})
        avail_pkg_names = avial_pkgs_info.get('names', [])
        for pkg_name in avail_pkg_names:
            pkg_info = get_package_info(avial_pkgs_info, pkg_name)
            tools_info = pkg_info.get('tools', {})
            tool_names = tools_info.get('names', [])
            if tool_name in tool_names:
                tool_info = tools_info.get(tool_name)
                break
    tool_info['name'] = tool_name
    tool_info['path'] = tool_path
    return tool_info


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


def get_dep_tools_info(arduino_info, platform_info):
    """."""
    board_info = get_sel_board_info(arduino_info)
    programmer_info = get_sel_programmer_info(arduino_info)
    upload_tool = board_info.get('upload.tool', '')
    program_tool = programmer_info.get('program.tool', '')
    bootloader_tool = board_info.get('bootloader.tool', '')
    build_ptfm_path = get_build_platform_path(arduino_info)

    tools = [upload_tool, program_tool, bootloader_tool]
    ptfm_paths = []
    for tool in tools:
        if tool:
            ptfm_info = get_target_platform_info(arduino_info, tool)
            ptfm_path = ptfm_info.get('path', '')
            ptfm_paths.append(ptfm_path)

    tools = ['compiler'] + tools
    ptfm_paths = [build_ptfm_path] + ptfm_paths

    cmds = []
    for ptfm_path, tool in zip(ptfm_paths, tools):
        if ':' in tool:
            tool = tool.split(':')[-1]
        path_word = '%s.path' % tool
        cmd_file_path = os.path.join(ptfm_path, 'platform.txt')
        cmd_file = plain_params_file.PlainParamsFile(cmd_file_path)
        cmds_info = cmd_file.get_info()

        for key in cmds_info:
            if path_word in key:
                cmds.append(cmds_info[key])
                break
    tool_names = get_tools_in_commands(cmds)

    #########################################
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

    for name in tool_names:
        if name not in tools_info['names']:
            tool_info = get_tool_info(arduino_info, name)
            tools_info['names'].append(name)
            tools_info[name] = tool_info
    return tools_info


def get_runtime_tools_path_info(arduino_info, platform_info):
    """."""
    path_info = {}
    tools_info = get_dep_tools_info(arduino_info, platform_info)
    tool_names = tools_info.get('names', [])

    for tool_name in tool_names:
        tool_info = tools_info.get(tool_name, {})
        tool_path = tool_info.get('path', '')
        path_info['runtime.tools.%s.path' % tool_name] = \
            tool_path.replace('\\', '/')
    return path_info


def get_runtime_path_info(arduino_info, platform_info):
    """."""
    path_info = {}
    platform_path = platform_info.get('path', '')
    path_info['runtime.platform.path'] = platform_path.replace('\\', '/')

    # Runtime Tools Path
    runtime_tools_path_info = \
        get_runtime_tools_path_info(arduino_info, platform_info)
    path_info.update(runtime_tools_path_info)
    return path_info


#####################################################################
def get_base_info(arduino_info, project=None):
    """."""
    base_info = {}
    generic_info = get_generic_info()
    base_info.update(generic_info)
    if project:
        project_info = get_project_info(arduino_info, project)
        base_info.update(project_info)

    # For Ardunio IDE / hardware path
    build_platform_path = get_build_platform_path(arduino_info)
    ide_pkg_path = os.path.dirname(build_platform_path)
    base_info['runtime.hardware.path'] = ide_pkg_path.replace('\\', '/')
    return base_info


def get_runtime_build_info(arduino_info):
    """."""
    build_info = {}

    # Arch Info
    sel_pkg = arduino_info['selected'].get('package', '')
    sel_ptfm = arduino_info['selected'].get('platform', '')
    build_info['build.arch'] = get_platform_arch_by_name(arduino_info,
                                                         sel_pkg, sel_ptfm)

    # Platform Info
    build_platform_path = get_build_platform_path(arduino_info)
    platform_system_path = os.path.join(build_platform_path, 'system')
    platform_variant_path = get_build_variant_path(arduino_info)

    build_info['build.system.path'] = platform_system_path.replace('\\', '/')
    build_info['build.variant.path'] = \
        platform_variant_path.replace('\\', '/')

    # Core Src Path Info
    core_path = get_build_core_src_path(arduino_info)
    build_info['build.core.path'] = core_path.replace('\\', '/')

    # User defined Extra Build Flags Info
    user_build_flags = arduino_info['settings'].get('extra_build_flag', '')
    extra_build_flags = build_info.get('build.extra_flags', '')
    build_info['build.extra_flags'] = ' '.join((extra_build_flags,
                                                user_build_flags))

    build_platform_info = get_build_platform_info(arduino_info)
    path_info = get_runtime_path_info(arduino_info, build_platform_info)
    build_info.update(path_info)
    return build_info


def get_build_params_info(arduino_info):
    """."""
    build_params_info = {}
    platform_path = get_build_platform_path(arduino_info)
    params_info = get_platform_file_params_info(platform_path)
    for key in params_info:
        if not key.startswith('tools'):
            build_params_info[key] = params_info[key]
    return build_params_info


def get_build_commands_info(arduino_info, project=None):
    """."""
    base_info = get_base_info(arduino_info, project)
    runtime_build_info = get_runtime_build_info(arduino_info)
    build_params_info = get_build_params_info(arduino_info)
    board_info = get_sel_board_info(arduino_info)

    all_info = {}
    all_info.update(base_info)
    all_info.update(runtime_build_info)
    all_info.update(build_params_info)
    all_info.update(board_info)

    if 'compiler.cpp.flags' not in all_info:
        all_info['compiler.cpp.flags'] = ''

    if 'recipe.ar.pattern' in build_params_info:
        value = build_params_info['recipe.ar.pattern']
        if 'core/{archive_file}' in value:
            value = value.replace('core/{archive_file}', '{archive_file}')
            build_params_info['recipe.ar.pattern'] = value

    if 'recipe.c.combine.pattern' in build_params_info:
        value = build_params_info['recipe.c.combine.pattern']
        if '{build.path}/syscalls_sam3.c.o' in value:
            value = value.replace('{build.path}/syscalls_sam3.c.o',
                                  '{build.path}/core/syscalls_sam3.c.o')
        if '{build.path}/startup_NRF51822.s.o' in value:
            value = value.replace('{build.path}/startup_NRF51822.s.o',
                                  '{build.path}/core/startup_NRF51822.s.o')
        if '{build.path}/system_nrf51.c.o' in value:
            text = '{build.path}/core/mbed/targets/cmsis/TARGET_NORDIC/'
            text += 'TARGET_MCU_NRF51822/system_nrf51.c.o'
            value = value.replace('{build.path}/system_nrf51.c.o', text)

    cmds_info = {}
    for key in build_params_info:
        if key.startswith('recipe.'):
            cmd = build_params_info[key]
            cmd = replace_variants_in_braces(cmd, all_info)
            cmds_info[key] = cmd
    return cmds_info


##################################################################
def get_tool_params_info(arduino_info, tool_platform_path, tool_name):
    """."""
    tool_params_info = {}
    params_info = get_platform_file_params_info(tool_platform_path)

    tool_key = 'tools.%s.' % tool_name
    for key in params_info:
        if key.startswith(tool_key):
            short_key = key.replace(tool_key, '')
            tool_params_info[short_key] = params_info[key]
    return tool_params_info


def get_upload_command(arduino_info, project=None,
                       bin_path='', mode='upload'):
    """."""
    all_info = {}

    base_info = get_base_info(arduino_info, project)
    all_info.update(base_info)

    if not project and os.path.isfile(bin_path):
        dir_path = os.path.dirname(bin_path)
        file_name = os.path.basename(bin_path)
        prj_name = os.path.splitext(file_name)[0]
        all_info['build.path'] = dir_path
        all_info['build.project_name'] = prj_name

    board_info = get_sel_board_info(arduino_info)
    programmer_info = get_sel_programmer_info(arduino_info)

    ser_port = arduino_info['selected'].get('serial_port', '')
    ser_port = str(ser_port)
    all_info['serial.port'] = ser_port
    serial_file = serial_port.get_serial_file(ser_port)
    all_info['serial.port.file'] = serial_file

    tool_name = 'None'
    if mode == 'upload':
        tool_name = board_info.get('upload.tool', '')
    elif mode == 'program':
        tool_name = programmer_info.get('program.tool', '')

    tool_ptfm_info = get_target_platform_info(arduino_info, tool_name)
    path_info = get_runtime_path_info(arduino_info, tool_ptfm_info)
    all_info.update(path_info)

    tool_ptfm_path = tool_ptfm_info.get('path', '')
    tool_params_info = get_tool_params_info(arduino_info,
                                            tool_ptfm_path, tool_name)
    all_info.update(tool_params_info)
    all_info.update(board_info)
    all_info.update(programmer_info)

    tool_key = 'upload.pattern'
    key = 'None.pattern'
    if mode == 'upload':
        is_network_upload = arduino_info['selected'].get('use_network_port',
                                                         False)
        if is_network_upload:
            key = 'upload.network_pattern'
    elif mode == 'program':
        key = 'program.pattern'

    if key in all_info:
        tool_key = key
    else:
        mode = 'upload'

    is_verbose_upload = bool(arduino_info['settings'].get('verbose_upload'))
    is_verify_code = bool(arduino_info['settings'].get('verify_code'))
    verbose_mode = 'verbose' if is_verbose_upload else 'quiet'
    verify_mode = '' if is_verify_code else '.noverify'

    param_verbose_key = '%s.params.%s' % (mode, verbose_mode)
    param_verbose_value = all_info.get(param_verbose_key, '')
    param_verify_key = '%s.params%s' % (mode, verify_mode)
    param_verify_value = all_info.get(param_verify_key, '')

    all_info['%s.verbose' % mode] = param_verbose_value
    all_info['%s.verify' % mode] = param_verify_value

    tool_cmd = all_info.get(tool_key, '')
    tool_cmd = replace_variants_in_braces(tool_cmd, all_info)
    return tool_cmd


def get_bootloader_commands(arduino_info):
    """."""
    all_info = {}
    base_info = get_base_info(arduino_info)
    board_info = get_sel_board_info(arduino_info)
    programmer_info = get_sel_programmer_info(arduino_info)
    tool_name = board_info.get('bootloader.tool', '')

    all_info.update(base_info)

    ser_port = arduino_info['selected'].get('serial_port', '')
    ser_port = str(ser_port)
    all_info['serial.port'] = ser_port
    serial_file = serial_port.get_serial_file(ser_port)
    all_info['serial.port.file'] = serial_file

    tool_ptfm_info = get_target_platform_info(arduino_info, tool_name)
    path_info = get_runtime_path_info(arduino_info, tool_ptfm_info)
    all_info.update(path_info)

    tool_ptfm_path = tool_ptfm_info.get('path', '')
    tool_params_info = get_tool_params_info(arduino_info,
                                            tool_ptfm_path, tool_name)
    all_info.update(tool_params_info)
    all_info.update(board_info)
    all_info.update(programmer_info)

    erase_cmd = all_info.get('erase.pattern', '')
    bootloader_cmd = all_info.get('bootloader.pattern', '')

    cmds = []
    is_verbose = bool(arduino_info['settings'].get('verbose_upload'))
    verbose_mode = 'verbose' if is_verbose else 'quiet'
    if erase_cmd and bootloader_cmd:
        modes = ['erase', 'bootloader']
        for mode in modes:
            param_verbose_key = '%s.params.%s' % (mode, verbose_mode)
            param_verbose_value = all_info.get(param_verbose_key, '')
            all_info['%s.verbose' % mode] = param_verbose_value

            cmd_key = '%s.pattern' % mode
            cmd = all_info.get(cmd_key, '')
            cmd = replace_variants_in_braces(cmd, all_info)
            cmds.append(cmd)
    return cmds


def get_board_from_hwid(arduino_info, vid, pid):
    """."""
    name = ''
    boards_info = arduino_info.get('boards', {})
    board_names = boards_info.get('names', [])
    has_board = False
    for board_name in board_names:
        board_info = boards_info.get(board_name)
        generic_info = board_info.get('generic', {})
        for key in generic_info:
            if key.startswith('vid'):
                value = generic_info.get(key)
                if value == vid:
                    suffix = ''
                    if '.' in key:
                        number = key.split('.')[-1]
                        suffix = '.' + number
                    pid_key = 'pid' + suffix
                    if pid_key in generic_info:
                        value = generic_info[pid_key]
                        if value == pid:
                            name = board_name
                            has_board = True
                            break
        if has_board:
            break
    return name
