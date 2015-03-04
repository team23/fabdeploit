from __future__ import absolute_import
import posixpath
import os


class CommandNotFoundException(Exception):
    pass


def select_bin(*commands, **kwargs):
    from fabric.contrib.files import exists as remote_exists

    paths = kwargs.get('paths', None)
    remote = kwargs.get('remote', True)
    if paths is None:
        paths = ('/usr/bin', '/bin',)
    elif not isinstance(paths, (list, tuple)):
        paths = [paths]
    for path in paths:
        for command in commands:
            if remote:
                command_path = posixpath.join(path, command)
                if remote_exists(command_path):
                    return command_path
            else:
                command_path = os.path.join(path, command)
                if os.path.exists(command_path):
                    return command_path
    raise CommandNotFoundException('Could not find suitable binary for %s' % ','.join(commands))


def legacy_wrap(legacy_constructor, methodname):
    def _legacy_wrap(*args, **kwargs):
        return getattr(legacy_constructor(), methodname)(*args, **kwargs)
    return _legacy_wrap
