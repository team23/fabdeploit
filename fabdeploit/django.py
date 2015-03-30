from __future__ import absolute_import
import fabric.api as fab
from .base import BaseCommandUtil
from .utils import legacy_wrap
import warnings


class Django(BaseCommandUtil):
    manage_path = None

    def __init__(self, virtualenv, **kwargs):
        self.virtualenv = virtualenv
        super(Django, self).__init__(**kwargs)
        if self.manage_path is None:
            raise RuntimeError('No manage_path specified (class or constructor)')

    def run(self, command, *options):
        self._run("%s %s %s %s" % (
            self.virtualenv.python_bin(),
            self._abs_path(self.manage_path),
            command,
            ' '.join([o for o in options if not o is None]),
        ))

    def collectstatic(self, clear=False):
        self.run(
            'collectstatic',
            '--noinput',
            '-c' if clear else None,
        )

    def syncdb(self, migrate=False, database=None):
        self.run(
            'syncdb',
            '--noinput',
            '--database="%s"' % database if database else None,
            '--migrate' if migrate else None,
        )

    def migrate(self, app=None, migration=None, database=None, fake=False, merge=False):
        self.run(
            'migrate',
            '--noinput',
            '--merge' if merge else None,
            '--database="%s"' % database if database else None,
            '--fake' if fake else None,
            app if app else None,
            migration if migration else None,
        )


# BACKWARDS COMPATIBILITY


def _legacy_django():
    from .virtualenv import _legacy_virtualenv

    warnings.warn('You are using the legacy function, please switch to class based version', PendingDeprecationWarning)

    fab.require('deploy_manage_path')
    virtualenv = _legacy_virtualenv()
    return Django(virtualenv,
                  manage_path=fab.env.deploy_manage_path)


run_command = legacy_wrap(_legacy_django, 'run')
collectstatic = legacy_wrap(_legacy_django, 'collectstatic')
syncdb = legacy_wrap(_legacy_django, 'syncdb')
migrate = legacy_wrap(_legacy_django, 'migrate')
