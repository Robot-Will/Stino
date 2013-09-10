#-*- coding: utf-8 -*-
# stino/__init__.py

from . import constant
from . import fileutil
from . import language
from . import base
from . import menu
from . import syntax
from . import sketch
from . import serial
from . import serial_monitor
from . import tools
from . import serial_monitor
from . import console
from . import preprocess
from . import compiler
from . import uploader

i18n = language.Language()
arduino_info = base.ArduinoInfo()
main_menu = menu.MainMenu(i18n, arduino_info, 'Main.sublime-menu')
ardunio_syntax = syntax.Syntax(arduino_info, 'Arduino.tmLanguage')

active_serial_listener = serial.SerialListener(main_menu)
active_file = sketch.SrcFile()
output_console = console.Console('stino_log')
