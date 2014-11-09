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

import re

H_EXTS = ['.h']
CPP_EXTS = ['.c', '.cpp', '.S']
INO_EXTS = ['.ino', '.pde']

whitespace = r'\s+'
multi_line_comment = r'/\*[^*]*(?:\*(?!/)[^*]*)*\*/'
single_line_comment = r'//.*?$'
preprocessor_directive = r'^\s*#.*?$'
include = r'^\s*#include\s*[<"](\S+)[">]'
single_quoted_character = r"'.'"
double_quoted_string = r'"(?:[^"\\]|\\.)*"'
prototype = r'[\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\)(?=\s*;)'
function = r'[\w\[\]\*]+\s+[&\[\]\*\w\s]+\([&,\[\]\*\w\s]*\)(?=\s*\{)'


def scrub_comments(src_text):
    """
    Replace all commented portions of a given source text as spaces.

    Args:
        src_text: The source code.

    Returns:
        scrubed_src_text: The scrubed source code.
    """
    pattern_text = multi_line_comment + '|' + single_line_comment
    pattern = re.compile(pattern_text, re.M | re.S)
    scrubed_src_text = pattern.sub('', src_text)
    return scrubed_src_text


def strip(src_text):
    """
    Strips comments, pre-processor directives, single- and double-quoted
    strings from a string.

    Args:
        src_text: The source code to strip.

    Returns:
        striped_src_text: The stripped source code.
    """
    pattern_text = multi_line_comment
    pattern_text += '|' + single_line_comment
    pattern_text += '|' + single_quoted_character
    pattern_text += '|' + double_quoted_string
    pattern_text += '|' + preprocessor_directive

    pattern = re.compile(pattern_text, re.M | re.S)
    striped_src_text = pattern.sub('', src_text)
    return striped_src_text


def get_index_of_first_statement(src_text):
    """
    Returns the index of the first character that's not whitespace, a comment
    or a pre-processor directive.

    Args:
        src_text: The source code.

    Returns:
        index: The index of first statement.
    """
    preprocessor_directive = r'\s*#.*?$'
    pattern_text = preprocessor_directive
    pattern_text += '|' + multi_line_comment
    pattern_text += '|' + single_line_comment
    pattern_text += '|' + whitespace

    pattern = re.compile(pattern_text, re.M | re.S)
    match_iter = pattern.finditer(src_text)

    index = 0
    for match in match_iter:
        if match.start() != index:
            break
        index = match.end()
    return index


def collapse_braces(src_text):
    """
    Removes the contents of all top-level curly brace pairs {}.

    Args:
        src_text: The source code to collapse.

    Returns:
        The collapsed source code.
    """
    nesting = 0
    start_index = 0
    collapsed_src_text = ''

    for index, char in enumerate(src_text):
        if nesting == 0:
            collapsed_src_text += char
        if char == '{':
            if nesting == 0:
                start_index = index + 1
            nesting += 1
        if char == '}':
            if nesting > 0:
                nesting -= 1
            if nesting == 0:
                collapsed_src_text += char
    if nesting != 0:
        collapsed_src_text += src_text[start_index:]
    return collapsed_src_text


def sanitize_text(text):
    """
    """
    words = text.split()
    sanitized_text = ' '.join(words)
    return sanitized_text


def sanitize_arg(arg):
    words = arg.split()
    sanitized_arg = ' '.join(words[:-1])
    return sanitized_arg


def sanitize_prototype(prototype):
    """
    """
    prototype = prototype.replace('*', ' * ')
    (function_name, args_text) = prototype.split('(')
    args_text = args_text.split(')')[0]
    arg_list = []
    if args_text.strip():
        arg_list = args_text.split(',')

    function_name = sanitize_text(function_name)
    arg_list = map(sanitize_text, arg_list)

    args_text = ', '.join(arg_list)

    prototype = function_name + '('
    prototype += args_text
    prototype += ')'
    return prototype


def generate_prototypes_from_src(src_text):
    """
    Generate prototypes for all functions of a given source code.

    Args:
        src_text: The source code.

    Returns:
        all_prototypes: A list of none declared prototypes.
    """
    src_text = collapse_braces(strip(src_text))
    prototype_pattern = re.compile(prototype, re.M | re.S)
    function_pattern = re.compile(function, re.M | re.S)
    prototypes = prototype_pattern.findall(src_text)
    functions = function_pattern.findall(src_text)

    declared_prototypes = list(map(sanitize_prototype, prototypes))
    all_prototypes = list(map(sanitize_prototype, functions))

    for declared_prototype in declared_prototypes:
        if declared_prototype in all_prototypes:
            all_prototypes.remove(declared_prototype)
    all_prototypes = sorted(set(all_prototypes), key=all_prototypes.index)
    return all_prototypes


def generate_prototypes_from_files(files):
    """
    Generate prototypes for all functions of a given file list.

    Args:
        files: The file list.

    Returns:
        all_prototypes: A list of none declared prototypes.
    """
    all_prototypes = []
    for f in files:
        src_text = f.read()
        prototypes = generate_prototypes_from_src(src_text)
        all_prototypes += prototypes
    if 'void setup()' in all_prototypes:
        all_prototypes.remove('void setup()')
    if 'void loop()' in all_prototypes:
        all_prototypes.remove('void loop()')
    return all_prototypes


def combine_ino_files(arduino_version, ino_files):
    prototypes = generate_prototypes_from_files(ino_files)
    arduino_include = '#include "Arduino.h"\n'
    if arduino_version < 100:
        arduino_include = '#include "WProgram.h"\n'

    combined_src = ''
    cur_file = ino_files[0]
    path = cur_file.get_path()
    path = path.replace('\\', '/')
    first_line = '#line 1 "%s"\n' % path

    src_text = cur_file.read()
    index = get_index_of_first_statement(src_text)
    header = src_text[:index]
    footer = src_text[index:]
    start_line_no_of_footer = len(header.split('\n'))
    first_line_of_footer = '#line %d\n' % start_line_no_of_footer

    combined_src += first_line
    combined_src += header
    combined_src += arduino_include
    for prototype in prototypes:
        combined_src += prototype
        combined_src += ';\n'
    combined_src += first_line_of_footer
    combined_src += footer
    combined_src += '\n'

    for cur_file in ino_files[1:]:
        path = cur_file.get_path()
        path = path.replace('\\', '/')
        first_line = '#line 1 "%s"\n' % path

        src_text = cur_file.read()
        combined_src += first_line
        combined_src += src_text
        combined_src += '\n'
    return combined_src


def list_headers_from_src(src_text):
    pattern_text = include
    pattern = re.compile(pattern_text, re.M | re.S)
    headers = pattern.findall(src_text)
    return headers


def list_headers_from_files(files):
    all_headers = []
    for f in files:
        src_text = f.read()
        headers = list_headers_from_src(src_text)
        all_headers += headers
    return all_headers


def list_libraries(files, arduino_info):
    libraries = []
    h_lib_dict = arduino_info.get_h_lib_dict()

    headers = list_headers_from_files(files)
    for header in headers:
        library = h_lib_dict.get(header)
        if library and not library in libraries:
            libraries.append(library)
    return libraries
