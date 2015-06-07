Magento
=======

Options
-------

php_commands
    List of possible PHP commands.

php_ini_path
    Optional specify your own php.ini (see php bin option "-c")

**magento_path**
    Path to magento installtion.

Methods
-------

run()
    Run any shell command (see magento shell/ path).

compiler_compile()/indexer_index()/indexer_reindexall()/log_clean()
    Shorthands for some shell commands.

maintenance_enable()/maintenance_disable()
    Enable/disable maintenance mode.

shell_command_bin()
    Return base command for additional (/own) shell commands.

Example Workflow
----------------

.. code:: python

    magento = Magento(magento_path="…")
    magento.maintenance_enable()
    magento.log_clean()
    magento.run("clear_cache.php")
    magento.run("apply_migrations.php")
    magento.maintenance_disable()