#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import time
import sys
import threading


class TaskQueue(object):
    """."""

    def __init__(self, consumer=sys.stdout.write, delay=0.1):
        """."""
        self._queue = []
        self._is_alive = False
        self._consumer = consumer
        self._delay = delay
        self._callable = callable(self._consumer)

    def put(self, obj):
        """."""
        if self._callable:
            self._queue.append(obj)
            self._start()

    def _start(self):
        """."""
        if not self._is_alive:
            self._is_alive = True
            thread = threading.Thread(target=self._run)
            thread.start()

    def _run(self):
        """."""
        while self._queue:
            obj = self._queue.pop(0)
            self._task(obj)
            time.sleep(self._delay)
        self._is_alive = False

    def _task(self, obj):
        """."""
        self._consumer(obj)
