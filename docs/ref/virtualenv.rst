Virtualenv
==========

Options
-------

python_commands
    List/tuple of possible python commands.

pip_commands
    List/tuple of possible pip commands.

virtualenv_commands
    List/tuple of possible virtualenv commands. If not found virtualenv
    will be installed from git by init().

**virtualenv_path** (mandatory)
    Path to virtualenv on the remote server.

virtualenv_download_branch:
    Branch to install virtualenv from when no virtualenv is available
    on the server. See init().

requirements_file
    Path to the requirements file used to install()/update() the virtualenv.
    Mandatory only if these methodes are called.

**Note:** Use Virtualenv2 or Virtualenv3 to setup python_commands/pip_commands/virtualenv_commands
according to the proper python versions.

Methods
-------

init()
    Set the virtualenv up by calling virtualenv bin for virtualenv_path. If no
    virtualenv bin is available on the server it will clone the virtualenv
    github repository to setup all manually. The git clone will use to branch
    specified in virtualenv_download_branch, if you need some particular version.

install()/update()
    Updates the virtualenv according to requirements_file.

git (Property)
    Allows you to put the entiry virtualenv under git control. May be used to
    rollback the virtualenv easily. Returns VirtualenvGit instance, see code for
    more details.

python_bin()
    Returns path to virtualenv python, may be used for running own commands.

Example Workflow
----------------

.. code:: python

    virtualenv = Virtualenv(virtualenv_path="…", requirements_file="…")
    virtualenv.init()  # Make sure the virtualenv exists
    virtualenv.update()  # Apply requirements_file

    run("{python_bin} --version".format({
        "python_bin": virtualenv.python_bin()
    }))