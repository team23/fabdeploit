Django
======

Options
-------

**manage_path** (mandatory)
    Path to manage.py

**virtualenv** (Constructor only, mandatory)
    Instance of Virtualenv

Methods
-------

run()
    Run any manage.py command.

collectstatic()/syncdb()/migrate()
    Runs the appropriate manaage.py command.

Example Workflow
----------------

.. code:: python

    virtualenv = Virtualenv(virtualenv_path="…", requirements_file="…")
    django = Django(virtualenv=virtualenv, manage_path="…")

    django.collectstatic()
    django.run("some_command", "---noinput", "--someparam")