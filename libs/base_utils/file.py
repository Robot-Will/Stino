#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import codecs
import json
import glob


class AbstractFile(object):
    """Class Docs."""

    def __init__(self, path):
        """Method Docs."""
        path = os.path.realpath(path)
        self.set_path(path)
        self._is_readonly = False

    def set_path(self, path):
        """Method Docs."""
        self._path = path
        self._dir = os.path.dirname(self._path)
        self._name = os.path.basename(self._path)

    def __str__(self):
        """Method Docs."""
        return '%s (%s)' % (self._name, self._path)

    def get_path(self):
        """Method Docs."""
        return self._path

    def get_dir(self):
        """Method Docs."""
        return self._dir

    def get_name(self):
        """Method Docs."""
        return self._name

    def get_ctime(self):
        """Method Docs."""
        ctime = 0
        if os.path.exists(self._path):
            ctime = os.path.getctime(self._path)
        return ctime

    def get_mtime(self):
        """Method Docs."""
        mtime = 0
        if os.path.exists(self._path):
            mtime = os.path.getmtime(self._path)
        return mtime

    def is_file(self):
        """Method Docs."""
        return os.path.isfile(self._path)

    def is_dir(self):
        """Method Docs."""
        return os.path.isdir(self._path)

    def is_temp_file(self):
        """Method Docs."""
        state = False
        lower_name = self._name.lower()
        if lower_name == 'cvs':
            state = True
        elif lower_name.startswith('$') or lower_name.startswith('.'):
            state = True
        elif lower_name.endswith('.tmp') or lower_name.endswith('.bak'):
            state = True
        return state

    def change_name(self, new_name):
        """Method Docs."""
        os.chdir(self._dir)
        os.rename(self._name, new_name)
        new_path = os.path.join(self._dir, new_name)
        self.set_path(new_path)

    def is_readonly(self):
        """Method Docs."""
        return self._is_readonly

    def set_readonly(self, state):
        """Method Docs."""
        if state:
            self._is_readonly = True
        else:
            self._is_readonly = False


class File(AbstractFile):
    """Class Docs."""

    def __init__(self, path, encoding='utf-8'):
        """Method Docs."""
        super(File, self).__init__(path)
        self.set_encoding(encoding)

    def has_ext(self, extension):
        """Method Docs."""
        return self.get_ext() == extension

    def get_ext(self):
        """Method Docs."""
        return os.path.splitext(self._name)[1]

    def get_basename(self):
        """Method Docs."""
        return os.path.splitext(self._name)[0]

    def get_encoding(self):
        """Method Docs."""
        return self._encoding

    def set_encoding(self, encoding='utf-8'):
        """Method Docs."""
        self._encoding = encoding

    def read(self):
        """Method Docs."""
        text = ''
        try:
            with codecs.open(self._path, 'r', self._encoding) as f:
                text = f.read()
        except (IOError, UnicodeError) as e:
            print(e)
        return text

    def write(self, text, append=False):
        """Method Docs."""
        if self._is_readonly:
            return

        mode = 'w'
        if append:
            mode = 'a'

        if not os.path.isdir(self._dir):
            os.makedirs(self._dir)
        try:
            with codecs.open(self._path, mode, self._encoding) as f:
                f.write(text)
        except (IOError, UnicodeError):
            pass


class JSONFile(File):
    """Class Docs."""

    def __init__(self, path):
        """Method Docs."""
        super(JSONFile, self).__init__(path)
        self._data = {}
        self.load()

    def set_data(self, data):
        """Method Docs."""
        self._data = data
        self.save()

    def get_data(self):
        """Method Docs."""
        return self._data

    def load(self):
        """Method Docs."""
        text = self.read()
        try:
            self._data = json.loads(text)
        except ValueError:
            pass
            # print('Error while loading Json file %s.' % self._path)

    def save(self):
        """Method Docs."""
        text = json.dumps(self._data, sort_keys=True, indent=4)
        self.write(text)


class SettingsFile(JSONFile):
    """Class Docs."""

    def __init__(self, path):
        """Method Docs."""
        super(SettingsFile, self).__init__(path)

    def get(self, key, default_value=None):
        """Method Docs."""
        value = self._data.get(key, default_value)
        return value

    def set(self, key, value):
        """Method Docs."""
        self._data[key] = value
        self.save()

    def get_keys(self):
        """."""
        return self._data.keys()


class Dir(AbstractFile):
    """Class Docs."""

    def __init__(self, path):
        """Method Docs."""
        super(Dir, self).__init__(path)

    def create(self):
        """Method Docs."""
        if self.is_file():
            cur_file = File(self._path)
            new_name = 'old_file_' + cur_file.name
            cur_file.change_name(new_name)
        if not self.is_dir():
            os.makedirs(self._path)

    def list_all(self, pattern='*'):
        """Method Docs."""
        all_files = []
        paths = glob.glob(os.path.join(self._path, pattern))
        all_files = (AbstractFile(path) for path in paths)
        all_files = [f for f in all_files if not f.is_temp_file()]
        all_files.sort(key=lambda f: f.get_name().lower())
        return all_files

    def list_dirs(self, pattern='*'):
        """Method Docs."""
        all_files = self.list_all(pattern)
        dirs = [Dir(f._path) for f in all_files if f.is_dir()]
        return dirs

    def list_files(self, pattern='*'):
        """Method Docs."""
        all_files = self.list_all(pattern)
        files = [File(f._path) for f in all_files if f.is_file()]
        return files

    def list_files_of_extension(self, ext=''):
        """Method Docs."""
        return self.list_files('*' + ext)

    def list_files_of_extensions(self, exts=['']):
        """Method Docs."""
        all_files = []
        for ext in exts:
            all_files += self.list_files_of_extension(ext)
        return all_files

    def recursive_list_files(self, exts=[''], exclude_dirs=[]):
        """Method Docs."""
        all_files = self.list_files_of_extensions(exts)
        dirs = self.list_dirs()
        for cur_dir in dirs:
            if cur_dir.get_name() not in exclude_dirs:
                all_files += cur_dir.recursive_list_files(exts)
        return all_files

    def has_file(self, file_name):
        """Method Docs."""
        file_path = os.path.join(self._path, file_name)
        return os.path.isfile(file_path)


def check_dir(dir_path):
    """."""
    if not os.path.isdir(dir_path):
        os.makedirs(dir_path)
