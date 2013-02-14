import sys
sys.path.append('../')

import git
from fabric.api import *


env.hosts = ['localhost']
env.deploy_git_repository = 'test_repo'
env.deploy_release_branch = 'master'
env.deploy_release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
env.deploy_remote_path = 'temp/git/test_fabdepoit'
env.deploy_merge_release_back = True
env.use_ssh_config = True


@task
def test_release():
    from fabdeploit.git import git_update_local, git_create_release, git_push_release, git_update_remote
    git_update_local()
    git_create_release()
    git_push_release()
    git_update_remote()


