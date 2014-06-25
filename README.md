Installation
============

    $ git clone https://github.com/digaev/oauth2-test
    $ virtualenv env
    $ source env/bin/activate
    $ cd oauth2-test
    $ pip install -e .
    $ initialize_oauth2-test-project_db development.ini
    $ pserve development.ini --reload


Domain Settings
---------------

In file services/services.py - replace REDIRECT_URI constant according to your wishes.
