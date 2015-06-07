Django example
==============

.. code:: python

    import os
    import git
    import fabdeploit
    import posixpath
    from fabric.api import *


    REPO_PATH = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
    os.chdir(REPO_PATH)

    env.hosts = ['some_hostname']
    env.use_ssh_config = True  # allows you to specify some_hostname in .ssh/config

    @task
    def deploy():
        REMOTE_PATH = 'path/to/htdocs'

        class GitFilter(fabdeploit.GitFilter):
            def filter(self):
                for obj in self.filtered_tree:
                    if not obj.name in ('web', 'scripts'):
                        self.remove(obj.name)
                with lcd(self.repo.working_tree_dir):
                    local('sass web/scss/style.scss web/css/style.css')
                    self.add('web/css/style.css')


        class Git(fabdeploit.Git):
            local_repository_path = REPO_PATH
            remote_repository_path = REMOTE_PATH
            release_branch = 'production'
            release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
            release_commit_filter_class = GitFilter

        class Virtualenv(fabdeploit.Virtualenv2):
            virtualenv_path = posixpath.join(REMOTE_PATH, '_env')
            requirements_file = posixpath.join(REMOTE_PATH, 'PYTHON_REQUIREMENTS')

        class Django(fabdeploit.Django):
            manage_path = posixpath.join(REMOTE_PATH, 'manage.py')

        git = Git()
        virtualenv = Virtualenv()
        django = Django(virtualenv=virtualenv)

        git.pull()
        commit = git.release()
        git.push()
        # TODO: enable maintenance
        git.switch_release()
        virtualenv.init()
        virtualenv.update()
        # make sure we can rollback virtualenv, too
        virtualenv.git.commit(tag='release/%s' % commit.hexsha)
        django.migrate()
        django.collectstatic()
        # TODO: run more deployment jobs?
        # TODO: disable maintenance
