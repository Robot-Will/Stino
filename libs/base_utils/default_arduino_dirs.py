#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
from . import sys_info
from . import sys_dirs


def arduino_app_path():
    """Function Docs."""
    app_path = os.path.join(sys_dirs.get_user_config_path(), 'Arduino15')
    if sys_info.get_os_name() == 'linux':
        home = os.getenv('HOME')
        app_path = os.path.join(home, '.arduino15')
    return app_path


def arduino_sketchbook_path():
    """Function Docs."""
    doc_path = sys_dirs.get_document_path()
    sketchbook_path = os.path.join(doc_path, 'Arduino')
    return sketchbook_path
