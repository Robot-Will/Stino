#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Doc."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import os
import re
from . import file

MAX_LINE_LENGTH = 80

INO_EXTS = ['.ino', '.pde']
H_EXTS = ['.h', '.hh', '.hpp']
C_EXTS = ['.c', '.cc']
CPP_EXTS = ['.cpp', '.cxx']
S_EXTS = ['.S']
CC_EXTS = CPP_EXTS + C_EXTS + S_EXTS
INOC_EXTS = INO_EXTS + CC_EXTS
SRC_EXTS = INOC_EXTS + H_EXTS
chars = '_abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
num_chars = '0123456789.'
var_chars = chars + num_chars
none_operator_chars = var_chars

whitespace = r'\s+'
preprocessor_directive = r'\s*#.*?$'
multi_line_comment = r'/\*[^*]*(?:\*(?!/)[^*]*)*\*/'
single_line_comment = r'//.*?$'
double_quoted_string = r'"(?:[^"\\]|\\.)*"'
include = r'#include\s*[<"](\S+)[">]'


def is_cpp_file(file_name):
    """."""
    state = False
    ext = os.path.splitext(file_name)[1]
    if ext in SRC_EXTS:
        state = True
    return state


def strip_back_slash(lines):
    """Doc."""
    new_lines = []
    is_last_break_line = False
    last_line = ''

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if not is_last_break_line:
            cur_line = line
        else:
            cur_line = last_line + line

        if line.endswith('\\'):
            is_last_break_line = True
            last_line = cur_line[:-1]
            continue

        is_last_break_line = False
        new_lines.append(cur_line)
    return new_lines


def break_lines(lines):
    """Doc."""
    new_lines = []

    in_multi_line_comment = False
    in_single_line_comment = False

    in_single_quoted_character = False
    in_double_quoted_string = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not in_multi_line_comment:
            in_single_line_comment = False
            in_single_quoted_character = False
            in_double_quoted_string = False

        text = ''
        for index, char in enumerate(line):
            in_str = (in_multi_line_comment or in_single_line_comment or
                      in_single_quoted_character or in_double_quoted_string)

            if in_str:
                text += char
                if index - 1 >= 0:
                    pre_char = line[index - 1]
                    if (char == '/' and pre_char == '*' and
                            in_multi_line_comment):
                        in_multi_line_comment = False
                        text += '\n'
                    elif (char == '\'' and pre_char != '\\' and
                            in_single_quoted_character):
                        in_single_quoted_character = False
                    elif (char == '"' and pre_char != '\\' and
                            in_double_quoted_string):
                        in_double_quoted_string = False
            else:
                if char == '/':
                    if index + 1 < len(line):
                        next_char = line[index + 1]
                        if next_char == '*':
                            in_multi_line_comment = True
                            text += '\n'
                            text += char
                        elif next_char == '/':
                            in_single_line_comment = True
                            text += char
                        else:
                            text += char
                    else:
                        text += char
                elif char == "'":
                    in_single_quoted_character = True
                    text += char
                elif char == '"':
                    in_double_quoted_string = True
                    text += char
                elif char == '#':
                    text += '\n'
                    text += char
                elif char not in none_operator_chars:
                    if char == '{' or char == '}':
                        delimeter = '\n'
                    else:
                        delimeter = ' '
                    text += (delimeter + char + delimeter)
                else:
                    text += char
        new_lines += text.split('\n')

    lines = new_lines
    new_lines = []
    for line in lines:
        if line.startswith('#'):
            line = '#' + line[1:].strip()
        new_lines.append(line)
    return new_lines


def split_line_by_str(line):
    """Doc."""
    indeces = [0]
    in_single_quoted_character = False
    in_double_quoted_string = False
    in_single_line_comment = False
    for index, char in enumerate(line):
        in_str = (in_single_quoted_character or in_double_quoted_string or
                  in_single_line_comment)
        if in_str:
            if index - 1 >= 0:
                pre_char = line[index - 1]
                if (char == '\'' and pre_char != '\\' and
                        in_single_quoted_character):
                    in_single_quoted_character = False
                    indeces.append(index + 1)
                elif (char == '"' and pre_char != '\\' and
                        in_double_quoted_string):
                    in_double_quoted_string = False
                    indeces.append(index + 1)
        else:
            if char == '\'':
                in_single_quoted_character = True
                indeces.append(index)
            elif char == '"':
                in_double_quoted_string = True
                indeces.append(index)
            elif char == '/' and index + 1 < len(line):
                next_char = line[index + 1]
                if next_char == '/':
                    in_single_line_comment = True
                    indeces.append(index)
    indeces.append(len(line))

    start_indeces = indeces[:-1]
    end_indeces = indeces[1:]
    index_pairs = zip(start_indeces, end_indeces)
    line_slices = []
    for index_pair in index_pairs:
        line_slice = line[index_pair[0]:index_pair[1]].strip()
        if line_slice:
            line_slices.append(line_slice)
    return line_slices


def split_line_to_words(line):
    """Doc."""
    words = []
    line_slices = split_line_by_str(line)
    for line_slice in line_slices:
        if not line_slice:
            continue
        if (line_slice.startswith('\'') or line_slice.startswith('"') or
                line_slice.startswith('//')):
            words.append(line_slice)
        else:
            words += line_slice.split()
    return words


def insert_semicolon_break(words_list):
    """Doc."""
    new_words_list = []
    for words in words_list:
        new_words = []
        in_for = False
        semicolon_counter = 0
        for index, word in enumerate(words):
            next_word = ''
            if index + 1 < len(words):
                next_word = words[index + 1]

            new_words.append(word)
            if not in_for:
                if word == ';' and next_word[:2] != '//':
                    new_words_list.append(new_words)
                    new_words = []
                if word == 'for':
                    in_for = True
            else:
                if word == ';':
                    semicolon_counter += 1
                if semicolon_counter == 2:
                    in_for = False
                    semicolon_counter = 0
        new_words_list.append(new_words)
    return new_words_list


def insert_right_parenthesis_break(words_list):
    """Doc."""
    new_words_list = []
    for words in words_list:
        in_condition = False
        indent_level = 0
        need_break = False
        for index, word in enumerate(words):
            if not in_condition:
                if word in ('if', 'while', 'for', 'switch'):
                    in_condition = True
                    continue
            else:
                if word == '(':
                    indent_level += 1
                elif word == ')':
                    indent_level -= 1
                    if indent_level == 0:
                        need_break = True
                        break
        if need_break:
            index = index + 1
            new_words_list.append(words[:index])
            new_words_list.append(words[index:])
        else:
            new_words_list.append(words)
    return new_words_list


def insert_else_break(words_list):
    """Doc."""
    new_words_list = []
    for words in words_list:
        if not words:
            continue
        if words[0] == 'else':
            if len(words) >= 2 and words[1].startswith('//'):
                new_words_list.append(words)
            else:
                new_words_list.append([words[0]])
                new_words_list.append(words[1:])
        else:
            new_words_list.append(words)
    return new_words_list


def insert_colon_break(words_list):
    """Doc."""
    keys = ('case', 'default', 'private', 'public', 'protect')
    new_words_list = []
    for words in words_list:
        if ':' in words and words[-1][:2] != '//' and words[0] in keys:
            index = words.index(':') + 1
            new_words_list.append(words[:index])
            new_words_list.append(words[index:])
        else:
            new_words_list.append(words)
    return new_words_list


def remove_blank_words(words_list):
    """Doc."""
    new_words_list = []
    for words in words_list:
        new_words = []
        for word in words:
            if not word:
                continue
            else:
                new_words.append(word)
        if new_words:
            new_words_list.append(new_words)
    return new_words_list


def remove_break_before_semicolon(words_list):
    """Doc."""
    new_words_list = []
    words_list = remove_blank_words(words_list)
    for index, words in enumerate(words_list):
        state = False
        if words[0] in ',;' and index - 1 >= 0:
            pre_words = words_list[index - 1]
            if not pre_words[-1].startswith('//'):
                if pre_words[-1][-1] in ')}':
                    state = True

        if state:
            pre_words = words_list[index - 1]
            pre_words += words
            new_words_list.pop()
            new_words_list.append(pre_words)
        else:
            new_words_list.append(words)
    return new_words_list


def remove_parenthesis_break(words_list):
    """Doc."""
    new_words_list = []
    parenthesis_num = 0
    new_words = []
    is_line_end = True
    for words in words_list:
        if not words:
            continue

        new_words += words
        if not words[-1].startswith('//'):
            for word in words:
                if word == '(':
                    parenthesis_num += 1
                elif word == ')':
                    parenthesis_num -= 1
            if parenthesis_num <= 0:
                is_line_end = True
            else:
                is_line_end = False
        else:
            is_line_end = True

        if is_line_end:
            new_words_list.append(new_words)
            new_words = []
    return new_words_list


def regular_chars(words):
    """Doc."""
    new_words = []
    new_word = ''

    for index, word in enumerate(words):
        pre_word = ''
        if index - 1 >= 0:
            pre_word = words[index - 1]

        if pre_word in '([!~^:' or word[0] in '[]]);,:?.^':
            new_word += word

        elif pre_word == '<':
            if words[0] == '#include' or word == '<':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif word == '=':
            if pre_word in '+-*/%<>!=&|^':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif pre_word == '+':
            if word == '+':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif pre_word == '-':
            if word == '->':
                new_word += word
            else:
                is_negtive = False
                pre_2_index = index - 2
                if pre_2_index >= 0:
                    pre_2_word = words[index - 2]
                    if pre_2_word not in (none_operator_chars + ')]'):
                        is_negtive = True
                if is_negtive:
                    new_word += word
                else:
                    new_words.append(new_word)
                    new_word = word

        elif pre_word == '>':
            if word == '>':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif pre_word == '&':
            if word == '&':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif pre_word == '|':
            if word == '|':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif word == '>':
            if words[0] == '#include':
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word

        elif word == '(':
            if pre_word in ('if', 'for', 'while', 'switch'):
                new_words.append(new_word)
                new_word = word
            elif pre_word[-1] in '+-*/%<>!=&|^':
                new_words.append(new_word)
                new_word = word
            elif words[0] == '#define' and index == 2:
                new_words.append(new_word)
                new_word = word
            else:
                new_word += word

        elif word.startswith('//'):
            new_words.append(new_word)
            new_word = '// ' + word[2:].strip()

        else:
            new_words.append(new_word)
            new_word = word
    new_words.append(new_word)
    return new_words


def regular_pp_mm(words):
    """Doc."""
    new_words = []
    new_word = ''
    for index, word in enumerate(words):
        pre_word = ''
        if index - 1 >= 0:
            pre_word = words[index - 1]

        if index == 0:
            new_word += word
        elif pre_word[-2:] in ('++', '--'):
            if word[0] in chars:
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word
        elif word[:2] in ('++', '--'):
            if pre_word[-1] in var_chars:
                new_word += word
            else:
                new_words.append(new_word)
                new_word = word
        else:
            new_words.append(new_word)
            new_word = word
    new_words.append(new_word)
    return new_words


def regular_blanks(words_list):
    """Doc."""
    new_words_list = []
    for words in words_list:
        words = regular_chars(words)
        words = regular_pp_mm(words)
        new_words_list.append(words)
    return new_words_list


def regular_none_comment_lines(lines):
    """Doc."""
    words_list = []
    for line in lines:
        words = split_line_to_words(line)
        words_list.append(words)
    words_list = insert_semicolon_break(words_list)
    words_list = insert_right_parenthesis_break(words_list)
    words_list = insert_colon_break(words_list)
    words_list = insert_else_break(words_list)
    words_list = remove_break_before_semicolon(words_list)
    words_list = regular_blanks(words_list)

    new_lines = []
    for words in words_list:
        line = ' '.join(words)
        new_lines.append(line)
    return new_lines


def split_lines_by_comment(lines):
    """Doc."""
    lines_list = []

    new_lines = []
    in_multi_line_comment = False
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not in_multi_line_comment:
            if line.startswith('/*'):
                in_multi_line_comment = True
                lines_list.append(new_lines)
                new_lines = []
            elif line.startswith('//'):
                line = '// ' + line[2:].strip()
                lines_list.append(new_lines)
                lines_list.append([line])
                new_lines = []
            else:
                new_lines.append(line)

        if in_multi_line_comment:
            new_lines.append(line)
            if line.endswith('*/'):
                in_multi_line_comment = False
                lines_list.append(new_lines)
                new_lines = []
    lines_list.append(new_lines)
    return lines_list


def regular_lines(lines):
    """Doc."""
    new_lines_list = []
    lines_list = split_lines_by_comment(lines)
    for lines in lines_list:
        if not lines:
            continue

        if not (lines[0].startswith('/*') or lines[0].startswith('//')):
            lines = regular_none_comment_lines(lines)
        new_lines_list.append(lines)
    return new_lines_list


def break_long_line(line, indent_level):
    """Doc."""
    words = split_line_to_words(line)
    level = indent_level + 1
    words_list = []
    new_words = []
    for word in words:
        new_words.append(word)
        line = ' '.join(new_words)
        if (4 * level + len(line)) > MAX_LINE_LENGTH:
            if not word.startswith('//'):
                new_words.pop()
                new_words.append('\\')
                words_list.append(new_words)
                new_words = ['\t' + word]
    words_list.append(new_words)
    lines = [' '.join(words) for words in words_list]
    lines = ['\t' * indent_level + line for line in lines]
    new_line = '\n'.join(lines)
    return new_line


def indent_lines(lines):
    """Doc."""
    new_lines = []
    indent_flags = []
    lines_list = regular_lines(lines)

    for lines in lines_list:
        if not lines:
            continue

        if lines[0].startswith('/*') or lines[0].startswith('//'):
            indent_level = len(indent_flags) - indent_flags.count('#')
            for line in lines:
                new_lines.append('\t' * indent_level + line)
            continue

        for line_index, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            no_indent_once = False
            parenthesis_indent_once = False
            macro_indent_once = False
            macro_no_indent_once = False

            line_slices = split_line_by_str(line)
            last_slice = line_slices[-1]
            if last_slice.startswith('//'):
                last_slice = line_slices[-2]

            if line.startswith('{'):
                indent_flags.append('{')
                no_indent_once = True
            elif line.endswith(':'):
                if indent_flags and ':' in indent_flags:
                    temp_flags = indent_flags[:]
                    flag = '#'
                    while(flag == '#'):
                        flag = temp_flags.pop()
                    if flag == ':':
                        index = len(temp_flags)
                        indent_flags.pop(index)
                if line_index + 1 < len(lines):
                    next_line = lines[line_index + 1]
                    if not next_line.startswith('{'):
                        indent_flags.append(':')
                        no_indent_once = True
            elif ((last_slice.endswith(')') or last_slice == 'else') and
                    not line.startswith('#')):
                parenthesis_indent_once = True
                if line_index + 1 < len(lines):
                    next_line = lines[line_index + 1]
                    if not next_line.startswith('{'):
                        no_indent_once = True
                        indent_flags.append(')')
            elif line.startswith('}'):
                if '{' in indent_flags:
                    index = indent_flags[::-1].index('{')
                    before_flags = indent_flags[::-1][index + 1:][::-1]
                    after_flags = indent_flags[::-1][:index + 1][::-1]
                else:
                    before_flags = []
                    after_flags = indent_flags
                sharp_num = after_flags.count('#')
                indent_flags = before_flags + ['#'] * sharp_num

            elif line.startswith('#if'):
                indent_flags.append('#')
                macro_indent_once = True
                macro_no_indent_once = True
            elif line.startswith('#else') or line.startswith('#elif'):
                macro_indent_once = True
                macro_no_indent_once = True
                if '#' in indent_flags:
                    index = indent_flags[::-1].index('#')
                    indent_flags = indent_flags[::-1][index:][::-1]
            elif line.startswith('#endif'):
                macro_indent_once = True
                if '#' in indent_flags:
                    index = indent_flags[::-1].index('#')
                    index = len(indent_flags) - 1 - index
                    indent_flags.pop(index)

            if macro_indent_once:
                indent_level = indent_flags.count('#')
                if macro_no_indent_once:
                    indent_level -= 1

                new_line = ''
                if line.startswith('#if'):
                    new_line += '\n'
                if (4 * indent_level + len(line)) < MAX_LINE_LENGTH:
                    new_line += '\t' * indent_level + line
                else:
                    new_line += break_long_line(line, indent_level)
                if line.startswith('#endif'):
                    new_line += '\n'
            else:
                indent_level = len(indent_flags) - indent_flags.count('#')
                if no_indent_once:
                    indent_level -= 1
                if (4 * indent_level + len(line)) < MAX_LINE_LENGTH:
                    new_line = '\t' * indent_level + line
                else:
                    new_line = break_long_line(line, indent_level)
                if line.startswith('}') and indent_flags.count('{') == 0:
                    new_line += '\n'
            new_lines.append(new_line)

            if not parenthesis_indent_once:
                if indent_flags:
                    flag = '?'
                    temp_flags = indent_flags[:]
                    while(temp_flags and flag not in '{:'):
                        flag = temp_flags.pop()

                    index = len(temp_flags)
                    if flag in '{:':
                        index += 1

                    before_flags = indent_flags[:index]
                    after_flags = indent_flags[index:]
                else:
                    before_flags = []
                    after_flags = indent_flags
                sharp_num = after_flags.count('#')
                indent_flags = before_flags + ['#'] * sharp_num
    return new_lines


def scrub_comments(lines):
    """Replace commented portions of a given source text as spaces."""
    lines = strip_back_slash(lines)

    new_lines = []
    in_multi_line_comment = False
    in_single_line_comment = False

    in_single_quoted_character = False
    in_double_quoted_string = False

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if not in_multi_line_comment:
            in_single_line_comment = False
            in_single_quoted_character = False
            in_double_quoted_string = False

        new_line = ''
        for index, char in enumerate(line):
            not_char = False
            in_str = (in_multi_line_comment or in_single_line_comment or
                      in_single_quoted_character or in_double_quoted_string)

            if in_str:
                if index - 1 >= 0:
                    pre_char = line[index - 1]
                    if (char == '/' and pre_char == '*' and
                            in_multi_line_comment):
                        in_multi_line_comment = False
                    elif (char == '\'' and pre_char != '\\' and
                            in_single_quoted_character):
                        in_single_quoted_character = False
                    elif (char == '"' and pre_char != '\\' and
                            in_double_quoted_string):
                        in_double_quoted_string = False
            else:
                if char == '/':
                    if index + 1 < len(line):
                        next_char = line[index + 1]
                        if next_char == '*':
                            in_multi_line_comment = True
                            not_char = True
                        elif next_char == '/':
                            in_single_line_comment = True
                            not_char = True
                elif char == "'":
                    in_single_quoted_character = True
                    not_char = True
                elif char == '"':
                    if not line.startswith('#include'):
                        in_double_quoted_string = True
                        not_char = True

                if not not_char:
                    if char == '{' or char == '}':
                        new_line += ('\n' + char + '\n')
                    elif char == '#':
                        new_line += ('\n' + char)
                    else:
                        new_line += char
        new_lines += new_line.split('\n')
    return new_lines


def collapse_braces(lines):
    """Doc."""
    lines = scrub_comments(lines)

    new_lines = []
    indent_flags = []
    macro_flags = []
    line_off_level = 100

    line_on = True
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line_on:
            if line.startswith('{'):
                indent_flags.append('{')
            elif line.startswith('}'):
                if '{' in indent_flags:
                    index = indent_flags[::-1].index('{')
                    index = len(indent_flags) - 1 - index
                    indent_flags.pop(index)

        if '{' not in indent_flags:
            if line.startswith('#if'):
                macro_flags.append('#')
            elif line.startswith('#else') or line.startswith('#elif'):
                if line_on:
                    line_on = False
                    line_off_level = len(macro_flags)
            elif line.startswith('#endif'):
                if len(macro_flags) == line_off_level:
                    line_on = True
                if macro_flags:
                    macro_flags.pop()
            if line_on and not (line.startswith('#if') or
                                line.startswith('#endif') or
                                line.startswith('#define')):
                new_lines.append(line)
        else:
            if line.startswith('#if'):
                indent_flags.append('#')
            elif line.startswith('#else') or line.startswith('#elif'):
                index = indent_flags[::-1].index('#')
                index = len(indent_flags) - index
                indent_flags = indent_flags[:index]
            elif line.startswith('#endif'):
                if '#' in indent_flags:
                    index = indent_flags[::-1].index('#')
                    index = len(indent_flags) - 1 - index
                    indent_flags.pop(index)

            if indent_flags.count('{') == 1 and line.startswith('{'):
                new_lines.append(line)
    return new_lines


def simplify_to_one_line(lines):
    """Doc."""
    new_lines = []
    new_line = ''
    is_line_end = False
    for line in lines:
        new_line += line
        if line.startswith('#') or line.endswith(';') or line.endswith('}'):
            is_line_end = True
        if is_line_end:
            new_lines.append(new_line)
            new_line = ''
            is_line_end = False
    if not is_line_end:
        new_lines.append(new_line)
    return new_lines


def remove_none_func_lines(lines):
    """Doc."""
    new_lines = []
    for line in lines:
        if line.startswith('#') and '.h' in line:
            new_lines.append(line)
        elif line.endswith(');') or line.endswith('}'):
            if '(' in line and ')' in line and '::' not in line:
                new_lines.append(line)
    return new_lines


def simplify_lines(lines):
    """Doc."""
    lines = break_lines(lines)
    lines = collapse_braces(lines)
    lines = regular_none_comment_lines(lines)
    lines = simplify_to_one_line(lines)
    lines = remove_none_func_lines(lines)
    return lines


def beautify_lines(lines):
    """Doc."""
    lines = strip_back_slash(lines)
    lines = break_lines(lines)
    lines = indent_lines(lines)
    return lines


def is_main_ino_file(file_path):
    """."""
    state = False
    f = CFile(file_path)
    funcs = f.list_function_definitions()
    funcs = [f.split('(')[0] for f in funcs]
    if 'void setup' in funcs and 'void loop' in funcs:
        state = True
    return state


def is_main_cpp_file(file_path):
    """."""
    state = False
    f = CFile(file_path)
    funcs = f.list_function_definitions()
    funcs = [f.split('(')[0] for f in funcs]
    if 'void main' in funcs or 'int main' in funcs:
        state = True
    return state


def get_index_of_first_statement(src_text):
    """
    Return the index of the first character.

    that's not whitespace a comment or a pre-processor directive.

    Args:
        src_text: The source code.

    Returns:
        index: The index of first statement.
    """
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


class CFile(file.File):
    """A c/c++ source file."""

    def __init__(self, file_path):
        """Initiate the source file."""
        super(CFile, self).__init__(file_path)
        self._last_mtime = 0
        self._text = self.read()
        self._lines = self._text.split('\n')
        self._beautified_lines = []
        self._simplified_lines = []

    def _is_modified(self):
        """Doc."""
        return self.get_mtime() != self._last_mtime

    def is_cpp_file(self):
        """Doc."""
        return self.get_ext() in SRC_EXTS

    def _update(self):
        """Doc."""
        self._last_mtime = self.get_mtime()
        self._text = self.read()
        self._lines = self._text.split('\n')

    def _check_modified(self):
        """Doc."""
        if self.is_cpp_file() and self._is_modified():
            self._update()

    def get_lines(self):
        """Doc."""
        self._check_modified()
        return self._lines

    def get_beautified_lines(self):
        """Doc."""
        self._check_modified()
        return self._beautified_lines

    def get_beautified_text(self):
        """Doc."""
        self._check_modified()
        if not self._beautified_lines:
            self._beautified_lines = beautify_lines(self._lines)
        beautified_text = '\n'.join(self._beautified_lines)
        beautified_text = beautified_text.replace('\n\n\n', '\n\n')
        beautified_text = beautified_text.replace('\n;', ';\n')
        return beautified_text

    def get_simplified_lines(self):
        """Doc."""
        self._check_modified()
        if not self._simplified_lines:
            self._simplified_lines = simplify_lines(self._lines)
        return self._simplified_lines

    def get_simplified_text(self):
        """Doc."""
        self._check_modified()
        if not self._simplified_lines:
            self._simplified_lines = simplify_lines(self._lines)
        return '\n'.join(self._simplified_lines)

    def list_function_declarations(self):
        """Doc."""
        self._check_modified()
        function_declarations = []
        if not self._simplified_lines:
            self._simplified_lines = simplify_lines(self._lines)
        for line in self._simplified_lines:
            if line.endswith(');'):
                function_declarations.append(line[:-1])
        return function_declarations

    def list_function_definitions(self):
        """Doc."""
        self._check_modified()
        function_definitions = []
        if not self._simplified_lines:
            self._simplified_lines = simplify_lines(self._lines)
        for line in self._simplified_lines:
            if line.endswith('{}'):
                function_definitions.append(line[:-2])
        return function_definitions

    def list_inclde_headers(self):
        """Doc."""
        self._check_modified()
        pattern_text = multi_line_comment
        pattern_text += '|' + single_line_comment

        pattern = re.compile(pattern_text, re.M | re.S)
        text = pattern.sub('', self._text)

        pattern = re.compile(include)
        headers = pattern.findall(text)
        return headers

    def get_undeclar_func_defs(self):
        """."""
        func_defs = self.list_function_definitions()
        func_declars = self.list_function_declarations()

        undeclar_func_defs = []
        for func_def in func_defs:
            if func_def not in func_declars:
                undeclar_func_defs.append(func_def)
        return undeclar_func_defs
