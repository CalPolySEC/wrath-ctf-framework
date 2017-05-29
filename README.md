WRATH CTF Framework
===================
[![Build Status](https://travis-ci.org/WhiteHatCP/wrath-ctf-framework.svg?branch=master)](https://travis-ci.org/WhiteHatCP/wrath-ctf-framework)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/DeltaHeavy/wrath-ctf-framework/master/LICENSE)

**What? Really? Another Tiny Homebrewed CTF Framework?**

This simple flask webapp takes password submission from teams, tallies score totals, and presents a leaderboard

Development Environment
-----------------------

First, you need to install Redis on your machine and start an instance running
with the command:

```
$ redis-server
```

Then set up a virtual enviornment and install the required sources:

```
$ virtualenv venv
$ source venv/bin/activate # (. venv/bin/activate.fish on fish)
$ pip install -r requirements.txt
```

To run the app:

`python run.py`

By default, this will be available at http://localhost:5000. To run on a
different port, use:

`PORT=8080 python run.py`
