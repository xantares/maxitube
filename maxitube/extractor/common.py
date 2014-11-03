import urllib.request
from youtube_dl import YoutubeDL
from youtube_dl.extractor.common import SearchInfoExtractor

class HomepageSearchExtractor(SearchInfoExtractor):
    """
    Instances should define _get(self) & _get_n_results(self, query, n):
    """
    def __init__(self):
        ydl = YoutubeDL()
        self.set_downloader(ydl)

    def _get_n_results(self, query, n):
        """Search
        """
        raise RuntimeError('Not implemented')

    def _get_homepage_results(self, n=10):
        """Lists  homepage content
        """
        raise RuntimeError('Not implemented')
