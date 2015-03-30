from __future__ import absolute_import
from .base import BaseCommandUtil


class Magento(BaseCommandUtil):
    php_commands = ('php',)
    php_ini_path = None
    magento_path = None

    def __init__(self, **kwargs):
        super(Magento, self).__init__(**kwargs)
        if self.magento_path is None:
            raise RuntimeError('No magento_path specified (class or constructor)')

    def php_bin(self):
        return self._select_bin(*self.php_commands)

    def shell_command_bin(self, shell_command):
        php_bin = self.php_bin()
        shell_bin = self._path_join(self._abs_path(self.magento_path), 'shell', shell_command)
        php_ini_path = self._abs_path(self.php_ini_path) if self.php_ini_path else None

        if not self._exists(shell_bin):
            raise RuntimeError("%s does not exist inside Magento install (shell/)" % shell_command)

        if php_ini_path:
            format_str = '{php_bin} -c {php_ini_path} {shell_bin}'
        else:
            format_str = '{php_bin} {shell_bin}'
        return format_str.format(
            php_bin=php_bin,
            shell_bin=shell_bin,
            php_ini_path=php_ini_path,
        )

    def run(self, shell_command, *options):
        with self._cd(self._abs_path(self.magento_path)):
            self._run("%s %s" % (
                self.shell_command_bin(shell_command),
                ' '.join([o for o in options if not o is None]),
            ))

    def compiler_compile(self):
        self.run(
            'compiler.php',
            'compile',
        )

    def indexer_index(self, index_name):
        self.run(
            'indexer.php',
            '--reindex',
            index_name,
        )

    def indexer_reindexall(self):
        self.run(
            'indexer.php',
            'reindexall',
        )

    def log_clean(self, days=None):
        self.run(
            'log.php',
            'clean',
            '--days %d' % days if days else None,
        )

    def maintenance_enable(self):
        self._run('touch "%s"' % self._path_join(self._abs_path(self.magento_path), 'maintenance.flag'))

    def maintenance_disable(self):
        self._run('rm -f "%s"' % self._path_join(self._abs_path(self.magento_path), 'maintenance.flag'))
