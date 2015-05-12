#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import os.path
import pkg_resources
import warnings
import sys

try:
    from setuptools import setup
    setuptools_available = True
except ImportError:
    from distutils.core import setup
    setuptools_available = False

try:
    # This will create an exe that needs Microsoft Visual C++ 2008
    # Redistributable Package
    import py2exe
except ImportError:
    if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
        print("Cannot import py2exe", file=sys.stderr)
        exit(1)

py2exe_options = {
    "bundle_files": 3,
    "compressed": 1,
    "optimize": 2,
    "dist_dir": '.',
    "dll_excludes": ['w9xpopen.exe'],
    'packages' : ['maxitube'],
}

py2exe_console = [{
    "script": "./maxitube/__main__.py",
    "dest_base": "maxitube",
}]

py2exe_params = {
    'console': py2exe_console,
    'options': {"py2exe": py2exe_options},
    'zipfile': None
}

if len(sys.argv) >= 2 and sys.argv[1] == 'py2exe':
    params = py2exe_params
else:
    #files_spec = [
        #('etc/bash_completion.d', ['youtube-dl.bash-completion']),
        #('etc/fish/completions', ['youtube-dl.fish']),
        #('share/doc/youtube_dl', ['README.txt']),
        #('share/man/man1', ['youtube-dl.1'])
    #]
    #root = os.path.dirname(os.path.abspath(__file__))
    
    data_files = [],
    #for dirname, files in files_spec:
        #resfiles = []
        #for fn in files:
            #if not os.path.exists(fn):
                #warnings.warn('Skipping file %s since it is not present. Type  make  to build all automatically generated files.' % fn)
            #else:
                #resfiles.append(fn)
        #data_files.append((dirname, resfiles))

    params = {
        'data_files': data_files,
    }
    if setuptools_available:
        params['entry_points'] = {'console_scripts': ['maxitube = maxitube:main']}
    else:
        params['scripts'] = ['bin/maxitube']

# Get the version from youtube_dl/version.py without importing the package
#exec(compile(open('maxitube/version.py').read(),
             #'maxitube/version.py', 'exec'))

setup(
    name='maxitube',
    #version=__version__,
    description='YouTube video GUI',
    long_description='Small GUI to download videos from'
    ' YouTube.com and other video sites.',
    url='https://github.com/xantares/maxitube',
    author='Michel Zou',
    author_email='xantares09@hotmail.com',
    maintainer='xantares',
    maintainer_email='xantares09@hotmail.com',
    packages=['maxitube', 'maxitube.extractor'],

    # Provokes warning on most systems (why?!)
    # test_suite = 'nose.collector',
    # test_requires = ['nosetest'],

    classifiers=[
        "Topic :: Multimedia :: Video",
        "Development Status :: 2 - Pre-Alpha",
        "Environment :: X11 Applications :: Qt",
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Programming Language :: Python :: 3",
    ],

    **params
)
