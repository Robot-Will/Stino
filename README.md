# Stino2017

Stino is a [Sublime Text](http://www.sublimetext.com) plugin that provides an [Arduino](http://arduino.cc)-like environement for editing, compiling and uploading sketches. The plugin was written by @Robot-Will in 2012-2017. If you have any ideas or suggestions, please leave messages at [Issues](https://github.com/Robot-Will/Stino/issues). Thanks.

### Current State
Stino2017 is a totally new software and it is under developing, please be patient. Thanks a lot!

Currently it works for Arduino Avr Boards, and still a lot of works to do to complete and test this plugin. I am working on Windows 10 x64 currently, and maybe on other platforms it will encounter many errors. You can press ctrl+` to open SublimeText console and find the error messages. The error messages will help to improve this plugin.

### Requirements
[Sublime Text](http://www.sublimetext.com) 3.0 (developing under Build 3126)

![Screenshot](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/stino_menu01.jpg)

### Installation

1. Download the .zip file from [github](https://github.com/Robot-Will/Stino)

2. Open SublimeText Packages Folder

3. Unzip the .zip file and copy the unzipped folder to the SublimeText Packages Folder

![Installation](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s004.jpg)

### How to use
#### 1. Add Package and Librarie Index files
This software do not need Arduino IDE, and it will download everything from internet. Defaultly it has [Arduino Package Index File](http://downloads.arduino.cc/packages/package_index.json) and [Arduino Library Index File](http://downloads.arduino.cc/libraries/library_index.json), and you can add your index files into the list. This software will check new index files every 30 minutes defaultly.

![Add Indexes](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s002.jpg)

#### 2. Set the folders
This software uses 3 folders: Arduino App Foleder, Sketchbook Folder and Arduino IDE folder.

Arduino App Folder is the folder where the packages folder(cores and toolchains), build folder, download folder(staging) and setting files are. Defaultly it is ~/Arduino15 (set to {$default}).

Sketchbook Folder is folder where sketches, examples and libraries are. Defaultly it is [Documents Folder]/Arduino (set to {$default}). You can put examples and libraries into the 'examples' and 'libraries' folders respectively.

If you want integrate SublimeText for portable use, you can set above two folders to {$sublime}, and it will use the [Sublime Packages]/User/Stino folder.

Arduino IDE folder is where is Arduino IDE is. This software supports Arduino IDE, but it do not need it. You can leave blank of this folder.

![Folders](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s001.jpg)

Then you can install packages and libraries from internet. And choose the platform, version and board, speed up your work.

![Select Board](https://github.com/Robot-Will/Stino/blob/Wiki-Images/images/s003.jpg)

### License

Copyright (C) 2012-2017 Sen <robot.will.me AT gmail.com>.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
