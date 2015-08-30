Git
===

Options
-------

**local_repository_path** (mandatory)
    Path to the local repository.

**remote_repository_path** (mandatory)
    Remote repository path.

release_author
    You may set some author for the release commits, if None original author will be used.

**release_branch** (mandatory)
    The branch you want to release ("production", "staging"). fabdeploit will create an
    "release/…"-branch for the release history ("release/production")

release_commit_filter_class
    A filter class to be used when creating the release commit tree. The filter may
    remove files from or add files to the commit tree. A filter should be a subclass
    of GitFilter and implement the filter()-method. The filter may then use self.add()
    and self.remove() to change the tree. Use self.filtered_tree to access the tree
    itself.

Methods
-------

pull_origin()
    Should be called before any additional actions, ensures the local
    repository is in sync with the origin.

pull()
    Calls self.pull_origin() if origin existy in local repository. Should
    be used instead of pull_origin() for a more generic appproach.

create_release_commit(message=None)
    Creates the new release commit by copying the last commit of release_branch
    into the release branch (applying the filter). An optional commit message
    may be provided.

tag_release(tag_name)
    Created a tag for the commit created by create_release_commit()

merge_release_back()
    Created a new commit in release_branch with the commit created by
    create_release_commit() and the last commit in this branch as parents.
    Can be used to push release commits back into the normal branches.
    SHOULD BE USED WITH CARE. SHOULD NEVER BE USED WHEN FILTERS ARE IN
    PLACE.

release(message=None, tag_name=None, merge_back=False)
    Calls create_release_commit(), tag_release() and merge_release_back()
    according to the parameters provided.

push_release()
    Pushes the commit created by create_release_commit() to the release
    git URL (see remote_repository_path). Created the repository if necessary.

push_origin()
    Pushes the release branch to origin.

push()
    Pushed the release branch to the release git URL and origin if origin exists
    in the local git repository.

switch_release(commit=None)
    Switched to a particular commit on the remote server. You may specify the
    commit yourself, if None the commit created by create_release_commit()
    will be used. This must be run to apply all changes on the server.

webserver_harden_remote_git()
    (Should be run after push)

    Tries to disable access to the .git folder for common configuration. This is
    currently done by writing a .htaccess (for Apache) and setting permissions to
    rwx------ (700) so no other user is allowed to access to directory.

    **Note**: *You should never push directly into the document root!* It is always better
    to have the document root being a sub-folder in your git repository for multiple
    good reasons (for example as "htdocs"). Anyways there are situations where you
    cannot ensure such a sane setup. This method helps you not shooting yourself
    in the foot. Please make sure it works for your setup, for example by
    browsing to www.your-domain.com/.git/config, you should get "access denied".

Example Workflow
----------------

.. code:: python

    git = Git(local_repository_path="…", remote_repository_path="…", release_branch="…")
    git.pull()  # Make sure we have all remote changes
    git.create_release_commit("New release")
    git.push()  # Make sure the new release is copied to origin and server
    # git.webserver_harden_remote_git() # No web access to .git
    git.switch_release()  # Apply all file changes

Example GitFilter
-----------------

.. code:: python

    class MyGitFilter(GitFilter):
        def filter(self):
            self.add('some/new/file.txt')
            self.remove('docs')  # remove whole docs directory
            self.remove('path/to/file.psd')

    git = Git(release_commit_filter_class=MyGitFilter, "…")
    # …
