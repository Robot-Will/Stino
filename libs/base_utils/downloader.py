#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import sys
import http.client
import ssl
import socket
import urllib.error
import urllib.request
import operator

from . import task_queue


def get_remote_file_info(url):
    """."""
    info = {}
    if url.startswith('https'):
        opener = urllib.request.build_opener(HTTPSHandlerV3())
        urllib.request.install_opener(opener)
    try:
        response = urllib.request.urlopen(url)
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(url, e)
    else:
        info = dict(response.headers)
        response.close()
    return info


def get_remote_etag(url):
    """."""
    info = get_remote_file_info(url)
    if 'ETag' in info:
        etag = info.get('ETag')
    elif 'Last-Modified' in info:
        etag = info.get('Last-Modified')
    elif 'Content-Length' in info:
        etag = info.get('Content-Length')
    else:
        etag = ''

    if etag.endswith('"'):
        etag = etag[:-1]
    if '"'in etag:
        index = etag.index('"')
        etag = etag[index + 1:]
    return etag


def download(url, target_dir,
             message_consumer=sys.stdout.write, mode='resume'):
    """Download a file from an URL into a target directory."""
    is_msg_quiet = True
    file_name = os.path.basename(url)
    target_file_path = os.path.join(target_dir, file_name)
    try:
        import urllib.request
        response = urllib.request.urlopen(url)
        response_info = dict(response.headers)
        message_consumer(
            "Downloading %s Bytes into %s" % (
                response_info.get('Content-Length', '0'),
                target_file_path,
            ),
            is_msg_quiet
        )
        open(target_file_path, 'wb').write(response.read())
    except Exception as e:
        message_consumer(
            '[Error] Can not fetch %s: %s\n' % (
                url,
                str(e)
            ),
            is_msg_quiet
        )
        return False
    message_consumer(
        'Download finished!\n',
        is_msg_quiet
    )
    return True


class HTTPSConnectionV3(http.client.HTTPSConnection):
    """."""

    def __init__(self, *args, **kwargs):
        """."""
        super(HTTPSConnectionV3, self).__init__(*args, **kwargs)

    def connect(self):
        """."""
        sock = socket.create_connection((self.host, self.port), self.timeout)
        try:
            protocol = ssl.PROTOCOL_SSLv23
            self.sock = ssl.SSLContext(protocol).wrap_socket(sock)
        except ssl.SSLError:
            try:
                protocol = ssl.PROTOCOL_SSLv3
                self.sock = ssl.SSLContext(protocol).wrap_socket(sock)
            except ssl.SSLError:
                try:
                    protocol = ssl.PROTOCOL_TLSv1
                    self.sock = ssl.SSLContext(protocol).wrap_socket(sock)
                except ssl.SSLError:
                    try:
                        protocol = ssl.PROTOCOL_SSLv2
                        self.sock = ssl.SSLContext(protocol).wrap_socket(sock)
                    except ssl.SSLError:
                        self.sock = sock


class HTTPSHandlerV3(urllib.request.HTTPSHandler):
    """."""

    def https_open(self, req):
        """."""
        return self.do_open(HTTPSConnectionV3, req)


class DownloadQueue(task_queue.TaskQueue):
    """."""

    def put(self, down_info):
        """."""
        if self._callable:
            in_queue = False
            for info in self._queue:
                if operator.eq(info, down_info):
                    in_queue = True
                    break
            if not in_queue:
                self._queue.append(down_info)
                self._start()
