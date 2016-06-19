from .common import HomepageSearchExtractor
import re

from youtube_dl.utils import unescapeHTML


class CanalPlusSE(HomepageSearchExtractor):

    def parse_page(self, url):
        webpage = self._download_webpage(url, 'main')
        download_list_html = re.findall(r'<a href="([^"]+vid=[0-9]+)" onclick="[^"]+">\s*<img src="([^"]+)"\s+alt="([^"]+)"(?:\s+width="\d+"\s+height="\d+"\s+data-frz-src="([^"]+)")?', webpage)
        result = []
        for expr in download_list_html:
            infos = {}
            infos['url'] = 'http://www.canalplus.fr' + expr[0]
            infos['title'] = unescapeHTML(expr[2])
            infos['thumbnail'] = expr[1]
            if len(expr)>3 and len(expr[3])>0:
                infos['thumbnail'] = expr[3]
            result.append(infos)
        return result
