from __future__ import absolute_import
import fabric.api as fab
from . import virtualenv


def run_command(command, *options):
    fab.require('deploy_manage_path')
    fab.run("%s %s %s %s" % (
        virtualenv._env_path(),
        fab.env.deploy_manage_path,
        command,
        ' '.join([o for o in options if not o is None]),
    ))


def collectstatic(clear=False):
    run_command(
        'collectstatic',
        '--noinput',
        '-c' if clear else None,
    )


def syncdb(migrate=False, database=None):
    run_command(
        'syncdb',
        '--noinput',
        '--database="%s"' % database if database else None,
        '--migrate' if migrate else None,
    )


def migrate(app=None, migration=None, database=None, fake=False):
    run_command(
        'migrate',
        '--noinput',
        '--database="%s"' % database if database else None,
        '--fake' if fake else None,
        app if app else None,
        migration if migration else None,
    )


