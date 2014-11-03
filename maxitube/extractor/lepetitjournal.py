from .common import HomepageSearchExtractor
import re


class LePetitJournalHSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.canalplus.fr/c-divertissement/c-le-petit-journal/pid6515-emission.html', 'main')

        download_list_html = re.findall('<a href="([^"]+vid=[0-9]+)"', webpage)
        return download_list_html

    def _get_icon_url(self):
        raise RuntimeError('should override _get_icon_url')