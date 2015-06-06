from __future__ import absolute_import
import datetime
import warnings
import fabric.api as fab
from .base import BaseCommandUtil
from .utils import CommandNotFoundException, legacy_wrap


# IDEA:
# Initialize a virtualenv using some REQUIREMENTS file. Then initialize a
# git repository in it. Create tags for every release made using
# "release/$COMMIT_SHA1" as tag name. This way we can revert to old versions
# inside the virtualenv as well.


class Virtualenv(BaseCommandUtil):
    python_commands = ('python', 'python.exe',)
    pip_commands = ('pip',)
    virtualenv_commands = ('virtualenv',)
    virtualenv_path = None
    virtualenv_download_branch = 'master'  # used for downloading current virtualenv from github
    requirements_file = None

    def __init__(self, **kwargs):
        super(Virtualenv, self).__init__(**kwargs)
        if self.virtualenv_path is None:
            raise RuntimeError('No virtualenv_path specified (class or constructor)')

    def select_bin(self, *commands):
        return self._select_bin(*commands, paths=[
            self._path_join(self._abs_path(self.virtualenv_path), 'bin'),  # UNIX
            self._path_join(self._abs_path(self.virtualenv_path), 'Scripts'),  # Windows
        ])

    def python_bin(self):
        return self.select_bin(*self.python_commands)

    def pip_bin(self):
        return self.select_bin(*self.pip_commands)

    def virtalenv_bin(self):
        return self._select_bin(*self.virtualenv_commands)  # global search, NOT self.select_bin as virtualenv does not exist yet

    def init(self, force=False):
        if not force and self._exists(self._abs_path(self.virtualenv_path)):
            return

        try:
            virtualenv_bin = self.virtalenv_bin()
        except CommandNotFoundException:
            download_path = self._path_join(self._abs_path(self.virtualenv_path), 'download')
            download_virtualenv_path = self._path_join(download_path, 'virtualenv')
            download_virtualenv_bin = self._path_join(download_virtualenv_path, 'virtualenv.py')
            self._run('mkdir -p "{download_path}"'.format(download_path=download_path))
            self._run('git clone --depth 1 --branch {branch} https://github.com/pypa/virtualenv.git {clone_path}'.format(
                # git_bin=select_bin('git'),
                branch=self.virtualenv_download_branch,
                clone_path=download_virtualenv_path,
            ))
            virtualenv_bin = '{python_bin} "{virtualenv_download}"'.format(
                python_bin=self._select_bin(*self.python_commands),  # global search, NOT self.select_bin as virtualenv does not exist yet
                virtualenv_download=download_virtualenv_bin,
            )

        self._run('{virtualenv_bin} --clear --no-site-packages "{virtualenv_path}"'.format(
            virtualenv_bin=virtualenv_bin,
            virtualenv_path=self.virtualenv_path,
        ))

    def install(self):
        self.update()

    def update(self):
        if self.requirements_file is None:
            raise RuntimeError('No requirements_file specified (class or constructor)')

        self._run('{pip_bin} install -Ur "{requirements_file}"'.format(
            pip_bin=self.pip_bin(),
            requirements_file=self._abs_path(self.requirements_file),
        ))

    @property
    def git(self):
        return VirtualenvGit(self)


class Virtualenv2(Virtualenv):
    python_commands = ('python2', 'python', 'python2.exe', 'python.exe',)
    pip_commands = ('pip2', 'pip',)
    virtualenv_commands = ('virtualenv2', 'virtualenv',)


class Virtualenv3(Virtualenv):
    python_commands = ('python3', 'python', 'python3.exe', 'python.exe',)
    pip_commands = ('pip3', 'pip',)
    virtualenv_commands = ('virtualenv3', 'virtualenv',)


class VirtualenvGit(object):
    def __init__(self, virtualenv, **kwargs):
        self.virtualenv = virtualenv

    def commit(self, message=None, tag=None):
        if message is None:
            message = datetime.datetime.now().isoformat()
        with self.virtualenv._cd(self.virtualenv._abs_path(self.virtualenv.virtualenv_path)):
            # (re) initialize
            self.virtualenv._run('git init')
            # TODO: Make sure this is done right:
            ## switch back to latest commit
            #fab.run('git checkout master')
            # addremove everything
            self.virtualenv._run('git add -A')
            self.virtualenv._run('git ls-files --deleted -z | xargs -r -0 git rm')
            # create commit (may fail if no changes happened)
            with fab.settings(warn_only=True):
                self.virtualenv._run('git commit --allow-empty -m "%s"' % message)
            # create tag if wanted
            if tag:
                self.virtualenv._run('git tag "%s"' % tag)

    def switch_commit(self, commit):
        with self.virtualenv._cd(self.virtualenv._abs_path(self.virtualenv.virtualenv_path)):
            # see git.py on why we do checkout + reset
            self.virtualenv._run('git checkout "%s"' % commit)
            self.virtualenv._run('git reset --hard')


# BACKWARDS COMPATIBILITY


def _legacy_virtualenv():
    fab.require('deploy_env_path', 'deploy_env_requirements')

    warnings.warn('You are using the legacy function, please switch to class based version', PendingDeprecationWarning)

    return Virtualenv2(virtualenv_path=fab.env.deploy_env_path,
                      requirements_file=fab.env.deploy_env_requirements)


def _legacy_virtualenv_git():

    warnings.warn('You are using the legacy function, please switch to class based version', PendingDeprecationWarning)

    return VirtualenvGit(_legacy_virtualenv())


_env_bin = legacy_wrap(_legacy_virtualenv, 'select_bin')
create_commit = legacy_wrap(_legacy_virtualenv_git, 'commit')
init = legacy_wrap(_legacy_virtualenv, 'init')
update = legacy_wrap(_legacy_virtualenv, 'update')
switch_release = legacy_wrap(_legacy_virtualenv_git, 'switch_commit')
