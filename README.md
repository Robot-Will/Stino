#Stino
![Stino](http://robot-will.github.com/Stino/images/stino.png)
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

