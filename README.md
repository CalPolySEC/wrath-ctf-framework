iFixit CTF
==========

This simple flask webapp takes password submission from teams, tallies score totals, and presents a leaderboard

TODO
----
* Statistics on how many have completed each challenge in each of the three modules
* Time remaining

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

Heroku
------

The following environment variables are used for configuration:

* ``DATABASE_URL`` - Heroku should set this automatically
* ``PORT`` - this should also be automatic
* ``SECRET_KEY`` - something unique
* ``STATIC_PREFIX`` - empty string to serve on ``/``
