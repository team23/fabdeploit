Basic example
=============

.. code:: python

    import os
    import git
    import fabdeploit
    from fabric.api import *


    REPO_PATH = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
    os.chdir(REPO_PATH)

    env.hosts = ['some_hostname']
    env.use_ssh_config = True  # allows you to specify some_hostname in .ssh/config


    @task
    def deploy():
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
            remote_repository_path = 'path/to/htdocs'
            release_branch = 'production'
            release_author = 'Team23 GmbH & Co. KG <info@team23.de>'
            release_commit_filter_class = GitFilter

        git = Git()
        git.pull()
        git.release()
        git.push()
        # TODO: enable maintenance
        git.switch_release()
        # TODO: run deployment jobs (like clear cache, db migrations, …)
        # TODO: disable maintenance
