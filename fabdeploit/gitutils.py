import git
import fabric.api as fab


def git_create_release(repo, commit):
    """ Creates a new release commit
    
    Creates release branch if necessary. Uses the following env variables:
    * env.deploy_release_branch: Branch the release lives in
    * env.deploy_release_author: Author for new release commit (optional)
    * env.deploy_release_message: Message used for release commit (optional)
    """
    from gitdb import IStream
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO
    
    assert 'deploy_release_branch' in fab.env
    
    # last release commit
    parent = None
    if fab.env.deploy_release_branch in repo.heads:
        parent = repo.heads[fab.env.deploy_release_branch].commit
    
    # create new commit
    release_commit = git.Commit(repo, git.Commit.NULL_BIN_SHA)
    release_commit.tree = commit.tree
    release_commit.authored_date = commit.authored_date # + 1?
    release_commit.author_tz_offset = commit.author_tz_offset
    release_commit.committed_date = commit.committed_date # + 1?
    release_commit.committer_tz_offset = commit.committer_tz_offset
    if 'deploy_release_author' in fab.env:
        release_commit.author = fab.env.deploy_release_author
        release_commit.committer = fab.env.deploy_release_author
    else:
        release_commit.author = commit.author
        release_commit.committer = commit.committer
    if 'deploy_release_message' in fab.env:
        release_commit.message = fab.env.deploy_release_message
    else:
        release_commit.message = commit.message
    if parent:
        release_commit.parents = [parent]
    else:
        release_commit.parents = []
    print release_commit.parents
    if 'deploy_share_history' in fab.env and fab.env.deploy_share_history:
        release_commit.parents.append(commit)
    print release_commit.parents
    release_commit.encoding = commit.encoding
    
    # write commit
    stream = StringIO()
    release_commit._serialize(stream)
    streamlen = stream.tell()
    stream.seek(0)
    istream = repo.odb.store(IStream(git.Commit.type, streamlen, stream))
    release_commit.binsha = istream.binsha
    
    # update release branch
    if not fab.env.deploy_release_branch in repo.heads:
        repo.create_head(fab.env.deploy_release_branch)
    repo.heads[fab.env.deploy_release_branch].commit = release_commit
    
    # create tag
    if 'deploy_release_tag' in fab.env and fab.env.deploy_release_tag:
        repo.create_tag(fab.env.deploy_release_tag)

