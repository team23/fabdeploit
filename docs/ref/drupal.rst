Drupal
======

**Note:** This class uses drush, drush will be installed from git by init().

Options
-------

php_commands
    List of possible PHP commands.

php_ini_path
    Optional specify your own php.ini (see php bin option "-c")

**drupal_path** (mandatory)
    Path to drupal installation.

**drush_path** (mandatory)
    Path where drush will be installed.

drush_download_branch
    Git branch to be downloaded for installation. Defauls to "6.x", this
    drush version is compatible with Drupal 6.x and 7.x.

Methods
-------

init()
    Installs drush into drush_path() by downloading from github.

run()
    Run any drush command.

cache_clear()/updatedb()/pm_enable()/pm_disable()/variable_set()
    Shorthands for some drush commands.

maintenance_enable()/maintenance_disable()
    Enable/disable maintenance mode.

drush_bin()
    Returns path or drush binary, may be used to run own scripts.

Example Workflow
----------------

.. code:: python

    drush = Django(drupal_path="…", drush_path="…")
    drush.maintenance_enable()
    drush.cache_clear()
    drush.updatedb()
    drush.run("somecommand", "param1", "param2")
    drush.maintenance_disable()