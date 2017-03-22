#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time
import threading


class TaskListener(object):
    """."""

    def __init__(self, task, response=None, delay=0.01):
        """."""
        self._is_alive = False
        self._task = task
        self._response = response
        self._delay = delay

    def start(self):
        """."""
        if not self._is_alive:
            self._is_alive = True
            thread = threading.Thread(target=self._loop)
            thread.start()

    def _loop(self):
        """."""
        while True:
            self._run()
            time.sleep(self._delay)

    def _run(self):
        """."""
        if callable(self._task):
            state = self._task()
            if state is True and callable(self._response):
                self._response()

    def stop(self):
        """."""
        self._is_alive = False
