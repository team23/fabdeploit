# -*- coding: utf-8 -*-
import os
try:
    from shlex import quote as shell_quote
except ImportError:
    from pipes import quote as shell_quote
import fabric.api as fab
import warnings

from .base import BaseCommandUtil


class BaseUploader(BaseCommandUtil):
    '''Base class for uploads

    fabdeploit can be used to upload files using rsync, too. The uploaders follow the Git schema we use
    inside fabdeploit. An upload should only push the files to the server and then an additional release
    switch is neccessary to apply the file changes. This also implies we have multiple releases stored
    on the server.

    Core methods that subclasses must implement:
    * upload(release_id): Upload a new release and store it using this release_id
    * switch_release(release_id): Switch to the release_id

    Usa a subclass defining upload_paths like this:
    class SomethingUploader(BaseUploaderSubclass):
        upload_paths = [
            '/from/path': '/to/path',
            '/from/another/path': '/to/another/path',
        ]

        …

    Usage might look like:
    uploader.upload('something')
    enable_maintenance()
    uploader.switch_release('something')
    run_update_commands()
    disable_maintenance()
    '''

    upload_paths = []
    rsync_defaults = {
        'delete': True,
        'default_opts': '-pthrlvz',
    }

    def _ensure_path_exists(self, path):
        if not self._exists(path):
            self._run('mkdir -p "%s"' % path)

    def _rsync_upload(self, local_path, remote_path, **kwargs):
        from fabric.contrib.project import rsync_project as rsync
        import posixpath

        for key, value in self.rsync_defaults.items():
            kwargs.setdefault(key, value)
        # Make sure we have an "/" at the end, so directory sync mode is enabled
        rsync_local_path = local_path.rstrip(os.sep) + os.sep
        rsync_remote_path = remote_path.rstrip(posixpath.sep) + posixpath.sep
        rsync(local_dir=rsync_local_path, remote_dir=rsync_remote_path, **kwargs)

    def upload(self, release_id):
        raise RuntimeError('Subclass should implement this')

    def switch_release(self, release_id):
        raise RuntimeError('Subclass should implement this')


class GitUploader(BaseUploader):
    '''GitUploader

    Uploads files using rsync and then creates a commit to allow switching between the releases. The
    release_id is used to create a tag for easy release switching.'''
    git_commands = 'git'

    def git_bin(self):
        return self._select_bin(*self.git_commands)

    def _release_tag(self, release_id):
        return 'release/%s' % release_id

    def upload(self, release_id, commit_message=None):
        import datetime

        warnings.warn(
            'The GitUploader has no way to follow the normal upload schema where changes to the files are '
            'only done when calling switch_release. This means the upload already applies the changes and '
            'then reverts back to the original state. THERE MIGHT BE DRAGONS!'
        )

        if commit_message is None:
            commit_message = datetime.datetime.now().isoformat()

        # TODO: Make sure no changes are done to the file system while uploading, which is bad design ;-)
        for local_path, remote_path in self.upload_paths:
            self._ensure_path_exists(remote_path)
            git_bin = self.git_bin()

            with self._cd(remote_path):
                current_release_sha = None
                if not self._exists(self._path_join(remote_path, '.git')):
                    self._run('{git_bin} init .'.format(git_bin=git_bin))
                else:
                    current_release_sha = self._run('{git_bin} rev-parse HEAD'.format(git_bin=git_bin))
                self._run('{git_bin} checkout master'.format(git_bin=git_bin))
                self._rsync_upload(local_path, remote_path, exclude=('.git',))
                self._run('{git_bin} add -A'.format(git_bin=git_bin))
                self._run('{git_bin} ls-files --deleted -z | xargs -r -0 git rm'.format(git_bin=git_bin))
                with fab.settings(warn_only=True):
                    self._run('{git_bin} commit --allow-empty -m {commit_message}'.format(
                        git_bin=git_bin,
                        commit_message=shell_quote(commit_message),
                    ))
                self._run('{git_bin} tag {release_id}'.format(
                    git_bin=git_bin,
                    release_id=shell_quote(self._release_tag(release_id)),
                ))
                if current_release_sha:  # rollback to previous release
                    self._run('{git_bin} checkout {sha}'.format(
                        git_bin=git_bin,
                        sha=shell_quote(current_release_sha),
                    ))

    def switch_release(self, release_id):
        git_bin = self.git_bin()
        for local_path, remote_path in self.upload_paths:
            with self._cd(remote_path):
                self._run('{git_bin} checkout {sha}'.format(
                    git_bin=git_bin,
                    sha=shell_quote(self._release_tag(release_id)),
                ))


class SymLinkUploader(BaseUploader):
    '''SymLinkUploader

    Uploads the files to an distinct storage path and then updates a symlink at the original target
    location to point to the current release. release_id is used a a sub-path inside the storeage
    directory.
    '''
    upload_storage_path = None
    upload_storage_current_link = 'active'

    cp_commands = ('cp',)
    cp_args = '-al'
    rm_commands = ('rm',)
    ln_commands = ('ln',)
    ln_args = '-s'

    def cp_bin(self):
        return self._select_bin(*self.cp_commands)

    def rm_bin(self):
        return self._select_bin(*self.rm_commands)

    def ln_bin(self):
        return self._select_bin(*self.ln_commands)

    def _get_upload_release_pathname(self, release_id):
        return release_id

    def _get_upload_release_path(self, release_id):
        return self._path_join(self._abs_path(self.upload_storage_path), self._get_upload_release_pathname(release_id))

    def _get_remote_upload_pathname(self, release_id, remote_path):
        import hashlib
        import posixpath

        remote_path_hash = hashlib.md5(remote_path).hexdigest()[:6]
        return "%s-%s" % (posixpath.basename(remote_path), remote_path_hash)

    def _get_remote_upload_path(self, release_id, remote_path):
        upload_release_path = self._get_upload_release_path(release_id)
        return self._path_join(upload_release_path, self._get_remote_upload_pathname(release_id, remote_path))

    def upload(self, release_id):
        from fabric.contrib import files
        import posixpath

        upload_storage_path = self._abs_path(self.upload_storage_path)
        self._ensure_path_exists(upload_storage_path)
        upload_release_path = self._get_upload_release_path(release_id)
        self._ensure_path_exists(upload_release_path)

        upload_storage_current_link = self._path_join(upload_storage_path, self.upload_storage_current_link)

        for local_path, remote_path in self.upload_paths:
            if files.exists(remote_path) and not files.is_link(remote_path):
                raise RuntimeError('Remote path already exists, but is no symlink (%s)' % remote_path)

            remote_upload_path = self._get_remote_upload_path(release_id, remote_path)

            if self._exists(upload_storage_current_link) and not self._exists(remote_upload_path):
                remote_upload_pathname = self._get_remote_upload_pathname(release_id, remote_path)
                active_remote_upload_path = self._path_join(upload_storage_current_link, remote_upload_pathname)
                cp_active_remote_upload_path = active_remote_upload_path.rstrip(posixpath.sep) + posixpath.sep
                cp_remote_upload_path = remote_upload_path.rstrip(posixpath.sep) + posixpath.sep
                self._run('{cp_bin} {cp_args} {from_path} {to_path}'.format(
                    cp_bin=self.cp_bin(),
                    cp_args=self.cp_args,
                    from_path=shell_quote(cp_active_remote_upload_path),
                    to_path=shell_quote(cp_remote_upload_path),
                ))

            self._rsync_upload(local_path, remote_upload_path)

    def switch_release(self, release_id):
        upload_storage_path = self._abs_path(self.upload_storage_path)
        upload_storage_current_link = self._path_join(upload_storage_path, self.upload_storage_current_link)

        # make sure all symlinks are working
        for local_path, remote_path in self.upload_paths:
            remote_upload_pathname = self._get_remote_upload_pathname(release_id, remote_path)
            if self._exists(remote_path):
                self._run('{rm_bin} {path}'.format(
                    rm_bin=self.rm_bin(),
                    path=shell_quote(remote_path),
                ))
            self._run('{ln_bin} {ln_args} {current_link} {upload_path}'.format(
                ln_bin=self.ln_bin(),
                ln_args=self.ln_args,
                current_link=shell_quote(self._path_join(upload_storage_current_link, remote_upload_pathname)),
                upload_path=shell_quote(remote_path),
            ))

        # switch to current release
        if self._exists(upload_storage_current_link):
            self._run('{rm_bin} {path}'.format(
                rm_bin=self.rm_bin(),
                path=shell_quote(upload_storage_current_link),
            ))
        self._run('{ln_bin} {ln_args} {release_path} {current_link}'.format(
            ln_bin=self.ln_bin(),
            ln_args=self.ln_args,
            release_path=shell_quote(self._get_upload_release_pathname(release_id)),
            current_link=shell_quote(upload_storage_current_link),
        ))
