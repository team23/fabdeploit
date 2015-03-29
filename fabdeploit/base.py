import fabric.api as fab
from .utils import select_bin
from fabric.contrib import files
import posixpath
import os


class BaseCommandUtil(object):
    def __init__(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])
            else:
                raise RuntimeError('Unknown key {key}'.format(key=key))

    def _select_bin(self, *commands, **kwargs):
        return select_bin(*commands, **kwargs)

    def _run(self, *args, **kwargs):
        fab.run(*args, **kwargs)

    def _exists(self, path):
        return files.exists(path)

    def _path_join(self, *paths):
        return posixpath.join(*paths)

    def _cd(self, path):
        return fab.cd(path)


class LocalCommandMixin(object):
    def _select_bin(self, *commands, **kwargs):
        kwargs.setdefault('remote', False)
        return super(LocalCommandMixin, self)._select_bin(*commands, **kwargs)

    def _run(self, *args, **kwargs):
        fab.local(*args, **kwargs)

    def _exists(self, path):
        return os.path.exists(path)

    def _path_join(self, *paths):
        return os.path.join(*paths)

    def _cd(self, path):
        return fab.lcd(path)
