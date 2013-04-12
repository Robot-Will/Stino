![Stino Logo](http://robot-will.github.com/Stino/images/logo.png)
![Stino](http://robot-will.github.com/Stino/images/stino.png)

Stino is a [Sublime Text 2](http://www.sublimetext.com) plugin, which provides an [Arduino](http://arduino.cc)-like environement for editing, compiling and uploading sketches. The plugin was written by Robot Will in 2012-2013.

Sublime Text is a sophisticated text editor for code, markup and prose. You'll love the slick user interface, extraordinary features and amazing performance. Stino is a Sublime Text plugin, providing a menu and a command palette, which make it as easy as Arduino IDE to write code and upload it to the I/O board. The plugin was written in pure python, and it runs on Windows, Mac OS X, and Linux. Two additional python libraries, [Pyserial](https://pypi.python.org/pypi/pyserial) and [chardet](https://pypi.python.org/pypi/chardet) were used in this plugin, these codes are belonging to their own authors.

## Requirements
#### 1. [Sublime Text 2](http://www.sublimetext.com/2)
Current version does not support [Sublime Text 3](http://www.sublimetext.com/3). The next version plugin will add the support of ST3.

#### 2. [Arduino](http://arduino.cc/en/Main/Software)
Arduino versions below 0017 are not supported. Non-standard cores, like Teensy, are supported.

## Installation
Stino installation coulde be achieved through Sublime Text Package Control or manual installation.

#### 1. Installation trough Sublime Text 2 Package Control
1. Open [Sublime Text 2 Package Control Installation Page](http://wbond.net/sublime_packages/package_control/installation), copy the installation command.

2. Open Sublime Text 2 console via Ctrl+` shorcut, and paste the installation command into the console.

3. Once installation completes, you will see 'Please restart Sublime Text to finish installation'.

4. After restart of Sublime Text, click the menu `Preferences`->`Package Control`.

5. Input `package control install` and select `Package Control: Install Package`.

6. Input 'arduino' and select 'Arduino-like IDE'.

![Stino Installation](http://robot-will.github.com/Stino/images/installation.png)

#### 2. Manual Installation
1. Download [Stino](https://github.com/Robot-Will/Stino) as a zip file, and extract it.

2. Click the menu `Preferences`->`Browse Packages...`.

3. Copy the extracted Stino folder to the Packages folder.

![Stino Manual Installation](http://robot-will.github.com/Stino/images/installation02.png)

## Set Arduino Application Folder
1. Click the menu `Preferences`->`Show Arduino Menu`, Arduino Menu will appear.

2. Click the menu 'Arduino'->'Preferences'->'Select Arduino Folder'.

3. Select your Arduino Application Folder in quick panel.

4. Once the folder you select is Arduino folder, you will see the message like the Step 4 in the following figure.

![Stino Select Arduino Folder](http://robot-will.github.com/Stino/images/select_arduino.png)

## Full Menu and Command Palette
Once the Arduino Application Folder was set, a full menu will be ready for use. The Arduino menu is not always showed in menu bar. When the active file's extension is `.ino`, `.pde`, `.c`, `.cc`, `.cpp` or `.cxx`, the Arduino menu will appear. The menu provides all functionalities of Arduino IDE, including a simple Serial Monitor.

![Stino Menu & Command Palette](http://robot-will.github.com/Stino/images/menu.png)

## Compilation and Upload


![Stino Compilation](http://robot-will.github.com/Stino/images/compilation.png)


![Stino Input](http://robot-will.github.com/Stino/images/input.png)

## Serial Monitor
![Stino Serial Monitor](http://robot-will.github.com/Stino/images/serial_monitor.png)


####A Sublime Text 2 Plugin for Arduino, Version 1.2
Copyright (c) 2012-2013 Robot-Will(robot.will.me (at) gmail.com). 

## To all users
I am still working on this plugin, and if you meet some problems or have suggestions, leave messages to me.
Link: https://github.com/Robot-Will/Stino/issues

####Attention:
If you met problems, please leave detailed information to me, including OS, board, etc.. You can find the error message in ST2 output panel. Use Ctrl+` to show the panel. If the commands in Arduino menu are gray, you may find error messages under the following line:

>Reloading plugin G:\test dir\ST-1.2\Data\Packages\stino\stcommands.py

Or you run commands and no response, maybe something wrong and you can also find error messages.



## Website
GitHub Page (http://robot-will.github.com/Stino/)

GitHub (https://github.com/Robot-Will/Stino)

##License information
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

##What is Stino anyway?
Stino is a Sublime Text 2 Plugin for Arduino. With this plugin, you can use Sublime Text 2 as IDE for developing Arduino projects. This Plugin provides most functionalities of Arduino IDE by an "Arduino" menu; and since Sublime Text 2 is a powerful editor, you will get better experience during the development. The main features are listed below:

1. Editing, Compilation and Uploading as Arduino IDE.
2. Multiple Selections.
3. Hilighting Arduino keywords.
4. Auto-completing Arduino keywors.
5. Supporting all Arduino versions, Teensy(1.0-3.0).
6. Multi-languages supported.
7. Cross platform (Win/Linux/OSX).
8. Supports multiple pde/ino/c++/c files per sketch.
9. Compiles projects that contains multiple pde/ino/c++/c sources in the correct order.
10. Fast compilation.
11. Supports additional non-arduino cores.
12. Reports SRAM size after compilation.

##Installation
1. Dowload the plugin form the website.
2. Extract the __Stino__ folder and put it into Sublime Text 2 __packages directory__ . You can access the packages directory from the Sublime Text 2 menu ( __Preferences | Browse Packages...__ )

##How to use this plugin?
1. The Arduino Menu can be activated automatically or manually. If the file ypu are editting with a extention name of '.ino', the menu will appear. Or use __Preferences | Show Arduino Menu...__ to show the menu.
2. Selecting the __Arduino directory__.
3. Editing your __Arduino Sketch__.
4. Selecting board, processor, serial port and programmer if needed.
5. Compilating or uploading your sketch.

##Translation
In the __language__ directory, there are translation files. Currently, all these files are generated from Arduino Translations (http://playground.arduino.cc/Main/LanguagesIDE). The translation files' name is the abbravation of the language according  to the ISO standard (http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Each file contains a line started with "LANG =", and the Plugin will look for this line to generate language list. As the translation files are automatically generated, the translations are not complete. If you want to make the tranlation better, you can revise the translations and email the file to me or pull request to me.

