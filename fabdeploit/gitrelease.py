import git
import fabric.api as fab


def _git_create_release_commit(repo, commit, message=None, parents=None, actor=None):
    """ Created a new git (release) commit, by reusing an existing commit tree"""
    from time import time, altzone
    
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


def _git_write_commit(repo, commit):
    from gitdb import IStream
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    
    stream = StringIO()
    commit._serialize(stream)
    streamlen = stream.tell()
    stream.seek(0)
    istream = repo.odb.store(IStream(git.Commit.type, streamlen, stream))
    commit.binsha = istream.binsha
    return commit


def _git_update_branch(repo, branch_name, commit):
    if not branch_name in repo.heads:
        repo.create_head(branch_name)
    repo.heads[branch_name].commit = commit


def _git_release_deployment_branch(branch_name):
    return 'release/%s' % branch_name


def git_update_local():
    assert 'deploy_git_repository' in fab.env
    assert 'deploy_release_branch' in fab.env
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # update local branches
    if not 'origin' in [_i.name for _i in repo.remotes]:
        return
    # TODO: Do this using gitpython api?
    repo.git.checkout(fab.env.deploy_release_branch)
    repo.git.pull('origin')
    if release_deployment_branch in repo.heads:
        repo.git.checkout(release_deployment_branch)
        repo.git.pull('origin')


def git_create_release():
    """ Creates a new release commit
    
    Creates release branch if necessary. Uses the following env variables:
    * env.deploy_git_repository: Path to the local git repository
    * env.deploy_release_branch: Branch that should be released
    * env.deploy_release_author: Author for new release commit (optional)
    * env.deploy_release_message: Message used for release commit (optional)
    * env.deploy_release_tag: Tag that should be created for release commit (optional)
    * env.deploy_merge_release_back: Normally we merge the release commit back to
            the branch it originated from. You can turn this of (on by default)
    """
    
    assert 'deploy_git_repository' in fab.env
    assert 'deploy_release_branch' in fab.env
    
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
    
    # write commit
    _git_write_commit(repo, release_commit)
    assert release_commit.binsha
    # update release branch
    _git_update_branch(repo, release_deployment_branch, release_commit)
    
    # create tag
    if 'deploy_release_tag' in fab.env and fab.env.deploy_release_tag:
        repo.create_tag(fab.env.deploy_release_tag)
    
    # merge commit back to origin branch
    if not 'deploy_merge_release_back' in fab.env or fab.env.deploy_merge_release_back:
        merge_commit = _git_create_release_commit(repo, release_commit, parents=[commit, release_commit])
        _git_write_commit(repo, merge_commit)
        assert merge_commit.binsha
        _git_update_branch(repo, fab.env.deploy_release_branch, merge_commit)
        #merge_index = Index.from_tree(repo, parent, 'HEAD', 'some_branch')
    
    return release_commit


def _git_release_deployment_remote_name(branch_name):
    return 'release_%s' % branch_name


def _git_release_deployment_remote_url(repo_path):
    if repo_path[0] == '/':
        return 'ssh://%s@%s:%s%s' % (fab.env.user, fab.env.host, fab.env.port, repo_path)
    else:
        return 'ssh://%s@%s:%s/~%s/%s' % (fab.env.user, fab.env.host, fab.env.port, fab.env.user, repo_path)


def git_push_release():
    """ Pushes the release branch
    
    Creates release branch if necessary. Uses the following env variables:
    * env.deploy_git_repository: Path to the local git repository
    * env.deploy_release_branch: Branch that should be released
    * env.deploy_remote_path: Remote git repository
    """
    
    # thanks to https://github.com/dbravender/gitric/blob/master/gitric/api.py
    
    assert 'deploy_git_repository' in fab.env
    assert 'deploy_release_branch' in fab.env
    assert 'deploy_remote_path' in fab.env
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    release_remote_name = _git_release_deployment_remote_name(fab.env.deploy_release_branch)
    release_remote_url = _git_release_deployment_remote_url(fab.env.deploy_remote_path)
    
    # initialize remote
    if not release_remote_name in [_i.name for _i in repo.remotes]:
        remote = repo.create_remote(release_remote_name, release_remote_url)
    else:
        remote = repo.remotes[release_remote_name]
        if remote.url != release_remote_url:
            repo.delete_remote(release_remote_name)
            remote = repo.create_remote(release_remote_name, release_remote_url)
    
    # initialize the remote repository (idempotent)
    fab.run('git init %s' % fab.env.deploy_remote_path)
    # silence git complaints about pushes coming in on the current branch
    # the pushes only seed the immutable object store and do not modify the
    # working copy
    fab.run('GIT_DIR=%s/.git git config receive.denyCurrentBranch ignore' %
        fab.env.deploy_remote_path)
    
    # push to remote
    repo.git.push(release_remote_name, release_deployment_branch)
    #remote.push(release_deployment_branch)


def git_push_origin():
    assert 'deploy_git_repository' in fab.env
    assert 'deploy_release_branch' in fab.env
    assert 'deploy_remote_path' in fab.env
    
    # init repo and config
    repo = git.Repo(fab.env.deploy_git_repository)
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # push changes
    if not 'origin' in [_i.name for _i in repo.remotes]:
        return
    repo.git.push('origin', fab.env.deploy_git_repository)
    repo.git.push('origin', release_deployment_branch)


def git_update_remote():
    assert 'deploy_release_branch' in fab.env
    assert 'deploy_remote_path' in fab.env
    
    # init repo and latest commit
    release_deployment_branch = _git_release_deployment_branch(fab.env.deploy_release_branch)
    
    # checkout changes on remote
    with fab.cd(fab.env.deploy_remote_path):
        #fab.run('git checkout %s' % release_deployment_branch)
        fab.run('git reset --hard %s' % release_deployment_branch)

