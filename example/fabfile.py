import sys
sys.path.append('../')

import git
from fabric.api import *


env.hosts = ['localhost']
env.deploy_git_repository = 'test_repo'
env.deploy_release_branch = 'master'
env.deploy_release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
env.deploy_remote_git_repository = 'temp/git/test_fabdeploit'
env.deploy_merge_release_back = True
env.use_ssh_config = True

env.deploy_env_path = 'temp/venv/test_fabdeploit'
env.deploy_env_history = True
env.deploy_env_requirements = '%s/REQUIREMENTS' % env.deploy_remote_git_repository



@task
def test():
    from fabdeploit import git, virtualenv
    git.pull_origin()
    commit = git.create_release()
    git.push_origin()
    git.push_release()
    git.switch_release()
    virtualenv.init()
    virtualenv.update_deps()
    virtualenv.create_commit(tag='release/%s' % commit.hexsha)
