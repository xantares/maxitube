from .common import HomepageSearchExtractor
import re


class LePetitJournalSE(HomepageSearchExtractor):

    def parse_page(self, url):
        webpage = self._download_webpage(url, 'main')
        download_list_html = re.findall(r'<a href="([^"]+vid=[0-9]+)" onclick="[^"]+">\s*<img src="[^"]+"\s+alt="([^"]+)"\s+width="\d+"\s+height="\d+"\s+data-frz-src="([^"]+)"', webpage)
        result = []
        for expr in download_list_html:
            infos = {}
            infos['url'] = expr[0]
            infos['title'] = expr[1]
            infos['thumbnail'] = expr[2]
            result.append(infos)
        return result

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.canalplus.fr/c-divertissement/c-le-petit-journal/pid6515-emission.html'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'http://upload.wikimedia.org/wikipedia/fr/e/eb/Logo_Petit_Journal.jpg'
