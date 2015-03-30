from __future__ import absolute_import
from .base import BaseCommandUtil


class Drupal(BaseCommandUtil):
    php_commands = ('php',)
    php_ini_path = None
    drupal_path = None
    drush_path = None
    drush_download_branch = '6.x'  # used for downloading current drush from github

    def __init__(self, **kwargs):
        super(Drupal, self).__init__(**kwargs)
        if self.drupal_path is None:
            raise RuntimeError('No drupal_path specified (class or constructor)')
        if self.drush_path is None:
            raise RuntimeError('No drush_path specified (class or constructor)')

    def php_bin(self):
        return self._select_bin(*self.php_commands)

    def init(self, force=False):
        from fabric.contrib import files

        if not force and self._exists(self.drush_path):
            return

        # TODO: Should {drush_path} be deleted on force?
        #if force and self._exists(self.drush_path):
        #    self._run('rm -rf "{drush_path}"'.format(drush_path=self.drush_path))

        self._run('mkdir -p "{drush_path}"'.format(drush_path=self._abs_path(self.drush_path)))
        self._run('git clone --depth 1 --branch {branch} https://github.com/drush-ops/drush.git {drush_path}'.format(
            branch=self.drush_download_branch,
            drush_path=self._abs_path(self.drush_path),
        ))

    def drush_bin(self):
        php_bin = self.php_bin()
        drush_bin = self._path_join(self._abs_path(self.drush_path), 'drush.php')
        php_ini_path = self._abs_path(self.php_ini_path) if self.php_ini_path else None

        if php_ini_path:
            format_str = '{php_bin} -c {php_ini_path} {drush_bin} --php="{php_bin} -c {php_ini_path}"'
        else:
            format_str = '{php_bin} {drush_bin} --php="{php_bin}"'
        return format_str.format(
            php_bin=php_bin,
            drush_bin=drush_bin,
            php_ini_path=php_ini_path,
        )

    def run(self, command, *options):
        with self._cd(self._abs_path(self.drupal_path)):
            self._run("%s %s %s" % (
                self.drush_bin(),
                command,
                ' '.join([o for o in options if not o is None]),
            ))

    def cache_clear(self, _type='all'):
        self.run(
            'cache-clear',
            _type,
        )
    cc = cache_clear

    def updatedb(self):
        self.run(
            'updatedb',
        )
    updb = updatedb

    def pm_enable(self, *packages):
        self.run(
            'pm-enable',
            '--yes',
            *packages
        )
    en = pm_enable

    def pm_disable(self, *packages):
        self.run(
            'pm-disable',
            '--yes',
            *packages
        )
    dis = pm_disable

    def variable_set(self, variable_name, variable_value):
        self.run(
            'variable-set',
            variable_name,
            variable_value,
        )
    vset = variable_set

    def maintenance_enable(self):
        self.variable_set('maintenance_mode', '1')

    def maintenance_disable(self):
        self.variable_set('maintenance_mode', '0')
