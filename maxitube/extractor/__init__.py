from .goldenmoustache import GoldenMoustacheSE
from .lepetitjournal import LePetitJournalSE
from .youtube import YouTubeSE

import os
extra_file = os.path.dirname(__file__)+'/extra_imports.py'
if os.path.exists(extra_file):
    exec(compile(open(extra_file).read(), 'a_filename', 'exec'))

_ALL_CLASSES = [
    klass
    for name, klass in globals().items()
    if name.endswith('SE') and name != 'GenericIE'
]

def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return [klass() for klass in _ALL_CLASSES]