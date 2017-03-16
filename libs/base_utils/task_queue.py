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


class ActionQueue(object):
    """."""

    def __init__(self, delay=0):
        """."""
        self._queue = []
        self._is_alive = False
        self._delay = delay

    def put(self, action, *args, **kwargs):
        """."""
        if callable(action):
            self._queue.append((action, args, kwargs))
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
            params = self._queue.pop(0)
            action = params[0]
            args = params[1]
            kwargs = params[2]
            if args and kwargs:
                action(*args, **kwargs)
            elif args:
                action(*args)
            elif kwargs:
                action(**kwargs)
            else:
                action()
            time.sleep(self._delay)
        self._is_alive = False


class TaskQueue(object):
    """."""

    def __init__(self, consumer=sys.stdout.write, delay=0):
        """."""
        self._queue = []
        self._is_alive = False
        self._consumer = consumer
        self._delay = delay
        self._callable = callable(self._consumer)

    def put(self, *args):
        """."""
        if self._callable:
            self._queue.append(args)
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
            args = self._queue.pop(0)
            self._consumer(*args)
            time.sleep(self._delay)
        self._is_alive = False
