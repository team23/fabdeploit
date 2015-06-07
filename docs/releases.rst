About fabdeploit release history
================================

As stated before fabdeploit allows you to use git for your releases while not pushing
all your history to your or your customers server. It uses GitPython to manage
release commits in a distinct branch which gets pushed to the server. This
branch only contains release history.

Your history may then look like::

    …
    |
    *    Commit after release (commit lives in "master")
    |
    | *  The actual release commit (living in "release/master")
    | |
    * |  Normal commit, it's tree is used for release commit above ("master")
    | |
    * |  Another normal commit ("master")
    | |
    | *  Another release commit ("release/master")
    | |
    * |  Another normal commit, tree used for release above ("master")
    | |
    | |  ...I think you should see the pattern now ;--)

As you may see release commits **never** have any parents except the previous
release. This way your history will never be pushed directly to the server,
as long as you only push the release branch. If you look at the release branch
("release/master") the history looks like::

    *  The actual release commit (living in "release/master")
    |
    *  Another release commit ("release/master")
    |

Each release commit may be run through a filter, which allows you to remove
files from the release commit tree or add new files to the release commit. This may be used
for many different use cases, like:

* Skip files not appropriate for the server (documentation, PSD files, …)
* Converting SASS to CSS and then add the new CSS files
* Create CSS/JS aggregates
