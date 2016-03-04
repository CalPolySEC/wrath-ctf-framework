WRATH CTF Framework
===================

**What? Really? Another Tiny Homebrewed CTF Framework?**

This simple flask webapp takes password submission from teams, tallies score totals, and presents a leaderboard

Todo
----
* Statistics on how many have completed each challenge in each of the three modules
* Time remaining til CTF end (auto-close challenges)
* Genericize (make is plug-n-play-able for any ctf with a simple config file, json, or whatever)
* We need a Jason API

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

    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python scripts/build_db.py

And to run the app:

    python app.py

By default, this will be available at http://localhost:5000. To run on a
different port, use:

    PORT=8080 python app.py
