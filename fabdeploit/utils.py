from __future__ import absolute_import
import fabric.api as fab
import posixpath
import os


def _select_bin(*commands, **kwargs):
    from fabric.contrib.files import exists as remote_exists

    paths = kwargs.get('paths', None)
    remote = kwargs.get('remote', True)
    if not isinstance(commands, (list, tuple)):
        commands = [commands]
    if paths is None:
        paths = fab.env.get('deploy_bin_paths', (
            '/usr/bin',
            '/bin',
        ))
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
                if posixpath.exists(command_path):
                    return command_path
    raise RuntimeError('Could not find suitable command for %s' % '/'.join(commands))
