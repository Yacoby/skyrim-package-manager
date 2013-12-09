Skryim Package Manager
======================

###Installing (Arch Linux)
Copy cfg.json.dist to cfg.json. Add the following

* The location to download the mods to. This can be any path but it must exist
* Your password and username for the Nexus sites. This isn't required but if you don't add them you can't download any file over 2mb

Install virtualenv and pip then run the following:

    $ virtualenv env
    $ source env/bin/activate
    $ pip install -r requirements.txt
    $ python server.py

Open [http://localhost:8080](http://localhost:8080) and add the nxm handler using the button

    $ ^C
    $ deactive

Downloading nxms should now work on Linux and while downloading [http://localhost:8080](http://localhost:8080) can be used to view the download progress

###Design Goals

Key:
* **Linux Support** (Windows is a bit more optional ;))
* **Minimal**, no need for GUIs etc unless there are errors
* **Fast** or at least the apearance of being fast. Downloading a small file (sub 100kb) should be faster than I can do it manually

###Roadmap:

0:
* Fix NXM support
* Auto shutdown when all downloads are finished
* Windows support (ideally some form of exe?)

1:
* Auto download depenecies
* Ability to run the app through some other means

2+:
* Version tracking
* Support for downloading new versions
* Support for changing file names
* Set login details/download location through the GUI
