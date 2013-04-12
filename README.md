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

6. Input `arduino` and select `Arduino-like IDE`.

![Stino Installation](http://robot-will.github.com/Stino/images/installation.png)

#### 2. Manual Installation
1. Download [Stino](https://github.com/Robot-Will/Stino) as a zip file, and extract it.

2. Click the menu `Preferences`->`Browse Packages...`.

3. Copy the extracted Stino folder to the Packages folder.

![Stino Manual Installation](http://robot-will.github.com/Stino/images/installation02.png)

## Set Arduino Application Folder
1. Click the menu `Preferences`->`Show Arduino Menu`, Arduino Menu will appear.

2. Click the menu `Arduino`->`Preferences`->`Select Arduino Folder`.

3. Select your Arduino Application Folder in the quick panel.

4. Once the folder you select is Arduino folder, you will see the message like the Step 4 in the following figure.

![Stino Select Arduino Folder](http://robot-will.github.com/Stino/images/select_arduino.png)

## Full Menu and Command Palette
Once the Arduino Application Folder was set, a full menu will be ready for use. The Arduino menu is not always shown in menu bar. When the active file's extension is `.ino`, `.pde`, `.c`, `.cc`, `.cpp` or `.cxx`, the Arduino menu will appear. The menu provides all functionalities of Arduino IDE, including a simple Serial Monitor.

![Stino Menu & Command Palette](http://robot-will.github.com/Stino/images/menu.png)

## Compilation and Upload
Click the menu `Arduino`->`Verify/Compile` to compile the sketch, or click `Arduino`->`Upload` to compile and upload the sketch.

![Stino Compilation](http://robot-will.github.com/Stino/images/compilation.png)

## Input Panel
When you use `New Sketch`, `New File` and `Add Extra Flags`, an input panel will appear at the bottom of the editor. Just input text and press `Enter` key, it will work.

![Stino Input](http://robot-will.github.com/Stino/images/input.png)

## Serial Monitor
Stino provides a simple serial monitor.

![Stino Serial Monitor](http://robot-will.github.com/Stino/images/serial_monitor.png)

##Translations
In the __language__ directory, there are translation files. Currently, all these files are generated from Arduino Translations (http://playground.arduino.cc/Main/LanguagesIDE). The translation files' name is the abbravation of the language according  to the ISO standard (http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Each file contains a line started with "LANG =", and the Plugin will look for this line to generate language list. As the translation files are automatically generated, the translations are not complete. If you want to make the tranlation better, you can revise the translations and email the file to me or pull request to me.

##License information
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Website
GitHub Page (http://robot-will.github.com/Stino/)

GitHub (https://github.com/Robot-Will/Stino)
