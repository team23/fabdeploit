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

    # # Example usage:
    # # Change commit after release was created. This allows using shell commands
    # # in addition to the filter above. You may for example generate CSS files
    # # using sass and add them to your release commit.
    # def create_release_commit(self, *args, **kwargs):
    #     super(Git, self).create_release_commit(*args, **kwargs)
    #     with lcd(self.local_repository_path):
    #         local('git checkout %s' % self.release_deployment_branch())
    #         local('echo $RANDOM > FOOBAR')
    #         local('git add FOOBAR')
    #         local('git commit --amend --no-edit')
    #         self.release_commit = self._get_local_repo().heads[self.release_deployment_branch()].commit
    #     return self.release_commit


class Virtualenv(fabdeploit.Virtualenv2):
    virtualenv_path = 'temp/git/test_fabdeploit/env'
    requirements_file = 'temp/git/test_fabdeploit/REQUIREMENTS'


env.hosts = ['localhost']
env.use_ssh_config = True


@task
def test():
    git = Git()
    git.pull()
    commit = git.release(merge_back=True)
    git.push()
    git.switch_release()

    virtualenv = Virtualenv()
    virtualenv.init()
    virtualenv.update()

    virtualenv_git = fabdeploit.VirtalenvGit(virtualenv)
    virtualenv_git.commit(tag='release/%s' % commit.hexsha)
