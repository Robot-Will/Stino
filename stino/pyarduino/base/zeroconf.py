from __future__ import absolute_import, division, print_function, unicode_literals

""" Multicast DNS Service Discovery for Python, v0.14-wmcbrine
    Copyright 2003 Paul Scott-Murphy, 2014 William McBrine

    This module provides a framework for the use of DNS Service Discovery
    using IP multicast.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301
    USA
"""

__author__ = 'Paul Scott-Murphy, William McBrine'
__maintainer__ = 'Jakub Stasiak <jakub@stasiak.at>'
__version__ = '0.15.1'
__license__ = 'LGPL'

import time
import struct
import socket
import threading
import select
import traceback
from functools import reduce

__all__ = ["Zeroconf", "ServiceInfo", "ServiceBrowser"]

try:
    xrange = xrange
except NameError:
    xrange = range

try:
    unicode
except NameError:
    unicode = str

if isinstance(chr(8), unicode):
    byte_chr = lambda num: bytes([num])
else:
    byte_chr = chr

if isinstance(bytes([8])[0], int):
    byte_ord = lambda x: x
else:
    byte_ord = ord

try:
    raw_input = raw_input
except NameError:
    raw_input = input

# hook for threads

_GLOBAL_DONE = False

# Some timing constants

_UNREGISTER_TIME = 125
_CHECK_TIME = 175
_REGISTER_TIME = 225
_LISTENER_TIME = 200
_BROWSER_TIME = 500

# Some DNS constants

_MDNS_ADDR = '224.0.0.251'
_MDNS_PORT = 5353
_DNS_PORT = 53
_DNS_TTL = 60 * 60  # one hour default TTL

_MAX_MSG_TYPICAL = 1460  # unused
_MAX_MSG_ABSOLUTE = 8972

_FLAGS_QR_MASK = 0x8000  # query response mask
_FLAGS_QR_QUERY = 0x0000  # query
_FLAGS_QR_RESPONSE = 0x8000  # response

_FLAGS_AA = 0x0400  # Authorative answer
_FLAGS_TC = 0x0200  # Truncated
_FLAGS_RD = 0x0100  # Recursion desired
_FLAGS_RA = 0x8000  # Recursion available

_FLAGS_Z = 0x0040  # Zero
_FLAGS_AD = 0x0020  # Authentic data
_FLAGS_CD = 0x0010  # Checking disabled

_CLASS_IN = 1
_CLASS_CS = 2
_CLASS_CH = 3
_CLASS_HS = 4
_CLASS_NONE = 254
_CLASS_ANY = 255
_CLASS_MASK = 0x7FFF
_CLASS_UNIQUE = 0x8000

_TYPE_A = 1
_TYPE_NS = 2
_TYPE_MD = 3
_TYPE_MF = 4
_TYPE_CNAME = 5
_TYPE_SOA = 6
_TYPE_MB = 7
_TYPE_MG = 8
_TYPE_MR = 9
_TYPE_NULL = 10
_TYPE_WKS = 11
_TYPE_PTR = 12
_TYPE_HINFO = 13
_TYPE_MINFO = 14
_TYPE_MX = 15
_TYPE_TXT = 16
_TYPE_AAAA = 28
_TYPE_SRV = 33
_TYPE_ANY = 255

# Mapping constants to names

_CLASSES = {_CLASS_IN: "in",
            _CLASS_CS: "cs",
            _CLASS_CH: "ch",
            _CLASS_HS: "hs",
            _CLASS_NONE: "none",
            _CLASS_ANY: "any"}

_TYPES = {_TYPE_A: "a",
          _TYPE_NS: "ns",
          _TYPE_MD: "md",
          _TYPE_MF: "mf",
          _TYPE_CNAME: "cname",
          _TYPE_SOA: "soa",
          _TYPE_MB: "mb",
          _TYPE_MG: "mg",
          _TYPE_MR: "mr",
          _TYPE_NULL: "null",
          _TYPE_WKS: "wks",
          _TYPE_PTR: "ptr",
          _TYPE_HINFO: "hinfo",
          _TYPE_MINFO: "minfo",
          _TYPE_MX: "mx",
          _TYPE_TXT: "txt",
          _TYPE_AAAA: "quada",
          _TYPE_SRV: "srv",
          _TYPE_ANY: "any"}

# utility functions


def currentTimeMillis():
    """Current system time in milliseconds"""
    return time.time() * 1000

# Exceptions


class NonLocalNameException(Exception):
    pass


class NonUniqueNameException(Exception):
    pass


class NamePartTooLongException(Exception):
    pass


class AbstractMethodException(Exception):
    pass


class BadTypeInNameException(Exception):
    pass

# implementation classes


class DNSEntry(object):

    """A DNS entry"""

    def __init__(self, name, type, clazz):
        self.key = name.lower()
        self.name = name
        self.type = type
        self.clazz = clazz & _CLASS_MASK
        self.unique = (clazz & _CLASS_UNIQUE) != 0

    def __eq__(self, other):
        """Equality test on name, type, and class"""
        return (isinstance(other, DNSEntry) and
                self.name == other.name and
                self.type == other.type and
                self.clazz == other.clazz)

    def __ne__(self, other):
        """Non-equality test"""
        return not self.__eq__(other)

    def getClazz(self, clazz):
        """Class accessor"""
        return _CLASSES.get(clazz, "?(%s)" % clazz)

    def getType(self, t):
        """Type accessor"""
        return _TYPES.get(t, "?(%s)" % t)

    def toString(self, hdr, other):
        """String representation with additional information"""
        result = "%s[%s,%s" % (hdr, self.getType(self.type),
                               self.getClazz(self.clazz))
        if self.unique:
            result += "-unique,"
        else:
            result += ","
        result += self.name
        if other is not None:
            result += ",%s]" % (other)
        else:
            result += "]"
        return result


class DNSQuestion(DNSEntry):

    """A DNS question entry"""

    def __init__(self, name, type, clazz):
        # if not name.endswith(".local."):
        #    raise NonLocalNameException
        DNSEntry.__init__(self, name, type, clazz)

    def answeredBy(self, rec):
        """Returns true if the question is answered by the record"""
        return (self.clazz == rec.clazz and
                (self.type == rec.type or self.type == _TYPE_ANY) and
                self.name == rec.name)

    def __repr__(self):
        """String representation"""
        return DNSEntry.toString(self, "question", None)


class DNSRecord(DNSEntry):

    """A DNS record - like a DNS entry, but has a TTL"""

    def __init__(self, name, type, clazz, ttl):
        DNSEntry.__init__(self, name, type, clazz)
        self.ttl = ttl
        self.created = currentTimeMillis()

    def __eq__(self, other):
        """Tests equality as per DNSRecord"""
        return isinstance(other, DNSRecord) and DNSEntry.__eq__(self, other)

    def suppressedBy(self, msg):
        """Returns true if any answer in a message can suffice for the
        information held in this record."""
        for record in msg.answers:
            if self.suppressedByAnswer(record):
                return True
        return False

    def suppressedByAnswer(self, other):
        """Returns true if another record has same name, type and class,
        and if its TTL is at least half of this record's."""
        return self == other and other.ttl > (self.ttl / 2)

    def getExpirationTime(self, percent):
        """Returns the time at which this record will have expired
        by a certain percentage."""
        return self.created + (percent * self.ttl * 10)

    def getRemainingTTL(self, now):
        """Returns the remaining TTL in seconds."""
        return max(0, (self.getExpirationTime(100) - now) / 1000)

    def isExpired(self, now):
        """Returns true if this record has expired."""
        return self.getExpirationTime(100) <= now

    def isStale(self, now):
        """Returns true if this record is at least half way expired."""
        return self.getExpirationTime(50) <= now

    def resetTTL(self, other):
        """Sets this record's TTL and created time to that of
        another record."""
        self.created = other.created
        self.ttl = other.ttl

    def write(self, out):
        """Abstract method"""
        raise AbstractMethodException

    def toString(self, other):
        """String representation with addtional information"""
        arg = "%s/%s,%s" % (self.ttl,
                            self.getRemainingTTL(currentTimeMillis()), other)
        return DNSEntry.toString(self, "record", arg)


class DNSAddress(DNSRecord):

    """A DNS address record"""

    def __init__(self, name, type, clazz, ttl, address):
        DNSRecord.__init__(self, name, type, clazz, ttl)
        self.address = address

    def write(self, out):
        """Used in constructing an outgoing packet"""
        out.writeString(self.address)

    def __eq__(self, other):
        """Tests equality on address"""
        return isinstance(other, DNSAddress) and self.address == other.address

    def __repr__(self):
        """String representation"""
        try:
            return socket.inet_ntoa(self.address)
        except Exception:  # TODO stop catching all Exceptions
            return self.address


class DNSHinfo(DNSRecord):

    """A DNS host information record"""

    def __init__(self, name, type, clazz, ttl, cpu, os):
        DNSRecord.__init__(self, name, type, clazz, ttl)
        self.cpu = cpu
        self.os = os

    def write(self, out):
        """Used in constructing an outgoing packet"""
        out.writeString(self.cpu)
        out.writeString(self.oso)

    def __eq__(self, other):
        """Tests equality on cpu and os"""
        return (isinstance(other, DNSHinfo) and
                self.cpu == other.cpu and self.os == other.os)

    def __repr__(self):
        """String representation"""
        return self.cpu + " " + self.os


class DNSPointer(DNSRecord):

    """A DNS pointer record"""

    def __init__(self, name, type, clazz, ttl, alias):
        DNSRecord.__init__(self, name, type, clazz, ttl)
        self.alias = alias

    def write(self, out):
        """Used in constructing an outgoing packet"""
        out.writeName(self.alias)

    def __eq__(self, other):
        """Tests equality on alias"""
        return isinstance(other, DNSPointer) and self.alias == other.alias

    def __repr__(self):
        """String representation"""
        return self.toString(self.alias)


class DNSText(DNSRecord):

    """A DNS text record"""

    def __init__(self, name, type_, clazz, ttl, text):
        assert isinstance(text, (bytes, type(None)))
        DNSRecord.__init__(self, name, type_, clazz, ttl)
        self.text = text

    def write(self, out):
        """Used in constructing an outgoing packet"""
        out.writeString(self.text)

    def __eq__(self, other):
        """Tests equality on text"""
        return isinstance(other, DNSText) and self.text == other.text

    def __repr__(self):
        """String representation"""
        if len(self.text) > 10:
            return self.toString(self.text[:7] + "...")
        else:
            return self.toString(self.text)


class DNSService(DNSRecord):

    """A DNS service record"""

    def __init__(self, name, type, clazz, ttl, priority, weight, port, server):
        DNSRecord.__init__(self, name, type, clazz, ttl)
        self.priority = priority
        self.weight = weight
        self.port = port
        self.server = server

    def write(self, out):
        """Used in constructing an outgoing packet"""
        out.writeShort(self.priority)
        out.writeShort(self.weight)
        out.writeShort(self.port)
        out.writeName(self.server)

    def __eq__(self, other):
        """Tests equality on priority, weight, port and server"""
        return (isinstance(other, DNSService) and
                self.priority == other.priority and
                self.weight == other.weight and
                self.port == other.port and
                self.server == other.server)

    def __repr__(self):
        """String representation"""
        return self.toString("%s:%s" % (self.server, self.port))


class DNSIncoming(object):

    """Object representation of an incoming DNS packet"""

    def __init__(self, data):
        """Constructor from string holding bytes of packet"""
        self.offset = 0
        self.data = data
        self.questions = []
        self.answers = []
        self.numQuestions = 0
        self.numAnswers = 0
        self.numAuthorities = 0
        self.numAdditionals = 0

        self.readHeader()
        self.readQuestions()
        self.readOthers()

    def unpack(self, format):
        length = struct.calcsize(format)
        info = struct.unpack(format, self.data[self.offset:self.offset + length])
        self.offset += length
        return info

    def readHeader(self):
        """Reads header portion of packet"""
        (self.id, self.flags, self.numQuestions, self.numAnswers,
         self.numAuthorities, self.numAdditionals) = self.unpack(b'!6H')

    def readQuestions(self):
        """Reads questions section of packet"""
        for i in xrange(self.numQuestions):
            name = self.readName()
            type, clazz = self.unpack(b'!HH')

            question = DNSQuestion(name, type, clazz)
            self.questions.append(question)

    def readInt(self):
        """Reads an integer from the packet"""
        return self.unpack(b'!I')[0]

    def readCharacterString(self):
        """Reads a character string from the packet"""
        length = byte_ord(self.data[self.offset])
        self.offset += 1
        return self.readString(length)

    def readString(self, length):
        """Reads a string of a given length from the packet"""
        info = self.data[self.offset:self.offset + length]
        self.offset += length
        return info

    def readUnsignedShort(self):
        """Reads an unsigned short from the packet"""
        return self.unpack(b'!H')[0]

    def readOthers(self):
        """Reads the answers, authorities and additionals section of the
        packet"""
        n = self.numAnswers + self.numAuthorities + self.numAdditionals
        for i in xrange(n):
            domain = self.readName()
            type, clazz, ttl, length = self.unpack(b'!HHiH')

            rec = None
            if type == _TYPE_A:
                rec = DNSAddress(domain, type, clazz, ttl, self.readString(4))
            elif type == _TYPE_CNAME or type == _TYPE_PTR:
                rec = DNSPointer(domain, type, clazz, ttl, self.readName())
            elif type == _TYPE_TXT:
                rec = DNSText(domain, type, clazz, ttl, self.readString(length))
            elif type == _TYPE_SRV:
                rec = DNSService(domain, type, clazz, ttl,
                                 self.readUnsignedShort(), self.readUnsignedShort(),
                                 self.readUnsignedShort(), self.readName())
            elif type == _TYPE_HINFO:
                rec = DNSHinfo(domain, type, clazz, ttl,
                               self.readCharacterString(), self.readCharacterString())
            elif type == _TYPE_AAAA:
                rec = DNSAddress(domain, type, clazz, ttl, self.readString(16))
            else:
                # Try to ignore types we don't know about
                # Skip the payload for the resource record so the next
                # records can be parsed correctly
                self.offset += length

            if rec is not None:
                self.answers.append(rec)

    def isQuery(self):
        """Returns true if this is a query"""
        return (self.flags & _FLAGS_QR_MASK) == _FLAGS_QR_QUERY

    def isResponse(self):
        """Returns true if this is a response"""
        return (self.flags & _FLAGS_QR_MASK) == _FLAGS_QR_RESPONSE

    def readUTF(self, offset, length):
        """Reads a UTF-8 string of a given length from the packet"""
        return unicode(self.data[offset:offset + length], 'utf-8', 'replace')

    def readName(self):
        """Reads a domain name from the packet"""
        result = ''
        off = self.offset
        next = -1
        first = off

        while True:
            length = byte_ord(self.data[off])
            off += 1
            if length == 0:
                break
            t = length & 0xC0
            if t == 0x00:
                result = ''.join((result, self.readUTF(off, length) + '.'))
                off += length
            elif t == 0xC0:
                if next < 0:
                    next = off + 1
                off = ((length & 0x3F) << 8) | byte_ord(self.data[off])
                if off >= first:
                    # TODO raise more specific exception
                    raise Exception("Bad domain name (circular) at %s" % (off,))
                first = off
            else:
                # TODO raise more specific exception
                raise Exception("Bad domain name at %s" % (off,))

        if next >= 0:
            self.offset = next
        else:
            self.offset = off

        return result


class DNSOutgoing(object):

    """Object representation of an outgoing packet"""

    def __init__(self, flags, multicast=True):
        self.finished = False
        self.id = 0
        self.multicast = multicast
        self.flags = flags
        self.names = {}
        self.data = []
        self.size = 12

        self.questions = []
        self.answers = []
        self.authorities = []
        self.additionals = []

    def addQuestion(self, record):
        """Adds a question"""
        self.questions.append(record)

    def addAnswer(self, inp, record):
        """Adds an answer"""
        if not record.suppressedBy(inp):
            self.addAnswerAtTime(record, 0)

    def addAnswerAtTime(self, record, now):
        """Adds an answer if if does not expire by a certain time"""
        if record is not None:
            if now == 0 or not record.isExpired(now):
                self.answers.append((record, now))

    def addAuthorativeAnswer(self, record):
        """Adds an authoritative answer"""
        self.authorities.append(record)

    def addAdditionalAnswer(self, record):
        """Adds an additional answer"""
        self.additionals.append(record)

    def pack(self, format, value):
        self.data.append(struct.pack(format, value))
        self.size += struct.calcsize(format)

    def writeByte(self, value):
        """Writes a single byte to the packet"""
        self.pack(b'!c', byte_chr(value))

    def insertShort(self, index, value):
        """Inserts an unsigned short in a certain position in the packet"""
        self.data.insert(index, struct.pack(b'!H', value))
        self.size += 2

    def writeShort(self, value):
        """Writes an unsigned short to the packet"""
        self.pack(b'!H', value)

    def writeInt(self, value):
        """Writes an unsigned integer to the packet"""
        self.pack(b'!I', int(value))

    def writeString(self, value):
        """Writes a string to the packet"""
        assert isinstance(value, bytes)
        self.data.append(value)
        self.size += len(value)

    def writeUTF(self, s):
        """Writes a UTF-8 string of a given length to the packet"""
        utfstr = s.encode('utf-8')
        length = len(utfstr)
        if length > 64:
            raise NamePartTooLongException
        self.writeByte(length)
        self.writeString(utfstr)

    def writeName(self, name):
        """Writes a domain name to the packet"""

        if name in self.names:
            # Find existing instance of this name in packet
            #
            index = self.names[name]

            # An index was found, so write a pointer to it
            #
            self.writeByte((index >> 8) | 0xC0)
            self.writeByte(index & 0xFF)
        else:
            # No record of this name already, so write it
            # out as normal, recording the location of the name
            # for future pointers to it.
            #
            self.names[name] = self.size
            parts = name.split('.')
            if parts[-1] == '':
                parts = parts[:-1]
            for part in parts:
                self.writeUTF(part)
            self.writeByte(0)

    def writeQuestion(self, question):
        """Writes a question to the packet"""
        self.writeName(question.name)
        self.writeShort(question.type)
        self.writeShort(question.clazz)

    def writeRecord(self, record, now):
        """Writes a record (answer, authoritative answer, additional) to
        the packet"""
        self.writeName(record.name)
        self.writeShort(record.type)
        if record.unique and self.multicast:
            self.writeShort(record.clazz | _CLASS_UNIQUE)
        else:
            self.writeShort(record.clazz)
        if now == 0:
            self.writeInt(record.ttl)
        else:
            self.writeInt(record.getRemainingTTL(now))
        index = len(self.data)
        # Adjust size for the short we will write before this record
        #
        self.size += 2
        record.write(self)
        self.size -= 2

        length = len(b''.join(self.data[index:]))
        self.insertShort(index, length)  # Here is the short we adjusted for

    def packet(self):
        """Returns a string containing the packet's bytes

        No further parts should be added to the packet once this
        is done."""
        if not self.finished:
            self.finished = True
            for question in self.questions:
                self.writeQuestion(question)
            for answer, time_ in self.answers:
                self.writeRecord(answer, time_)
            for authority in self.authorities:
                self.writeRecord(authority, 0)
            for additional in self.additionals:
                self.writeRecord(additional, 0)

            self.insertShort(0, len(self.additionals))
            self.insertShort(0, len(self.authorities))
            self.insertShort(0, len(self.answers))
            self.insertShort(0, len(self.questions))
            self.insertShort(0, self.flags)
            if self.multicast:
                self.insertShort(0, 0)
            else:
                self.insertShort(0, self.id)
        return b''.join(self.data)


class DNSCache(object):

    """A cache of DNS entries"""

    def __init__(self):
        self.cache = {}

    def add(self, entry):
        """Adds an entry"""
        try:
            list = self.cache[entry.key]
        except Exception:  # TODO stop catching all Exceptions
            list = self.cache[entry.key] = []
        list.append(entry)

    def remove(self, entry):
        """Removes an entry"""
        try:
            list = self.cache[entry.key]
            list.remove(entry)
        except Exception:  # TODO stop catching all Exceptions
            pass

    def get(self, entry):
        """Gets an entry by key.  Will return None if there is no
        matching entry."""
        try:
            list = self.cache[entry.key]
            return list[list.index(entry)]
        except Exception:  # TODO stop catching all Exceptions
            return None

    def getByDetails(self, name, type, clazz):
        """Gets an entry by details.  Will return None if there is
        no matching entry."""
        entry = DNSEntry(name, type, clazz)
        return self.get(entry)

    def entriesWithName(self, name):
        """Returns a list of entries whose key matches the name."""
        try:
            return self.cache[name]
        except Exception:  # TODO stop catching all Exceptions
            return []

    def entries(self):
        """Returns a list of all entries"""
        def add(x, y):
            return x + y
        try:
            return reduce(add, self.cache.values())
        except Exception:  # TODO stop catching all Exceptions
            return []


class Engine(threading.Thread):

    """An engine wraps read access to sockets, allowing objects that
    need to receive data from sockets to be called back when the
    sockets are ready.

    A reader needs a handle_read() method, which is called when the socket
    it is interested in is ready for reading.

    Writers are not implemented here, because we only send short
    packets.
    """

    def __init__(self, zc):
        threading.Thread.__init__(self)
        self.daemon = True
        self.zc = zc
        self.readers = {}  # maps socket to reader
        self.timeout = 5
        self.condition = threading.Condition()
        self.start()

    def run(self):
        while not _GLOBAL_DONE:
            rs = self.getReaders()
            if len(rs) == 0:
                # No sockets to manage, but we wait for the timeout
                # or addition of a socket
                #
                self.condition.acquire()
                self.condition.wait(self.timeout)
                self.condition.release()
            else:
                try:
                    rr, wr, er = select.select(rs, [], [], self.timeout)
                    for socket_ in rr:
                        try:
                            self.readers[socket_].handle_read()
                        except Exception:  # TODO stop catching all Exceptions
                            traceback.print_exc()
                except Exception:  # TODO stop catching all Exceptions
                    pass

    def getReaders(self):
        result = []
        self.condition.acquire()
        result = self.readers.keys()
        self.condition.release()
        return result

    def addReader(self, reader, socket):
        self.condition.acquire()
        self.readers[socket] = reader
        self.condition.notify()
        self.condition.release()

    def delReader(self, socket):
        self.condition.acquire()
        del(self.readers[socket])
        self.condition.notify()
        self.condition.release()

    def notify(self):
        self.condition.acquire()
        self.condition.notify()
        self.condition.release()


class Listener(object):

    """A Listener is used by this module to listen on the multicast
    group to which DNS messages are sent, allowing the implementation
    to cache information as it arrives.

    It requires registration with an Engine object in order to have
    the read() method called when a socket is availble for reading."""

    def __init__(self, zc):
        self.zc = zc
        self.zc.engine.addReader(self, self.zc.socket)

    def handle_read(self):
        try:
            data, (addr, port) = self.zc.socket.recvfrom(_MAX_MSG_ABSOLUTE)
        except socket.error as e:
            # If the socket was closed by another thread -- which happens
            # regularly on shutdown -- an EBADF exception is thrown here.
            # Ignore it.
            if e.errno == socket.EBADF:
                return
            else:
                raise e
        self.data = data
        msg = DNSIncoming(data)
        if msg.isQuery():
            # Always multicast responses
            #
            if port == _MDNS_PORT:
                self.zc.handleQuery(msg, _MDNS_ADDR, _MDNS_PORT)
            # If it's not a multicast query, reply via unicast
            # and multicast
            #
            elif port == _DNS_PORT:
                self.zc.handleQuery(msg, addr, port)
                self.zc.handleQuery(msg, _MDNS_ADDR, _MDNS_PORT)
        else:
            self.zc.handleResponse(msg)


class Reaper(threading.Thread):

    """A Reaper is used by this module to remove cache entries that
    have expired."""

    def __init__(self, zc):
        threading.Thread.__init__(self)
        self.daemon = True
        self.zc = zc
        self.start()

    def run(self):
        while True:
            self.zc.wait(10 * 1000)
            if _GLOBAL_DONE:
                return
            now = currentTimeMillis()
            for record in self.zc.cache.entries():
                if record.isExpired(now):
                    self.zc.updateRecord(now, record)
                    self.zc.cache.remove(record)


class ServiceBrowser(threading.Thread):

    """Used to browse for a service of a specific type.

    The listener object will have its addService() and
    removeService() methods called when this browser
    discovers changes in the services availability."""

    def __init__(self, zc, type, listener):
        """Creates a browser for a specific type"""
        threading.Thread.__init__(self)
        self.daemon = True
        self.zc = zc
        self.type = type
        self.listener = listener
        self.services = {}
        self.nextTime = currentTimeMillis()
        self.delay = _BROWSER_TIME
        self.list = []

        self.done = False

        self.zc.addListener(self, DNSQuestion(self.type, _TYPE_PTR, _CLASS_IN))
        self.start()

    def updateRecord(self, zc, now, record):
        """Callback invoked by Zeroconf when new information arrives.

        Updates information required by browser in the Zeroconf cache."""
        if record.type == _TYPE_PTR and record.name == self.type:
            expired = record.isExpired(now)
            try:
                oldrecord = self.services[record.alias.lower()]
                if not expired:
                    oldrecord.resetTTL(record)
                else:
                    del(self.services[record.alias.lower()])
                    callback = lambda x: self.listener.removeService(x,
                                                                     self.type, record.alias)
                    self.list.append(callback)
                    return
            except Exception:  # TODO stop catching all Exceptions
                if not expired:
                    self.services[record.alias.lower()] = record
                    callback = lambda x: self.listener.addService(x,
                                                                  self.type, record.alias)
                    self.list.append(callback)

            expires = record.getExpirationTime(75)
            if expires < self.nextTime:
                self.nextTime = expires

    def cancel(self):
        self.done = True
        self.zc.notifyAll()

    def run(self):
        while True:
            event = None
            now = currentTimeMillis()
            if len(self.list) == 0 and self.nextTime > now:
                self.zc.wait(self.nextTime - now)
            if _GLOBAL_DONE or self.done:
                return
            now = currentTimeMillis()

            if self.nextTime <= now:
                out = DNSOutgoing(_FLAGS_QR_QUERY)
                out.addQuestion(DNSQuestion(self.type, _TYPE_PTR, _CLASS_IN))
                for record in self.services.values():
                    if not record.isExpired(now):
                        out.addAnswerAtTime(record, now)
                self.zc.send(out)
                self.nextTime = now + self.delay
                self.delay = min(20 * 1000, self.delay * 2)

            if len(self.list) > 0:
                event = self.list.pop(0)

            if event is not None:
                event(self.zc)


class ServiceInfo(object):

    """Service information"""

    def __init__(self, type, name, address=None, port=None, weight=0,
                 priority=0, properties=None, server=None):
        """Create a service description.

        type: fully qualified service type name
        name: fully qualified service name
        address: IP address as unsigned short, network byte order
        port: port that the service runs on
        weight: weight of the service
        priority: priority of the service
        properties: dictionary of properties (or a string holding the
                    bytes for the text field)
        server: fully qualified name for service host (defaults to name)"""

        if not name.endswith(type):
            raise BadTypeInNameException
        self.type = type
        self.name = name
        self.address = address
        self.port = port
        self.weight = weight
        self.priority = priority
        if server:
            self.server = server
        else:
            self.server = name
        self.setProperties(properties)

    def setProperties(self, properties):
        """Sets properties and text of this info from a dictionary"""
        if isinstance(properties, dict):
            self.properties = properties
            list = []
            result = b''
            for key in properties:
                value = properties[key]
                if isinstance(key, unicode):
                    key = key.encode('utf-8')

                if value is None:
                    suffix = b''
                elif isinstance(value, unicode):
                    suffix = value.encode('utf-8')
                elif isinstance(value, int):
                    if value:
                        suffix = b'true'
                    else:
                        suffix = b'false'
                else:
                    suffix = b''
                list.append(b'='.join((key, suffix)))
            for item in list:
                result = b''.join((result, byte_chr(len(item)), item))
            self.text = result
        else:
            self.text = properties

    def setText(self, text):
        """Sets properties and text given a text field"""
        self.text = text
        try:
            result = {}
            end = len(text)
            index = 0
            strs = []
            while index < end:
                length = byte_ord(text[index])
                index += 1
                strs.append(text[index:index + length])
                index += length

            for s in strs:
                try:
                    key, value = s.split('=', 1)
                    if value == 'true':
                        value = True
                    elif value == 'false' or not value:
                        value = False
                except Exception:  # TODO stop catching all Exceptions
                    # No equals sign at all
                    key = s
                    value = False

                # Only update non-existent properties
                if key and result.get(key) is None:
                    result[key] = value

            self.properties = result
        except Exception:  # TODO stop catching all Exceptions
            traceback.print_exc()
            self.properties = None

    def getType(self):
        """Type accessor"""
        return self.type

    def getName(self):
        """Name accessor"""
        if self.type is not None and self.name.endswith("." + self.type):
            return self.name[:len(self.name) - len(self.type) - 1]
        return self.name

    def getAddress(self):
        """Address accessor"""
        return self.address

    def getPort(self):
        """Port accessor"""
        return self.port

    def getPriority(self):
        """Pirority accessor"""
        return self.priority

    def getWeight(self):
        """Weight accessor"""
        return self.weight

    def getProperties(self):
        """Properties accessor"""
        return self.properties

    def getText(self):
        """Text accessor"""
        return self.text

    def getServer(self):
        """Server accessor"""
        return self.server

    def updateRecord(self, zc, now, record):
        """Updates service information from a DNS record"""
        if record is not None and not record.isExpired(now):
            if record.type == _TYPE_A:
                # if record.name == self.name:
                if record.name == self.server:
                    self.address = record.address
            elif record.type == _TYPE_SRV:
                if record.name == self.name:
                    self.server = record.server
                    self.port = record.port
                    self.weight = record.weight
                    self.priority = record.priority
                    # self.address = None
                    self.updateRecord(zc, now,
                                      zc.cache.getByDetails(self.server, _TYPE_A, _CLASS_IN))
            elif record.type == _TYPE_TXT:
                if record.name == self.name:
                    self.setText(record.text)

    def request(self, zc, timeout):
        """Returns true if the service could be discovered on the
        network, and updates this object with details discovered.
        """
        now = currentTimeMillis()
        delay = _LISTENER_TIME
        next = now + delay
        last = now + timeout
        result = False
        try:
            zc.addListener(self, DNSQuestion(self.name, _TYPE_ANY, _CLASS_IN))
            while (self.server is None or self.address is None or
                   self.text is None):
                if last <= now:
                    return False
                if next <= now:
                    out = DNSOutgoing(_FLAGS_QR_QUERY)
                    out.addQuestion(DNSQuestion(self.name, _TYPE_SRV,
                                                _CLASS_IN))
                    out.addAnswerAtTime(zc.cache.getByDetails(self.name,
                                                              _TYPE_SRV, _CLASS_IN), now)
                    out.addQuestion(DNSQuestion(self.name, _TYPE_TXT,
                                                _CLASS_IN))
                    out.addAnswerAtTime(zc.cache.getByDetails(self.name,
                                                              _TYPE_TXT, _CLASS_IN), now)
                    if self.server is not None:
                        out.addQuestion(DNSQuestion(self.server,
                                                    _TYPE_A, _CLASS_IN))
                        out.addAnswerAtTime(zc.cache.getByDetails(self.server,
                                                                  _TYPE_A, _CLASS_IN), now)
                    zc.send(out)
                    next = now + delay
                    delay = delay * 2

                zc.wait(min(next, last) - now)
                now = currentTimeMillis()
            result = True
        finally:
            zc.removeListener(self)

        return result

    def __eq__(self, other):
        """Tests equality of service name"""
        if isinstance(other, ServiceInfo):
            return other.name == self.name
        return False

    def __ne__(self, other):
        """Non-equality test"""
        return not self.__eq__(other)

    def __repr__(self):
        """String representation"""
        result = "service[%s,%s:%s," % (self.name,
                                        socket.inet_ntoa(self.getAddress()), self.port)
        if self.text is None:
            result += "None"
        else:
            if len(self.text) < 20:
                result += self.text
            else:
                result += self.text[:17] + "..."
        result += "]"
        return result


class Zeroconf(object):

    """Implementation of Zeroconf Multicast DNS Service Discovery

    Supports registration, unregistration, queries and browsing.
    """

    def __init__(self, bindaddress=None):
        """Creates an instance of the Zeroconf class, establishing
        multicast communications, listening and reaping threads."""
        global _GLOBAL_DONE
        _GLOBAL_DONE = False
        if bindaddress is None:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(('4.2.2.1', 123))
                self.intf = s.getsockname()[0]
            except Exception:  # TODO stop catching all Exceptions
                self.intf = socket.gethostbyname(socket.gethostname())
        else:
            self.intf = bindaddress
        self.group = ('', _MDNS_PORT)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except Exception:  # TODO stop catching all Exceptions
            # SO_REUSEADDR should be equivalent to SO_REUSEPORT for
            # multicast UDP sockets (p 731, "TCP/IP Illustrated,
            # Volume 2"), but some BSD-derived systems require
            # SO_REUSEPORT to be specified explicity.  Also, not all
            # versions of Python have SO_REUSEPORT available.
            #
            pass
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
        try:
            self.socket.bind(self.group)
        except Exception:  # TODO stop catching all Exceptions
            # Some versions of linux raise an exception even though
            # the SO_REUSE* options have been set, so ignore it
            #
            pass
        # self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF,
        #    socket.inet_aton(self.intf) + socket.inet_aton('0.0.0.0'))
        self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                               socket.inet_aton(_MDNS_ADDR) + socket.inet_aton('0.0.0.0'))

        self.listeners = []
        self.browsers = []
        self.services = {}
        self.servicetypes = {}

        self.cache = DNSCache()

        self.condition = threading.Condition()

        self.engine = Engine(self)
        self.listener = Listener(self)
        self.reaper = Reaper(self)

    def isLoopback(self):
        return self.intf.startswith("127.0.0.1")

    def isLinklocal(self):
        return self.intf.startswith("169.254.")

    def wait(self, timeout):
        """Calling thread waits for a given number of milliseconds or
        until notified."""
        self.condition.acquire()
        self.condition.wait(timeout / 1000)
        self.condition.release()

    def notifyAll(self):
        """Notifies all waiting threads"""
        self.condition.acquire()
        self.condition.notifyAll()
        self.condition.release()

    def getServiceInfo(self, type, name, timeout=3000):
        """Returns network's service information for a particular
        name and type, or None if no service matches by the timeout,
        which defaults to 3 seconds."""
        info = ServiceInfo(type, name)
        if info.request(self, timeout):
            return info
        return None

    def addServiceListener(self, type, listener):
        """Adds a listener for a particular service type.  This object
        will then have its updateRecord method called when information
        arrives for that type."""
        self.removeServiceListener(listener)
        self.browsers.append(ServiceBrowser(self, type, listener))

    def removeServiceListener(self, listener):
        """Removes a listener from the set that is currently listening."""
        for browser in self.browsers:
            if browser.listener == listener:
                browser.cancel()
                del(browser)

    def registerService(self, info, ttl=_DNS_TTL):
        """Registers service information to the network with a default TTL
        of 60 seconds.  Zeroconf will then respond to requests for
        information for that service.  The name of the service may be
        changed if needed to make it unique on the network."""
        self.checkService(info)
        self.services[info.name.lower()] = info
        if info.type in self.servicetypes:
            self.servicetypes[info.type] += 1
        else:
            self.servicetypes[info.type] = 1
        now = currentTimeMillis()
        nextTime = now
        i = 0
        while i < 3:
            if now < nextTime:
                self.wait(nextTime - now)
                now = currentTimeMillis()
                continue
            out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
            out.addAnswerAtTime(DNSPointer(info.type, _TYPE_PTR,
                                           _CLASS_IN, ttl, info.name), 0)
            out.addAnswerAtTime(DNSService(info.name, _TYPE_SRV,
                                           _CLASS_IN, ttl, info.priority, info.weight, info.port,
                                           info.server), 0)
            out.addAnswerAtTime(DNSText(info.name, _TYPE_TXT, _CLASS_IN,
                                        ttl, info.text), 0)
            if info.address:
                out.addAnswerAtTime(DNSAddress(info.server, _TYPE_A,
                                               _CLASS_IN, ttl, info.address), 0)
            self.send(out)
            i += 1
            nextTime += _REGISTER_TIME

    def unregisterService(self, info):
        """Unregister a service."""
        try:
            del(self.services[info.name.lower()])
            if self.servicetypes[info.type] > 1:
                self.servicetypes[info.type] -= 1
            else:
                del self.servicetypes[info.type]
        except Exception:  # TODO stop catching all Exceptions
            pass
        now = currentTimeMillis()
        nextTime = now
        i = 0
        while i < 3:
            if now < nextTime:
                self.wait(nextTime - now)
                now = currentTimeMillis()
                continue
            out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
            out.addAnswerAtTime(DNSPointer(info.type, _TYPE_PTR,
                                           _CLASS_IN, 0, info.name), 0)
            out.addAnswerAtTime(DNSService(info.name, _TYPE_SRV,
                                           _CLASS_IN, 0, info.priority, info.weight, info.port,
                                           info.name), 0)
            out.addAnswerAtTime(DNSText(info.name, _TYPE_TXT, _CLASS_IN,
                                        0, info.text), 0)
            if info.address:
                out.addAnswerAtTime(DNSAddress(info.server, _TYPE_A,
                                               _CLASS_IN, 0, info.address), 0)
            self.send(out)
            i += 1
            nextTime += _UNREGISTER_TIME

    def unregisterAllServices(self):
        """Unregister all registered services."""
        if len(self.services) > 0:
            now = currentTimeMillis()
            nextTime = now
            i = 0
            while i < 3:
                if now < nextTime:
                    self.wait(nextTime - now)
                    now = currentTimeMillis()
                    continue
                out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                for info in self.services.values():
                    out.addAnswerAtTime(DNSPointer(info.type, _TYPE_PTR,
                                                   _CLASS_IN, 0, info.name), 0)
                    out.addAnswerAtTime(DNSService(info.name, _TYPE_SRV,
                                                   _CLASS_IN, 0, info.priority, info.weight,
                                                   info.port, info.server), 0)
                    out.addAnswerAtTime(DNSText(info.name, _TYPE_TXT,
                                                _CLASS_IN, 0, info.text), 0)
                    if info.address:
                        out.addAnswerAtTime(DNSAddress(info.server,
                                                       _TYPE_A, _CLASS_IN, 0, info.address), 0)
                self.send(out)
                i += 1
                nextTime += _UNREGISTER_TIME

    def checkService(self, info):
        """Checks the network for a unique service name, modifying the
        ServiceInfo passed in if it is not unique."""
        now = currentTimeMillis()
        nextTime = now
        i = 0
        while i < 3:
            for record in self.cache.entriesWithName(info.type):
                if (record.type == _TYPE_PTR and
                        not record.isExpired(now) and
                        record.alias == info.name):
                    if info.name.find('.') < 0:
                        info.name = '%s.[%s:%s].%s' % (info.name,
                                                       info.address, info.port, info.type)

                        self.checkService(info)
                        return
                    raise NonUniqueNameException
            if now < nextTime:
                self.wait(nextTime - now)
                now = currentTimeMillis()
                continue
            out = DNSOutgoing(_FLAGS_QR_QUERY | _FLAGS_AA)
            self.debug = out
            out.addQuestion(DNSQuestion(info.type, _TYPE_PTR, _CLASS_IN))
            out.addAuthorativeAnswer(DNSPointer(info.type, _TYPE_PTR,
                                                _CLASS_IN, _DNS_TTL, info.name))
            self.send(out)
            i += 1
            nextTime += _CHECK_TIME

    def addListener(self, listener, question):
        """Adds a listener for a given question.  The listener will have
        its updateRecord method called when information is available to
        answer the question."""
        now = currentTimeMillis()
        self.listeners.append(listener)
        if question is not None:
            for record in self.cache.entriesWithName(question.name):
                if question.answeredBy(record) and not record.isExpired(now):
                    listener.updateRecord(self, now, record)
        self.notifyAll()

    def removeListener(self, listener):
        """Removes a listener."""
        try:
            self.listeners.remove(listener)
            self.notifyAll()
        except Exception:  # TODO stop catching all Exceptions
            pass

    def updateRecord(self, now, rec):
        """Used to notify listeners of new information that has updated
        a record."""
        for listener in self.listeners:
            listener.updateRecord(self, now, rec)
        self.notifyAll()

    def handleResponse(self, msg):
        """Deal with incoming response packets.  All answers
        are held in the cache, and listeners are notified."""
        now = currentTimeMillis()
        for record in msg.answers:
            expired = record.isExpired(now)
            if record in self.cache.entries():
                if expired:
                    self.cache.remove(record)
                else:
                    entry = self.cache.get(record)
                    if entry is not None:
                        entry.resetTTL(record)
                        record = entry
            else:
                self.cache.add(record)

            self.updateRecord(now, record)

    def handleQuery(self, msg, addr, port):
        """Deal with incoming query packets.  Provides a response if
        possible."""
        out = None

        # Support unicast client responses
        #
        if port != _MDNS_PORT:
            out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA, False)
            for question in msg.questions:
                out.addQuestion(question)

        for question in msg.questions:
            if question.type == _TYPE_PTR:
                if question.name == "_services._dns-sd._udp.local.":
                    for stype in self.servicetypes.keys():
                        if out is None:
                            out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                        out.addAnswer(msg,
                                      DNSPointer("_services._dns-sd._udp.local.",
                                                 _TYPE_PTR, _CLASS_IN, _DNS_TTL, stype))
                for service in self.services.values():
                    if question.name == service.type:
                        if out is None:
                            out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)
                        out.addAnswer(msg,
                                      DNSPointer(service.type, _TYPE_PTR,
                                                 _CLASS_IN, _DNS_TTL, service.name))
            else:
                try:
                    if out is None:
                        out = DNSOutgoing(_FLAGS_QR_RESPONSE | _FLAGS_AA)

                    # Answer A record queries for any service addresses we know
                    if question.type in (_TYPE_A, _TYPE_ANY):
                        for service in self.services.values():
                            if service.server == question.name.lower():
                                out.addAnswer(msg, DNSAddress(question.name,
                                                              _TYPE_A, _CLASS_IN | _CLASS_UNIQUE,
                                                              _DNS_TTL, service.address))

                    service = self.services.get(question.name.lower(), None)
                    if not service:
                        continue

                    if question.type in (_TYPE_SRV, _TYPE_ANY):
                        out.addAnswer(msg, DNSService(question.name,
                                                      _TYPE_SRV, _CLASS_IN | _CLASS_UNIQUE,
                                                      _DNS_TTL, service.priority, service.weight,
                                                      service.port, service.server))
                    if question.type in (_TYPE_TXT, _TYPE_ANY):
                        out.addAnswer(msg, DNSText(question.name,
                                                   _TYPE_TXT, _CLASS_IN | _CLASS_UNIQUE,
                                                   _DNS_TTL, service.text))
                    if question.type == _TYPE_SRV:
                        out.addAdditionalAnswer(DNSAddress(service.server,
                                                           _TYPE_A, _CLASS_IN | _CLASS_UNIQUE,
                                                           _DNS_TTL, service.address))
                except Exception:  # TODO stop catching all Exceptions
                    traceback.print_exc()

        if out is not None and out.answers:
            out.id = msg.id
            self.send(out, addr, port)

    def send(self, out, addr=_MDNS_ADDR, port=_MDNS_PORT):
        """Sends an outgoing packet."""
        packet = out.packet()
        try:
            while packet:
                bytes_sent = self.socket.sendto(packet, 0, (addr, port))
                if bytes_sent < 0:
                    break
                packet = packet[bytes_sent:]
        except Exception:  # TODO stop catching all Exceptions
            # Ignore this, it may be a temporary loss of network connection
            pass

    def close(self):
        """Ends the background threads, and prevent this instance from
        servicing further queries."""
        global _GLOBAL_DONE
        if not _GLOBAL_DONE:
            _GLOBAL_DONE = True
            self.notifyAll()
            self.engine.notify()
            self.unregisterAllServices()
            self.socket.setsockopt(socket.IPPROTO_IP,
                                   socket.IP_DROP_MEMBERSHIP,
                                   socket.inet_aton(_MDNS_ADDR) +
                                   socket.inet_aton('0.0.0.0'))
            self.socket.close()

# Test a few module features, including service registration, service
# query (for Zoe), and service unregistration.

if __name__ == '__main__':
    print("Multicast DNS Service Discovery for Python, version %s" % __version__)
    r = Zeroconf()
    print("1. Testing registration of a service...")
    desc = {'version': '0.10', 'a': 'test value', 'b': 'another value'}
    info = ServiceInfo("_http._tcp.local.",
                       "My Service Name._http._tcp.local.",
                       socket.inet_aton("127.0.0.1"), 1234, 0, 0, desc)
    print("   Registering service...")
    r.registerService(info)
    print("   Registration done.")
    print("2. Testing query of service information...")
    print("   Getting ZOE service: %s" % (
        r.getServiceInfo("_http._tcp.local.", "ZOE._http._tcp.local.")))
    print("   Query done.")
    print("3. Testing query of own service...")
    print("   Getting self: %s" % (
        r.getServiceInfo("_http._tcp.local.", "My Service Name._http._tcp.local.")),)
    print("   Query done.")
    print("4. Testing unregister of service information...")
    r.unregisterService(info)
    print("   Unregister done.")
    r.close()
