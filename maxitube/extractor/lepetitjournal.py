from .common import HomepageSearchExtractor
import re


class LePetitJournalHSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.canalplus.fr/c-divertissement/c-le-petit-journal/pid6515-emission.html', 'main')

        download_list_html = re.findall(r'<a href="([^"]+vid=[0-9]+)"', webpage)

        # remove duplicates whilst preserving the order
        seen = set()
        download_list_html = [ x for x in download_list_html if not (x in seen or seen.add(x))]

        #download_list_html = list(set(download_list_html))
        return download_list_html

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/529938139536580609/_3hhguDs_400x400.jpeg'