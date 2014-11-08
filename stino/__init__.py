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

from . import st_base
from . import main
from . import st_console


main.set_pyarduino()
i18n = st_base.get_i18n()
settings = st_base.get_settings()
main.create_menus()
main.create_completions()
main.create_syntax_file()
serial_listener = main.get_serial_listener()
serial_listener.start()
