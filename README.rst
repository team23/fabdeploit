git Releases
============

fabdeplois allows you to use git for your releases while not pushing
all your history to your customers server. It uses gitpython to manage
release commits in a distinct branch which gets pushed to the server.

Your history may then look like::

    |
    *    Commit after release (commit lives in "master")
    |
    *    Release commit gets merged back to "master"
    |\
    | *  The actual release commit (living in "release/master")
    | |
    * |  Normal commit, it's tree is used for release commit above ("master")
    | |
    * |  Another normal commit ("master")
    | |
    * |  Another commit, that merges release back ("master")
    |\|
    | *  Another release commit ("release/master")
    | |
    * |  Another normal commit, tree used for release above ("master")
    | |
    | |  ...I think you should see the pattern now ;--)

As you may see release commits **never** have any parents except the previous
release. This way your history will never be pushed to your customers server,
as long as you only push the release branch. If you look at the release branch
("release/master") the history looks like::

    *  The actual release commit (living in "release/master")
    |
    *  Another release commit ("release/master")
    |



Use cases
=========





Option reference (env)
======================

git
---

* env.deploy_git_repository: Path to the local git repository
* env.deploy_release_branch: Branch that should be released
* env.deploy_release_author: Author for new release commit (optional)
* env.deploy_release_message: Message used for release commit (optional)
* env.deploy_release_tag: Tag that should be created for release commit (optional)
* env.deploy_merge_release_back: Normally we merge the release commit back to
  the branch it originated from. You can turn this off (on by default)
* env.deploy_remote_git_repository: Remote git repository path

django
------

* env.deploy_manage_path: Path to manage.py

virtualanv
----------

* env.deploy_env_path: Path to virtualenv
* env.deploy_env_history: Keep virtualenv in git to allow switching back
  to older releases. (off by default)
* env.deploy_requirements_path: Path to requirements file (for automatic
  virtualenv updates)
