from __future__ import absolute_import
import fabric.api as fab
import os

# IDEA:
# Initialize a virtualenv using some REQUIREMENTS file. Then initialize a
# git repository in it. Create tags for every release made using
# "release/$COMMIT_SHA1" as tag name. This way we can revert to old versions
# inside the virtualenv as well.

def python_path():
    in 'deploy_env_path' in fab.env:
        return os.path.join(fab.env.deploy_env_path, 'bin', 'python2')
    else:
        return 'python2'

