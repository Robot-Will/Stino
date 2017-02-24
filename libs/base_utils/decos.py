#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals


def singleton(cls):
    """From PEP-318 http://www.python.org/dev/peps/pep-0318/#examples."""
    _instances = {}

    def get_instance(*args, **kwargs):
        if cls not in _instances:
            _instances[cls] = cls(*args, **kwargs)
        return _instances[cls]
    return get_instance
