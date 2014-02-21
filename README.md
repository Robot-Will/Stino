![Stino Logo](http://robot-will.github.com/Stino/images/logo.png)
![Stino](http://robot-will.github.com/Stino/images/stino.png)

Stino is a [Sublime Text](http://www.sublimetext.com) plugin, which provides an [Arduino](http://arduino.cc)-like environement for editing, compiling and uploading sketches. The plugin was written by Robot Will in 2012-2013.

Sublime Text is a sophisticated text editor for code, markup and prose. You'll love the slick user interface, extraordinary features and amazing performance. Stino is a Sublime Text plugin, providing a menu and a command palette, which make it as easy as Arduino IDE to write code and upload it to the I/O board. The plugin was written in pure python, and it runs on Windows, Mac OS X, and Linux. A additional python libraries, [Pyserial](https://pypi.python.org/pypi/pyserial) is used in this plugin, the codes are belonging to their own authors.

## Requirements
#### 1. [Sublime Text](http://www.sublimetext.com)
Current version supports ST2 and ST3. This version is done at 09/10/2013.

#### 2. [Arduino](http://arduino.cc/en/Main/Software)
Most Arduino versions are supported.
 
#### 3. Tested OS
* Windows: Windows 8, Windows 7, Windows XP 

* Linux: Ubuntu (13), Slax (7), Arch, ReactOS and SkyOS

* Mac OS X: OSX 10.8, 10.7, Snow Leopard (10.6)

If your OS is not listed, please see this [issue](https://github.com/Robot-Will/Stino/issues/18) and leave your OS information. Thanks.

## Installation
Stino installation coulde be achieved through Sublime Text Package Control or manual installation.

#### 1. Installation through Sublime Text Package Control

1. Open [Sublime Text Package Control Installation Page](http://wbond.net/sublime_packages/package_control/installation), copy the installation command.

2. Open Sublime Text console via Ctrl+` shorcut, and paste the installation command into the console.

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

## Set Arduino Install Location
1. Click the menu `Preferences`->`Show Arduino Menu`, Arduino Menu will appear.

2. Click the menu `Arduino`->`Preferences`->`Select Arduino Folder`.

3. Select your `Arduino Application Folder` in the quick panel. This is the location where Arduino.app is installed.

4. Once you've selected the appropriate directory, you will see the message like the Step 4 in the following figure.

![Stino Select Arduino Folder](http://robot-will.github.com/Stino/images/select_arduino.png)

## Compilation and Upload
Click the menu `Arduino`->`Verify/Compile` to compile the sketch, or click `Arduino`->`Upload` to compile and upload the sketch.

![Stino Compilation](http://robot-will.github.com/Stino/images/compilation.png)

## Input Panel
When you use `New Sketch`, `New File` and `Add Extra Flags`, an input panel will appear at the bottom of the editor. Just input text and press `Enter` key, it will work.

![Stino Input](http://robot-will.github.com/Stino/images/input.png)

## Serial Monitor
Stino provides a simple serial monitor.

![Stino Serial Monitor](http://robot-will.github.com/Stino/images/serial_monitor.png)

##Settings
Stino uses global setting defaultly, i.e., all sketches use same settings. If you have different I/O boards and write codes for them at the same time, maybe you need different settings for each sketch. Click the menu `Arduino`->`Preferences`->`Global Setting` and each sketch can have their own settings.

![Stino Languages](http://robot-will.github.com/Stino/images/setting.png)

## Translations
Stino is a multi-language software and you can select your favorite language. All translations are stored in files in `language` folder. The translation files' name is the abbravation of the language according  to the [ISO standard](http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes). Currently, most of these files are generated from [Arduino Translations](http://playground.arduino.cc/Main/LanguagesIDE). As the translation files are automatically generated, the translations are not complete. You can improve the translation and make it better.

![Stino Languages](http://robot-will.github.com/Stino/images/languages.png)

## Issues
If you meet any problems, you can leave messages at [Issues](https://github.com/Robot-Will/Stino/issues).

#### Known Issues:

###### 1. Build Process

The build process is similar to [Arduino Build Process](http://arduino.cc/en/Hacking/BuildProcess). A number of things have to happen for your Arduino code to get onto the Arduino board. First, Stino performs some small transformations to make sure that the code is correct C or C++ (two common programming languages). It then gets passed to a compiler (avr-gcc), which turns the human readable code into machine readable instructions (or object files). Then, your code gets combined with (linked against), the standard Arduino libraries that provide basic functions like digitalWrite() or Serial.print(). The result is a single Intel hex file, which contains the specific bytes that need to be written to the program memory of the chip on the Arduino board. This file is then uploaded to the board: transmitted over the USB or serial connection via the bootloader already on the chip or with external programming hardware.

* Multi-file sketches

A sketch can contain multiple files with extensions of `.ino`, `.pde`, `.c`, `.cc`, `.cpp`, `.cxx` and `.h`. When your sketch is compiled, all files with extensions of are `.ino` and `.pde` concatenated together to form the "main sketch file". Files with `.c`, `.cc`, `.cpp` or `.cxx` extensions are compiled separately. To use files with a .h extension, you need to `#include` it (using "double quotes" not angle brackets).

* Transformations to the main sketch file

Stino performs a few transformations to your main sketch file (the concatenation of all the files in the sketch with extensions of `.ino` and `.pde`) before passing it to the compiler. 

First, `#include "Arduino.h"`, or for versions less than 1.0, `#include "WProgram.h"` is added to the top of your sketch. This header file (found in `<ARDUINO>/hardware/cores/<CORE>/`) includes all the defintions needed for the standard Arduino core.

Next, Stino searches for function definitions within your main sketch file and creates declarations (prototypes) for them. These are inserted after any comments or pre-processor statements (#includes or #defines), but before any other statements (including type declarations). This means that if you want to use a custom type as a function argument, you should declare it within a separate header file. Also, this generation isn't perfect: it won't create prototypes for functions that have default argument values, or which are declared within a namespace or class.

* Build process

First, Stino reads `<ARDUINO>/hardware/cores/boards.txt` and `<ARDUINO>/hardware/cores/programmers.txt` to generate all parameters according settings.

Next, Stino seraches the file `<ARDUINO>/hardware/cores/platform.txt`, which defines the compilation commands. If this file does not exist, Stino will use the file in `compilation` folder. After reading compilation commands, Stino starts compilation. 

###### 2. Add Libraries

Copy the library folder to the `<SKETCHBOOK>/libraries/` folder.

###### 3. Add Cores

Copy the core folder to the `<SKETCHBOOK>/hardware/` folder.

## License
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## About The Author
Dr. Robot Will is a chemist, not a programmer. He is in Shanghai, China, once a member of Xinchejian. He writes this plugin just for fun, meanwhile learning Python and Arduino. If you have any ideas or suggestions, please leave messages to him. He will appreciate your help.

## Website
GitHub Page (http://robot-will.github.com/Stino/)

GitHub (https://github.com/Robot-Will/Stino)
