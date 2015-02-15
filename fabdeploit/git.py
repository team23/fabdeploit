from __future__ import absolute_import
import warnings
import fabric.api as fab
import datetime
import os
from time import time, altzone
from .base import BaseCommandUtil
from .utils import legacy_wrap
import git


class Git(BaseCommandUtil):
    local_repository_path = None
    remote_repository_path = None
    release_author = None
    release_branch = None

    def __init__(self, **kwargs):
        super(Git, self).__init__(**kwargs)
        self.base_commit = None
        self.release_commit = None
        if self.local_repository_path is None:
            raise RuntimeError('No local_repository_path specified (class or constructor)')
        if self.remote_repository_path is None:
            raise RuntimeError('No remote_repository_path specified (class or constructor)')
        if self.release_branch is None:
            raise RuntimeError('No release_branch specified (class or constructor)')
        self.local_repository_path = os.path.realpath(os.path.abspath(self.local_repository_path))

    def _get_local_repo(self):
        try:
            return self._local_repo
        except AttributeError:
            self._local_repo = git.Repo(self.local_repository_path)
            return self._local_repo

    def _raw_copy_commit(self, commit, message=None, parents=None, actor=None):
        # create a new commit reusing the tree (meaning no file changes)
        new_commit = git.Commit(self._get_local_repo(), git.Commit.NULL_BIN_SHA)
        new_commit.tree = commit.tree

        # set commit date
        unix_time = int(time())
        offset = altzone
        new_commit.authored_date = unix_time
        new_commit.author_tz_offset = offset
        # make sure we have a somewhat more linear history
        # (gitg and possibly others will get confused otherwise)
        if new_commit.authored_date == commit.authored_date:
            new_commit.authored_date = new_commit.authored_date + 1
        new_commit.committed_date = unix_time
        new_commit.committer_tz_offset = offset
        if new_commit.committed_date == commit.committed_date:
            new_commit.committed_date = new_commit.committed_date + 1

        # set author / comitter
        if actor:
            if isinstance(actor, basestring):
                actor = git.Actor._from_string(actor)
            new_commit.author = actor
            new_commit.committer = actor
        else:
            cr = self._get_local_repo().config_reader()
            new_commit.author = git.Actor.author(cr)
            new_commit.committer = git.Actor.committer(cr)

        # set commit message
        if message:
            new_commit.message = message
        else:
            new_commit.message = commit.message

        # set parents
        new_commit.parents = parents if not parents is None else []

        # reuse encoding
        new_commit.encoding = commit.encoding
        return new_commit

    def _raw_write_object(self, obj):
        from gitdb import IStream
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO

        stream = StringIO()
        obj._serialize(stream)
        streamlen = stream.tell()
        stream.seek(0)
        istream = self._get_local_repo().odb.store(IStream(obj.__class__.type, streamlen, stream))
        obj.binsha = istream.binsha
        return obj

    def _raw_update_branch(self, branch_name, commit):
        repo = self._get_local_repo()
        if not branch_name in repo.heads:
            repo.create_head(branch_name)
        repo.heads[branch_name].commit = commit

    def release_deployment_branch(self):
        return 'release/{release_branch}'.format(release_branch=self.release_branch)

    def release_deployment_remote_name(self):
        return self.release_deployment_branch()

    def pull_origin(self):
        # init repo and config
        repo = self._get_local_repo()
        release_deployment_branch = self.release_deployment_branch()

        # update local branches
        if not 'origin' in [_i.name for _i in repo.remotes]:
            raise RuntimeError('No origin exists in remotes')

        with fab.lcd(self.local_repository_path):
            fab.local('git checkout "{branch}"'.format(branch=self.release_branch))
            fab.local('git pull origin "{branch}"'.format(branch=self.release_branch))
            if release_deployment_branch in repo.heads or \
                    ('origin' in [_i.name for _i in repo.remotes] and
                             release_deployment_branch in repo.remotes.origin.refs):
                fab.local('git checkout "{branch}"'.format(branch=release_deployment_branch))
                with fab.settings(warn_only=True):
                    fab.local('git pull origin "{branch}"'.format(branch=release_deployment_branch))

    def pull(self):
        if 'origin' in [_i.name for _i in self._get_local_repo().remotes]:
            self.pull_origin()

    def create_release_commit(self, message=None):
        """ Creates a new release commit """

        # init repo, latest commit and config
        repo = self._get_local_repo()
        commit = repo.heads[self.release_branch].commit
        self.base_commit = commit  # may be used later again
        release_deployment_branch = self.release_deployment_branch()

        # last release commit
        parent = None
        if release_deployment_branch in repo.heads:
            parent = repo.heads[release_deployment_branch].commit

        # create new commit
        if message is None:
            message = datetime.datetime.now().isoformat()
        if parent:
            self.release_commit = self._raw_copy_commit(commit, message=message, parents=[parent], actor=self.release_author)
        else:
            self.release_commit = self._raw_copy_commit(commit, message=message, actor=self.release_author)

        self.filter_release_commit()

        # write commit
        self._raw_write_object(self.release_commit)
        assert self.release_commit.binsha
        # update release branch
        self._raw_update_branch(release_deployment_branch, self.release_commit)

        return self.release_commit

    def filter_release_commit(self):
        # You may write a filter to change the commit after if is initially
        # created. Changes may involve changing the tree (remove, change or
        # add files) or changing the meta data (author, date, message).
        # I think this only should be used for tree filters, as other data may be
        # set before even creating the commit.
        pass

    def tag_release(self, tag_name):
        if self.release_commit is None:
            raise RuntimeError('You should create a release commit first')
        self._get_local_repo().create_tag(tag_name, ref=self.release_commit.hexsha1)

    def merge_release_back(self):
        # We reuse the original commit here, as the release commit may be
        # changed by some filter.
        if self.base_commit is None or self.release_commit is None:
            raise RuntimeError('You should create a release commit first')
        merge_commit = self._raw_copy_commit(self.base_commit, parents=[self.base_commit, self.release_commit])
        self._raw_write_object(merge_commit)
        assert merge_commit.binsha
        self._raw_update_branch(self.release_branch, merge_commit)
        #merge_index = Index.from_tree(repo, parent, 'HEAD', 'some_branch')

    def release(self, message=None, tag_name=None, merge_back=False):
        self.create_release_commit(message=message)
        if tag_name:
            self.tag_release(tag_name)
        if merge_back:
            self.merge_release_back()
        return self.release_commit

    def remote_deployment_repository_url(self):
        if self.remote_repository_path[0] == '/':
            return 'ssh://%s@%s:%s%s' % (fab.env.user, fab.env.host, fab.env.port, self.remote_repository_path)
        else:
            return 'ssh://%s@%s:%s/~%s/%s' % (fab.env.user, fab.env.host, fab.env.port, fab.env.user, self.remote_repository_path)

    def push_release(self, bare=False):
        """ Pushes the release branch """
        # thanks to https://github.com/dbravender/gitric/blob/master/gitric/api.py

        # init repo and config
        repo = self._get_local_repo()
        release_deployment_branch = self.release_deployment_branch()
        release_remote_name = self.release_deployment_remote_name()
        release_remote_url = self.remote_deployment_repository_url()

        # initialize remote
        if not release_remote_name in [_i.name for _i in repo.remotes]:
            remote = repo.create_remote(release_remote_name, release_remote_url)
        else:
            remote = repo.remotes[release_remote_name]
            if remote.url != release_remote_url:
                repo.delete_remote(release_remote_name)
                remote = repo.create_remote(release_remote_name, release_remote_url)

        # initialize the remote repository (idempotent)
        if bare:
            fab.run('git init --bare "%s"' % self.remote_repository_path)
        else:
            fab.run('git init "%s"' % self.remote_repository_path)
            # silence git complaints about pushes coming in on the current branch
            # the pushes only seed the immutable object store and do not modify the
            # working copy
            fab.run('GIT_DIR="%s/.git" git config receive.denyCurrentBranch ignore' %
                    self.remote_repository_path)

        # push to remote
        with fab.lcd(self.local_repository_path):
            fab.local('git push "{remote}" "{branch}"'.format(
                remote=release_remote_name,
                branch=release_deployment_branch,
            ))
        #remote.push(release_deployment_branch)

    def push_origin(self):
        # init repo and config
        repo = self._get_local_repo()

        # push changes
        if not 'origin' in [_i.name for _i in repo.remotes]:
            return
        with fab.lcd(self.local_repository_path):
            fab.local('git push origin "{branch}"'.format(branch=self.release_branch))
            fab.local('git push origin "{branch}"'.format(branch=self.release_deployment_branch()))

    def push(self):
        if 'origin' in [_i.name for _i in self._get_local_repo().remotes]:
            self.push_origin()
        self.push_release()

    def switch_release(self, commit=None, update_to_remote=None):
        # init repo and latest commit
        release_deployment_branch = self.release_deployment_branch()

        # checkout changes on remote
        with fab.cd(self.remote_repository_path):
            # we switch to the appropriate commit using a normal checkout, this
            # way git "knowns" where we are going. Afterwards we reset the working
            # to this version, cleaning possible changes.
            # if we would just reset the working copy (like gitric does) we would
            # get a funny state in git. git then resets the branch-pointer to this
            # revision, meaning git would think we have fallen back behind the
            # origin some revisions. If we switch branch when doing the reset we
            # get a diverged warning, because git still thinks our commit belongs
            # to the original branch.
            # so we use checkout (detached head) as this covers the actual stage
            # much better. git now knows we want to fall back to an old revision
            # and thus does not mix up branch information.
            # anyways we do an reset before checkout so the working directory is
            # clean.
            with fab.settings(warn_only=True):
                # may fail on initial push
                fab.run('git reset --hard')
            if update_to_remote:
                # THIS IS NOT HOW FABDEPLOIT IS INTENDED TO BE USED
                # If we have pulled the changes (which gitdeploit does not do by
                # default) and switch back to the branch (not a particular release
                # commit) we may have a edge case. The branch may have fallen
                # behind the remote branch while we stayed at headless commit
                # checkouts. This means switching directly to the branch would
                # revert a lot of changes, pulling them back in afterwards and
                # by this doing a lot of IO while risking some funny state (and
                # perhaps even conflicts?).
                # So if users want to pull changes and switch back to the branch
                # after some time we need to first reset the (local) branch to the
                # current remote version.
                # If you pass update_to_remote (meaning update_to_remote="origin")
                # switch_release() will do that for you by first comparing the
                # sha1 of the branch to the current HEAD. If both differ we are
                # most probably in headless mode and should update the (local)
                # branch. This is done by calling an update-ref to the remote
                # branch. Afterwards the normal checkout.
                # IF YOU USE THIS YOU HAVE TO FETCH FIRST (SOMEWHERE ELSE)
                # ANYWAYS AGAIN, THIS IS NOT HOW FABDEPLOIT IS INTENDED TO BE USED
                if commit is None or commit == release_deployment_branch:
                    head_rev = fab.run('git rev-parse HEAD')
                    # not done here, but should look like this
                    #fab.run('git fetch "%s"' % update_to_remote)
                    # switch to headless or make sure we are in headless mode
                    fab.run('git checkout "%s"' % head_rev)
                    # update branch pointer
                    fab.run('git update-ref "refs/heads/%s" "refs/remotes/%s/%s"' % (
                        release_deployment_branch,
                        update_to_remote,
                        release_deployment_branch,
                    ))
                    # switch to updated branch
                    fab.run('git checkout "%s"' % release_deployment_branch)
            else:
                fab.run('git checkout "%s"' % (commit if commit else release_deployment_branch))
            # make sure everything is clean
            fab.run('git reset --hard')


# BACKWARDS COMPATIBILITY


def _legacy_git(git_class=Git):
    warnings.warn('You are using the legacy function, please switch to class based version', PendingDeprecationWarning)

    fab.require('deploy_git_repository', 'deploy_release_branch', 'deploy_remote_git_repository')
    return git_class(
        local_repository_path=fab.env.deploy_git_repository,
        remote_repository_path=fab.env.deploy_remote_git_repository,
        release_branch=fab.env.deploy_release_branch,
        release_author=fab.env.get('deploy_release_author', None),
    )


def create_release(release_commit_filter=None):
    if release_commit_filter and callable(release_commit_filter):
        class FilteredGit(Git):
            def filter_release_commit(self):
                release_commit_filter(self.release_commit)
        git = _legacy_git(FilteredGit)
    else:
        git = _legacy_git()

    return git.release(
        message=fab.env.get('deploy_release_message', None),
        tag_name=fab.env.get('deploy_release_tag', None),
        merge_back=fab.env.get('deploy_merge_release_back', False),
    )


pull_origin = legacy_wrap(_legacy_git, 'pull_origin')
push_release = legacy_wrap(_legacy_git, 'push_release')
push_origin = legacy_wrap(_legacy_git, 'push_origin')
switch_release = legacy_wrap(_legacy_git, 'switch_release')
