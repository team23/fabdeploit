import sys
sys.path.append('../')

import git
from fabric.api import *


env.hosts = ['localhost']
env.deploy_git_repo = 'test_repo'
env.deploy_release_branch = 'release'
env.deploy_share_history = True


@task
def test_release():
    from fabdeploit.gitutils import git_create_release
    repo = git.Repo(env.deploy_git_repo)
    commit = repo.heads.master.commit
    git_create_release(repo, commit)

