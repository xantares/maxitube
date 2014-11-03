from .lepetitjournal import LePetitJournalHSE

_ALL_CLASSES = [
    klass
    for name, klass in globals().items()
    if name.endswith('HSE') and name != 'GenericIE'
]
#_ALL_CLASSES.append(GenericIE)


def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return [klass() for klass in _ALL_CLASSES]