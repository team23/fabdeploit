from __future__ import absolute_import
import fabric.api as fab


def _git_create_release_commit(repo, commit, message=None, parents=None, actor=None):
    """ Created a new git (release) commit, by reusing an existing commit tree"""
    from time import time, altzone
    import git
    
    # create a new commit reusing the tree (meaning no file changes)
    release_commit = git.Commit(repo, git.Commit.NULL_BIN_SHA)
    release_commit.tree = commit.tree
    
    # set commit date
    unix_time = int(time())
    offset = altzone
    release_commit.authored_date = unix_time
    release_commit.author_tz_offset = offset
    # make sure we have a somewhat more linear history
    # (gitg and possibly others will get confused otherwise)
    if release_commit.authored_date == commit.authored_date:
        release_commit.authored_date = release_commit.authored_date + 1
    release_commit.committed_date = unix_time
    release_commit.committer_tz_offset = offset
    if release_commit.committed_date == commit.committed_date:
        release_commit.committed_date = release_commit.committed_date + 1
    
    # set author / comitter
    if actor:
        if isinstance(actor, basestring):
            actor = git.Actor._from_string(actor)
        release_commit.author = actor
        release_commit.committer = actor
    else:
        cr = repo.config_reader()
        release_commit.author = git.Actor.author(cr)
        release_commit.committer = git.Actor.committer(cr)
    
    # set commit message
    if message:
        release_commit.message = message
    else:
        release_commit.message = commit.message
    
    # set parents
    release_commit.parents = parents if not parents is None else []
    
    # reuse encoding
    release_commit.encoding = commit.encoding
    return release_commit


def _git_write_object(repo, obj):
    from gitdb import IStream
    import git
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    
    stream = StringIO()
    obj._serialize(stream)
    streamlen = stream.tell()
    stream.seek(0)
    istream = repo.odb.store(IStream(obj.__class__.type, streamlen, stream))
    obj.binsha = istream.binsha
    return obj


def _git_update_branch(repo, branch_name, commit):
    if not branch_name in repo.heads:
        repo.create_head(branch_name)
    repo.heads[branch_name].commit = commit


def _git_release_deployment_branch(branch_name):
    return 'release/%s' % branch_name


def pull_origin():
    import git
    fab.require(
        'deploy_git_repository',
        'deploy_release_branch')
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # update local branches
    if not 'origin' in [_i.name for _i in repo.remotes]:
        return
    # TODO: Do this using gitpython api?
    repo.git.checkout(fab.env.deploy_release_branch)
    repo.git.pull('origin', fab.env.deploy_release_branch)
    if release_deployment_branch in repo.heads:
        repo.git.checkout(release_deployment_branch)
        repo.git.pull('origin', release_deployment_branch)


def create_release(release_commit_filter=None):
    """ Creates a new release commit
    
    Creates release branch if necessary. Uses the following env variables:
    * env.deploy_git_repository: Path to the local git repository
    * env.deploy_release_branch: Branch that should be released
    * env.deploy_release_author: Author for new release commit (optional)
    * env.deploy_release_message: Message used for release commit (optional)
    * env.deploy_release_tag: Tag that should be created for release commit (optional)
    * env.deploy_merge_release_back: Normally we merge the release commit back to
            the branch it originated from. You can turn this off (on by default)
    """
    import git
    
    fab.require(
        'deploy_git_repository',
        'deploy_release_branch')
    
    # init repo, latest commit and config
    repo = git.Repo(fab.env.deploy_git_repository)
    commit = repo.heads[fab.env.deploy_release_branch].commit
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # last release commit
    parent = None
    if release_deployment_branch in repo.heads:
        parent = repo.heads[release_deployment_branch].commit
    
    # create new commit
    if 'deploy_release_author' in fab.env:
        release_actor = fab.env.deploy_release_author
    else:
        release_actor = None
    if 'deploy_release_message' in fab.env:
        message = fab.env.deploy_release_message
    else:
        message = None
    if parent:
        release_commit = _git_create_release_commit(repo, commit, message=message, parents=[parent], actor=release_actor)
    else:
        release_commit = _git_create_release_commit(repo, commit, message=message, actor=release_actor)
    
    if release_commit_filter and callable(release_commit_filter):
        # You may write a filter to change the commit after if is initially
        # created. Changes may involve changing the tree (remove, change or
        # add files) or changing the meta data (author, date, message).
        # I think this should be used for tree filters, as other data may be
        # set before even creating the commit.
        release_commit_filter(release_commit)
    
    # write commit
    _git_write_object(repo, release_commit)
    assert release_commit.binsha
    # update release branch
    _git_update_branch(repo, release_deployment_branch, release_commit)
    
    # create tag
    if 'deploy_release_tag' in fab.env and fab.env.deploy_release_tag:
        repo.create_tag(fab.env.deploy_release_tag)
    
    # merge commit back to origin branch
    if not 'deploy_merge_release_back' in fab.env or fab.env.deploy_merge_release_back:
        # We reuse the original commit here, as the release commit may be
        # changed by some filter.
        merge_commit = _git_create_release_commit(repo, commit, parents=[commit, release_commit])
        _git_write_object(repo, merge_commit)
        assert merge_commit.binsha
        _git_update_branch(repo, fab.env.deploy_release_branch, merge_commit)
        #merge_index = Index.from_tree(repo, parent, 'HEAD', 'some_branch')
    
    return release_commit


def _git_release_deployment_remote_name(branch_name):
    return 'release/%s' % branch_name


def _git_release_deployment_remote_url(repo_path):
    if repo_path[0] == '/':
        return 'ssh://%s@%s:%s%s' % (fab.env.user, fab.env.host, fab.env.port, repo_path)
    else:
        return 'ssh://%s@%s:%s/~%s/%s' % (fab.env.user, fab.env.host, fab.env.port, fab.env.user, repo_path)


def push_release(bare=False):
    """ Pushes the release branch
    
    Creates release branch if necessary. Uses the following env variables:
    * env.deploy_git_repository: Path to the local git repository
    * env.deploy_release_branch: Branch that should be released
    * env.deploy_remote_git_repository: Remote git repository path
    """
    import git
    
    # thanks to https://github.com/dbravender/gitric/blob/master/gitric/api.py
    
    fab.require(
        'deploy_git_repository',
        'deploy_release_branch',
        'deploy_remote_git_repository')
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    release_remote_name = _git_release_deployment_remote_name(fab.env.deploy_release_branch)
    release_remote_url = _git_release_deployment_remote_url(fab.env.deploy_remote_git_repository)
    
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
        fab.run('git init --bare "%s"' % fab.env.deploy_remote_git_repository)
    else:
        fab.run('git init "%s"' % fab.env.deploy_remote_git_repository)
        # silence git complaints about pushes coming in on the current branch
        # the pushes only seed the immutable object store and do not modify the
        # working copy
        fab.run('GIT_DIR="%s/.git" git config receive.denyCurrentBranch ignore' %
            fab.env.deploy_remote_git_repository)
    
    # push to remote
    repo.git.push(release_remote_name, release_deployment_branch)
    #remote.push(release_deployment_branch)


def push_origin():
    import git
    fab.require(
        'deploy_git_repository',
        'deploy_release_branch')
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # push changes
    if not 'origin' in [_i.name for _i in repo.remotes]:
        return
    repo.git.push('origin', fab.env.deploy_release_branch)
    repo.git.push('origin', release_deployment_branch)


def switch_release(commit=None, update_to_remote=None):
    fab.require(
        'deploy_release_branch',
        'deploy_remote_git_repository')
    
    # init repo and latest commit
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # checkout changes on remote
    with fab.cd(fab.env.deploy_remote_git_repository):
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

