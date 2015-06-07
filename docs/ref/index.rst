fabdeploit reference
====================

fabdeploit utilizes multiple helper classes to implement the desired behavior for
a clean deployment process.

Each class provides some options (instance attributes) to setup where files live, which
commands to call, etc. These options may be provided when constructing the class or
be set as class attributes when using subclasses. Bold options are mandatory.

Each class will in addition provide some methods to do the real work (like running
some command). You have to call these methods in the right way to get things working
like intended.

Below you will find an overview of all classes, options, methods and an example workflow.

.. toctree::
   :maxdepth: 2

   git
   virtualenv
   django
   drupal
   magento