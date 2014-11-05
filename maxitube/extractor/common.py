import urllib.request
from youtube_dl import YoutubeDL
from youtube_dl.extractor.common import SearchInfoExtractor

class HomepageSearchExtractor(SearchInfoExtractor):
    """
    Instances should define:
     - _get_homepage_results
     - _get_n_results:
     - _get_icon_url
    """
    def __init__(self):
        pass
        #ydl = YoutubeDL()
        #self.set_downloader(ydl)

    def _get_n_results(self, query, n):
        """Search
        """
        raise RuntimeError('Not implemented')

    def _get_homepage_results(self, n=10):
        """Lists  homepage content
        """
        raise RuntimeError('Not implemented')

    def _get_icon_url(self):
        return r'https://pbs.twimg.com/profile_images/501746918968406018/E9niujVF.jpeg'
