Skryim Package Manager
======================

###Installing (Arch Linux)
Install virtualenv and pip then run the following:

    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt
    $ python main.py

Use the button to set the NXM handler ect, When finished you can exit the virtual environment using (or just close the terminal):

    $ deactive

Downloading nxms should now work on Linux and while downloading [http://localhost:8080](http://localhost:8080) can be used to view the download progress

###Design Goals

Key:
* **Linux Support** (Windows is a bit more optional ;))
* **Minimal**, no need for GUIs etc unless there are errors
* **Fast** or at least the apearance of being fast. Downloading a small file (sub 100kb) should be faster than I can do it manually

###Roadmap:

0:
* Windows binary

1:
* Auto download depenecies
* Setting config options from the GUI

2+:
* Version tracking
* Support for downloading new versions
* Support for changing file names
* Set login details/download location through the GUI
