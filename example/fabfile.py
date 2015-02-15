import sys
sys.path.append('../')

import git
import fabdeploit
from fabric.api import *


class Git(fabdeploit.Git):
    local_repository_path = 'test_repo'
    remote_repository_path = 'temp/git/test_fabdeploit'
    release_branch = 'master'
    release_author = 'Team23 GmbH & Co. KG <info@team23.de>'

    def filter_release_commit(self):
        repo = self.release_commit.repo
        tree = git.Tree(repo, git.Tree.NULL_BIN_SHA)
        tree._cache = [] # prefill cache
        for obj in self.release_commit.tree:
            if obj.path[0] in ('1', '5', 'R'):
                tree.cache.add(obj.hexsha, obj.mode, obj.path)
        tree.cache.set_done()
        self._raw_write_object(tree)
        self.release_commit.tree = tree


class Virtualenv(fabdeploit.Virtualenv2):
    virtualenv_path = 'temp/git/test_fabdeploit/env'
    requirements_file = 'temp/git/test_fabdeploit/REQUIREMENTS'


env.hosts = ['localhost']
env.use_ssh_config = True


@task
def test():
    git = Git()
    # git.pull()
    commit = git.release(merge_back=True)
    # git.push()
    git.push_release()
    git.switch_release()

    virtualenv = Virtualenv()
    virtualenv.init()
    virtualenv.update()

    virtualenv_git = fabdeploit.VirtalenvGit(virtualenv)
    virtualenv_git.commit(tag='release/%s' % commit.hexsha)
