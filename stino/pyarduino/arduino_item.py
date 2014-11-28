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

from . import arduino_params_file


class ItemsFile(arduino_params_file.ParamsFile):
    def __init__(self, parent_id, path):
        super(ItemsFile, self).__init__(path)
        self.item_set = ItemSet(parent_id, self.param_pairs)

    def get_item_set(self):
        return self.item_set


class ItemSet(object):
    def __init__(self, parent_id, param_pairs, top_level=True):
        self.id = parent_id
        self.caption = parent_id
        self.load_items(param_pairs)
        item_ids = [item.get_id() for item in self.items]
        self.id_item_dict = dict(zip(item_ids, self.items))

        self.menu_caption_dict = {}
        if top_level:
            self.load_menu_caption_dict()

    def get_id(self):
        return self.id

    def get_caption(self):
        return self.caption

    def get_items(self):
        return self.items

    def get_item(self, item_id):
        return self.id_item_dict.get(item_id, None)

    def set_caption(self, caption):
        self.caption = caption

    def is_empty(self):
        return not bool(self.items)

    def load_items(self, param_pairs):
        item_ids = []
        self.items = []

        for key, value in param_pairs:
            if not '.' in key:
                key = key + '.name'

            index = key.index('.')
            item_id = key[:index]
            item_param_id = key[index + 1:]
            if not item_id in item_ids:
                item_ids.append(item_id)
                item = Item(self.id, item_id, [])
                self.items.append(item)
            item_param_pair = (item_param_id, value)
            index = item_ids.index(item_id)
            self.items[index].add_param_pair(item_param_pair)

    def load_menu_caption_dict(self):
        menu_id = self.id + '.menu'
        if menu_id in self.id_item_dict:
            item = self.id_item_dict.get(menu_id)
            self.menu_caption_dict = item.get_params()
            self.items.remove(item)
            for item in self.items:
                item.load_options(self.menu_caption_dict)


class Item(object):
    def __init__(self, parent_id, item_id, param_pairs):
        self.id = item_id
        if parent_id:
            self.id = parent_id + '.' + item_id
        self.param_pairs = param_pairs
        self.options = []

    def __str__(self):
        return self.id

    def get_id(self):
        return self.id

    def get_caption(self):
        return self.get_params().get('name', 'Unknown')

    def get_params(self):
        return dict(self.param_pairs)

    def get_options(self):
        return self.options

    def add_param_pair(self, param_pair):
        self.param_pairs.append(param_pair)

    def has_options(self):
        return bool(self.options)

    def has_sub_menus(self):
        state = False
        for key, value in self.param_pairs:
            if key.startswith('menu.'):
                state = True
                break
        return state

    def load_options(self, menu_caption_dict):
        if not self.has_sub_menus():
            return
        menu_id = self.id + '.menu'
        menu_item = ItemSet(self.id, self.param_pairs, False).get_item(menu_id)
        option_set = ItemSet(self.id, menu_item.param_pairs, False)
        for option in option_set.get_items():
            sub_item_set = ItemSet(option.id, option.param_pairs, False)
            sub_menu_id = option.id.split('.')[-1]
            sub_menu_caption = menu_caption_dict.get(sub_menu_id, '')
            sub_item_set.set_caption(sub_menu_caption)
            if not sub_item_set.is_empty():
                self.options.append(sub_item_set)
        self.option_ids = [option.get_id() for option in self.options]
        self.id_option_dict = dict(zip(self.option_ids, self.options))
        self.param_pairs = [pair for pair in self.param_pairs
                            if not pair[0].startswith('menu.')]
