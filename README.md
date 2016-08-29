WRATH CTF Framework
===================

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/DeltaHeavy/wrath-ctf-framework/master/LICENSE)

**What? Really? Another Tiny Homebrewed CTF Framework?**

This simple flask webapp takes password submission from teams, tallies score totals, and presents a leaderboard

Todo
----
* Statistics and visualizations of difficulty, success, challenge popularity, completion speed, etc
* Email/deliverable of the stats and visualizations at end of ctf
* Time remaining til CTF end (auto-close challenges)
* Stop Snoopin

Adding Challenges
-----------------

**We need a single JSON file which can be parsed, which sets up an entire CTF**

It needs to contain
* CTF name
* Time+date open and close
* Categories (name, challenges)
* Challenges (name, description/hint, points, prerequisites)

Development Environment
-----------------------

First, you need to install Redis on your machine and start and instance running.

Then set up a virtual enviornment and install the required sources:

```
virtualenv venv
source venv/bin/activate # (. venv/bin/activate.fish on fish)
pip install -r requirements.txt
python scripts/build_db.py
```

To run the app:

`python run.py`

By default, this will be available at http://localhost:5000. To run on a
different port, use:

`PORT=8080 python run.py`
