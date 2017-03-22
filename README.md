# Stino2017

Stino is a [Sublime Text](http://www.sublimetext.com) plugin that provides an [Arduino](http://arduino.cc)-like environment for editing, compiling and uploading sketches. The plugin was written by @Robot-Will in 2012-2017. If you have any ideas or suggestions, please leave messages at [Issues](https://github.com/Robot-Will/Stino/issues). Thanks.

### Current State
Stino2017 is a totally new software and it is under development, please be patient. Thanks a lot!

Currently it works for Arduino Avr Boards and still a lot of work is left to do to complete and test this plugin. I am working on Windows 10 x64 currently, however on other platforms you may encounter errors. You can press ctrl+` to open the SublimeText console and find the error messages. The error messages will help to improve this plugin.

### Requirements
[Sublime Text](http://www.sublimetext.com) 3.0 (developing under Build 3126)

![Screenshot](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/stino_menu01.jpg)

### Installation

1. Download the .zip file from [github](https://github.com/Robot-Will/Stino)

2. Open SublimeText Packages Folder

3. Unzip the .zip file and copy the unzipped folder to the SublimeText Packages Folder

![Installation](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s004.jpg)

### How to use
#### 1. Add Package and Library Index files
This software does not need the Arduino IDE and it will download everything from the internet. By default it has [Arduino Package Index File](http://downloads.arduino.cc/packages/package_index.json) and [Arduino Library Index File](http://downloads.arduino.cc/libraries/library_index.json), and you can add your index files into the list. This software will check new index files every 30 minutes by default. Some package index files' link can be found in the [Unofficial list of 3rd party boards support urls](https://github.com/arduino/Arduino/wiki/Unofficial-list-of-3rd-party-boards-support-urls) page.

![Add Indexes](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s002.jpg)

#### 2. Set the folders
This software uses 3 folders: Arduino App Folder, Sketchbook Folder and Arduino IDE folder.

Arduino App Folder is the folder where the packages folder (cores and toolchains), build folder, download folder (staging) and setting files are. By default it is ~/Arduino15 (set to {$default}).

Sketchbook Folder is folder where sketches, examples and libraries are. By default it is [Documents Folder]/Arduino (set to {$default}). You can put examples and libraries into the 'examples' and 'libraries' folders respectively.

If you want integrate SublimeText for portable use, you can set the above two folders to {$sublime}, and it will use the [Sublime Packages]/User/Stino folder.

Arduino IDE folder is where is the Arduino IDE is. This software supports the Arduino IDE, but it does not need it. You do not need to provide this folder and can leave this option blank.

![Folders](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s001.jpg)

Then you can install packages and libraries from the internet and speed up your work by choosing your platform, version and board.

![Select Board](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s003.jpg)

### License

Copyright (C) 2012-2017 Sen <robot.will.me AT gmail.com>.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
