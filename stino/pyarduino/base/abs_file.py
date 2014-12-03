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

import os
import glob
import codecs


class AbstractFile(object):
    def __init__(self, path):
        path = os.path.abspath(path)
        self.set_path(path)

    def set_path(self, path):
        self.path = path
        self.dir = os.path.dirname(self.path)
        self.name = os.path.basename(self.path)
        self.caption = self.name

    def __str__(self):
        return '%s (%s)' % (self.name, self.path)

    def get_path(self):
        return self.path

    def get_dir(self):
        return self.dir

    def get_name(self):
        return self.name

    def get_ctime(self):
        ctime = 0
        if os.path.exists(self.path):
            ctime = os.path.getctime(self.path)
        return ctime

    def get_mtime(self):
        mtime = 0
        if os.path.exists(self.path):
            mtime = os.path.getmtime(self.path)
        return mtime

    def is_file(self):
        return os.path.isfile(self.path)

    def is_dir(self):
        return os.path.isdir(self.path)

    def is_temp_file(self):
        state = False
        lower_name = self.name.lower()
        if lower_name == 'cvs':
            state = True
        elif lower_name.startswith('$') or lower_name.startswith('.'):
            state = True
        elif lower_name.endswith('.tmp') or lower_name.endswith('.bak'):
            state = True
        return state

    def change_name(self, new_name):
        os.chdir(self.dir)
        os.rename(self.name, new_name)
        new_path = os.path.join(self.dir, new_name)
        self.set_path(new_path)


class Dir(AbstractFile):
    def __init__(self, path):
        super(Dir, self).__init__(path)

    def ensure_existence(self):
        if self.is_file():
            cur_file = File(self.path)
            new_name = 'old_file_' + cur_file.name
            cur_file.change_name(new_name)
        if not self.is_dir():
            os.makedirs(self.path)

    def list_all(self, pattern='*'):
        all_files = []
        paths = glob.glob(os.path.join(self.path, pattern))
        all_files = (AbstractFile(path) for path in paths)
        all_files = [f for f in all_files if not f.is_temp_file()]
        all_files.sort(key=lambda f: f.get_name().lower())
        return all_files

    def list_dirs(self, pattern='*'):
        all_files = self.list_all(pattern)
        dirs = [Dir(f.path) for f in all_files if f.is_dir()]
        return dirs

    def list_files(self, pattern='*'):
        all_files = self.list_all(pattern)
        files = [File(f.path) for f in all_files if f.is_file()]
        return files

    def list_files_of_extension(self, ext=''):
        return self.list_files('*' + ext)

    def list_files_of_extensions(self, exts=['']):
        all_files = []
        for ext in exts:
            all_files += self.list_files_of_extension(ext)
        return all_files

    def recursive_list_files(self, exts=[''], exclude_dirs=[]):
        all_files = self.list_files_of_extensions(exts)
        dirs = self.list_dirs()
        for cur_dir in dirs:
            if cur_dir.get_name() not in exclude_dirs:
                all_files += cur_dir.recursive_list_files(exts)
        return all_files

    def has_file(self, file_name):
        file_path = os.path.join(self.path, file_name)
        return os.path.isfile(file_path)


class File(AbstractFile):
    """
    Doc of this class
    """
    def __init__(self, path, encoding='utf-8'):
        super(File, self).__init__(path)
        self.set_encoding(encoding)

    def has_ext(self, extension):
        return self.get_ext() == extension

    def get_ext(self):
        return os.path.splitext(self.name)[1]

    def get_basename(self):
        return os.path.splitext(self.name)[0]

    def get_encoding(self):
        return self.encoding

    def set_encoding(self, encoding='utf-8'):
        self.encoding = encoding

    def read(self):
        text = ''
        try:
            with codecs.open(self.path, 'r', self.encoding) as f:
                text = f.read()
        except (IOError, UnicodeError):
            pass
        return text

    def write(self, text, append=False):
        mode = 'w'
        if append:
            mode = 'a'
        try:
            with codecs.open(self.path, mode, self.encoding) as f:
                f.write(text)
        except (IOError, UnicodeError):
            pass
