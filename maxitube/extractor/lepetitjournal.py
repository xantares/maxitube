from .common import HomepageSearchExtractor
import re


class LePetitJournalSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.canalplus.fr/c-divertissement/c-le-petit-journal/pid6515-emission.html', 'main')

        download_list_html = re.findall(r'<a href="([^"]+vid=[0-9]+)" onclick="[^"]+">\s*<img src="[^"]+"\s+alt="([^"]+)"\s+width="\d+"\s+height="\d+"\s+data-frz-src="([^"]+)"', webpage)
        result = []
        for expr in download_list_html:
            infos = {}
            infos['url'] = expr[0]
            infos['title'] = expr[1]
            infos['thumbnail'] = expr[2]
            result.append(infos)

        return result

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/529938139536580609/_3hhguDs_400x400.jpeg'
