WRATH CTF Framework
===================

[![Coverage Status](https://coveralls.io/repos/github/DeltaHeavy/wrath-ctf-framework/badge.svg?branch=master)](https://coveralls.io/github/DeltaHeavy/wrath-ctf-framework?branch=master)

**What? Really? Another Tiny Homebrewed CTF Framework?**

This simple flask webapp takes password submission from teams, tallies score totals, and presents a leaderboard

Todo
----
* Statistics on how many have completed each challenge in each of the three modules
* Generate report.html containing visualizations of difficulty, success, challenge popularity, completion speed, etc
* Time remaining til CTF end (auto-close challenges)
* Genericize (make is plug-n-play-able for any ctf with a simple config file, json, or whatever)
* Fix code inconsistencies
* Stop Snoopin
* Flag -> Fleg

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

Here's how to get a local copy up and running:

```
virtualenv venv
source venv/bin/activate # (. venv/bin/activate.fish on fish)
pip install -r requirements.txt
python scripts/build_db.py
```

And to run the app:

`python app.py`

By default, this will be available at http://localhost:5000. To run on a
different port, use:

`PORT=8080 python app.py`
