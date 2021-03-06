from .goldenmoustache import GoldenMoustacheSE
from .groland import GrolandSE
from .lepetitjournal import LePetitJournalSE
from .zapping import ZappingSE
from .youtube import YouTubeSE
from .lequotidien import LeQuotidienSE

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
    extractors = [klass() for klass in _ALL_CLASSES]
    return extractors
