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

from . import zeroconf
zeroconf.Zeroconf()


def list_wifi_ports():
    wifi_ports = []
    wifi_ports.sort()
    return wifi_ports
