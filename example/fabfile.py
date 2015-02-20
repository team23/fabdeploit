import sys
sys.path.append('../')

import git
import fabdeploit
from fabric.api import *


class GitFilter(fabdeploit.GitFilter):
    def filter(self):
        for obj in self.filtered_tree:
            if not obj.name[0] in ('1', '5', 'R'):
                self.remove(obj.name)
        with lcd(self.repo.working_tree_dir):
            local('echo $RANDOM > FOOBAR')
            self.add('FOOBAR')

            local('mkdir -p a1/b')
            local('echo $RANDOM > a1/b/1')
            self.add('a1/b/1')

            local('mkdir -p a2/b')
            local('echo $RANDOM > a2/b/2')
            self.add('a2/b/2')

            local('mkdir -p a3/b')
            local('echo $RANDOM > a3/b/3')
            self.add('a3/b/3')


class Git(fabdeploit.Git):
    local_repository_path = 'test_repo'
    remote_repository_path = 'temp/git/test_fabdeploit'
    release_branch = 'master'
    release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
    release_commit_filter_class = GitFilter


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
