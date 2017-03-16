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
    """."""
    is_done = False
    trunk_size = 1024
    done_size = 0
    is_msg_quiet = True

    file_name = os.path.basename(url)
    target_file_path = os.path.join(target_dir, file_name)
    tmp_file_path = target_file_path + '.stino-down'

    remote_info = get_remote_file_info(url)
    remote_size = int(remote_info.get('Content-Length', '0'))

    if remote_size > 0:
        if mode == 'resume':
            if os.path.isfile(target_file_path):
                if os.path.getsize(target_file_path) == remote_size:
                    is_done = True

        if not is_done:
            if url.startswith('https'):
                opener = urllib.request.build_opener(HTTPSHandlerV3())
                urllib.request.install_opener(opener)
            req = urllib.request.Request(url)
            if os.path.isfile(tmp_file_path):
                if mode == 'resume':
                    done_size = os.path.getsize(tmp_file_path)
                    req.add_header('Range', 'bytes=%d-' % done_size)
                else:
                    os.remove(tmp_file_path)

            try:
                remote_f = urllib.request.urlopen(req)
            except (ValueError, urllib.error.HTTPError, urllib.error.URLError):
                message_consumer('[Error] Can not fetch %s\n' % url,
                                 is_msg_quiet)
            else:
                message_consumer('[%s] Download started.\n' % url,
                                 is_msg_quiet)
                block = b''
                retry_counter = 0

                if not os.path.isdir(target_dir):
                    os.makedirs(target_dir)
                f = open(tmp_file_path, 'ab')
                while True:
                    try:
                        trunk = remote_f.read(trunk_size)
                    except (urllib.error.HTTPError, urllib.error.URLError):
                        retry_counter += 1
                        if retry_counter < 20:
                            continue
                        else:
                            break
                    else:
                        if not trunk:
                            is_done = True
                            break

                        block += trunk
                        if len(block) > remote_size / 10:
                            done_size += len(block)
                            f.write(block)
                            block = b''

                            percent = done_size / remote_size * 100
                            text = '[%s] %.0f%%' % (url, percent)
                            text += ' ('
                            text += '%.2f' % (done_size / 1024 / 1024)
                            text += ' M / '
                            text += '%.2f' % (remote_size / 1024 / 1024)
                            text += ' M)\n'
                            message_consumer(text, is_msg_quiet)

                if done_size < remote_size:
                    f.write(block)

                remote_f.close()
                f.close()

                if is_done:
                    if os.path.isfile(target_file_path):
                        os.remove(target_file_path)
                    os.rename(tmp_file_path, target_file_path)
                    message_consumer('[%s] Download completed.\n' % url,
                                     is_msg_quiet)
                else:
                    message_consumer('[%s] Download failed.\n' % url,
                                     is_msg_quiet)
    return is_done


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
