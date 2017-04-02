#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Package Docs."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import sys
import threading
import time


class ProgressBar:
    """."""

    def __init__(self):
        """."""
        self._is_alive = False

    def start(self, consumer=sys.stdout.write, caption=''):
        """."""
        self._caption = caption
        if callable(consumer):
            self._consumer = consumer
            if not self._is_alive:
                self._is_alive = True
                thread = threading.Thread(target=self._run)
                thread.start()

    def _run(self):
        """."""
        width = 16
        status = 1
        direction = 'right'
        while self._is_alive:
            before_blank = ' ' * (status - 1)
            after_blank = ' ' * (width - status)
            text = '%s [%s=%s]' % (self._caption, before_blank, after_blank)
            self._consumer(text)

            if direction == 'right':
                status += 1
            else:
                status -= 1

            if status == width:
                direction = 'left'
            if status == 1:
                direction = 'right'

            time.sleep(0.5)

    def stop(self):
        """."""
        self._is_alive = False
