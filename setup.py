from setuptools import setup, find_packages

setup(
    name = "fabdeploit",
    version = "0.12.6",
    description = 'fabric utilities for git based deployments',
    author = 'David Danier',
    author_email = 'david.danier@team23.de',
    url = 'https://github.com/ddanier/fabdeploit',
    long_description=open('README.rst', 'r').read(),
    packages = [
        'fabdeploit',
    ],
    package_data = {
    },
    install_requires = [
        'fabric >=1.4',
        'GitPython >=0.3.0',
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities'
    ],
    zip_safe=False,
)

