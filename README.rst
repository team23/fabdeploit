About
=====

Using git for deployments is a great solution for agile development processes and is
implemented by different people with many different flavours. Any solution has one
thing in common: You have to move the whole history of your project over to your server.
This may be ok for some setups, but has - besides giving many internals to your
clients - some disadvantages like:

* Rollbacks are more complex, as you need to know which commit is the last release
  (may be solved using tags)
* You have to copy the whole repository over to the server, so you cannot skip any
  files or add new ones only needed on the server (like aggregated CSS/JS)

fabdeploit tries to solve these issues by using a seprate release branch, not wired
to the normal git branches and history. This release branch will only contain release
history (one commit for every release/deployment) and allows you to use filters to
change the contents of the commit tree. This way you are able to have a very slick
deployment process only containing what is necessary, you may even add new files not
contained in your normal history.

In addition fabdeploit contains helpers for professional deployment of some common
CMS/Frameworks we use. This will help you implementing a clean process of common deployments,
including enabling maintenance mode, running database migrations, clearing the caches, …

Documentation
=============

Still not as much as intended, but growing, this is a goal for 1.0. Please feel
free to look at the example/ directory or the code itself in addition to the
documentation.

See http://fabdeploit.readthedocs.org/.

