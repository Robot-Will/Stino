#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from . import file


def get_item_info(parent_item, items_id):
    """
    .

    {
        'packages' :
        {
            'names': [$names],
            $name:
            {
                'platforms':
                {
                    'names': [$names],
                    'arches': [$arches]
                    $name:
                    {

                    }
                }
                'tools':
                {
                    'names': [$names],
                    $name:
                    {

                    }
                }
            }
        }
    }
    """
    info = {'names': [],
            'arches': []}

    name_items_info = {}
    items = parent_item.get(items_id, [])
    for item in items:
        name = item.get('name', '')
        if name not in info['names']:
            info['names'].append(name)
            name_items_info[name] = [item]
        else:
            name_items_info[name].append(item)

        arch = item.get('architecture', '')
        if arch not in info['arches']:
            info['arches'].append(arch)

    for name in info['names']:
        info[name] = {}
        info[name]['versions'] = []
        items = name_items_info[name]
        for item in items:
            version = item.get('version', '')
            if version not in info[name]['versions']:
                info[name]['versions'].append(version)
            info[name][version] = item
    return info


class IndexFile(file.JSONFile):
    """Class Docs."""

    def __init__(self, path):
        """Method Docs."""
        super(IndexFile, self).__init__(path)
        self._is_readonly = True
        self._info = {'packages': {}}
        self._info['packages']['names'] = []

        package_infos = self._data.get('packages', [])
        for package_info in package_infos:
            package_name = package_info.get('name', '')
            platform_info = get_item_info(package_info, 'platforms')
            tool_info = get_item_info(package_info, 'tools')
            package_info['platforms'] = platform_info
            package_info['tools'] = tool_info
            self._info['packages']['names'].append(package_name)
            self._info['packages'][package_name] = package_info
        self._info['packages']['names'].sort(key=str.lower)

    def get_info(self):
        """."""
        return self._info


class IndexFiles():
    """Class Docs."""

    def __init__(self, paths):
        """Method Docs."""
        all_packages_info = {'names': []}
        for path in paths:
            index_file = IndexFile(path)
            index_file_info = index_file.get_info()

            packages_info = index_file_info.get('packages')
            names = packages_info.pop('names')
            all_packages_info['names'] += names
            all_packages_info.update(packages_info)
        all_packages_info['names'].sort(key=str.lower)
        self._info = {'packages': all_packages_info}

    def get_info(self):
        """."""
        return self._info
