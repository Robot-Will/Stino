#!/usr/bin/env python
#-*- coding: utf-8 -*-

#
# Documents
#

"""
Documents
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import glob

from . import deco
from . import sys_info
from . import language_file
from . import settings


@deco.singleton
class I18N(object):
    def __init__(self):
        self.load()

    def load(self):
        self.lang_params = {}
        self.lang_ids = []
        self.id_path_dict = {}
        self.trans_dict = {}
        self.list_ids()
        self.settings = settings.get_arduino_settings()
        self.lang_id = self.settings.get(
            'lang_id', sys_info.get_sys_language())
        self.change_lang(self.lang_id)

    def list_ids(self):
        self.lang_params = settings.get_user_settings(
            'language.stino-settings')
        preset_paths = [settings.get_preset_path(),
                        settings.get_user_preset_path()]
        for preset_path in preset_paths:
            lang_file_paths = glob.glob(preset_path + '/lang_*.txt')
            lang_file_names = [os.path.basename(p) for p in lang_file_paths]
            self.lang_ids += [name[5:-4] for name in lang_file_names]
            self.id_path_dict.update(dict(zip(self.lang_ids, lang_file_paths)))
        self.lang_ids.sort(key=lambda _id: self.lang_params.get(_id)[1])

    def change_lang(self, lang_id):
        if lang_id in self.id_path_dict:
            self.lang_id = lang_id
            lang_file_path = self.id_path_dict[lang_id]
            lang_file = language_file.LanguageFile(lang_file_path)
            self.trans_dict = lang_file.get_trans_dict()
        else:
            self.lang_id = 'en'
            self.trans_dict = {}
        self.settings.set('lang_id', self.lang_id)

    def translate(self, text, *params):
        trans_text = self.trans_dict.get(text, text)
        for seq, param in enumerate(params):
            seq_text = '{%d}' % seq
            trans_text = trans_text.replace(seq_text, str(param))
        return trans_text

    def get_lang_id(self):
        return self.lang_id

    def get_lang_ids(self):
        return self.lang_ids

    def get_lang_names(self, lang_id):
        return self.lang_params.get(lang_id, ['Unknown', 'Unknown'])
