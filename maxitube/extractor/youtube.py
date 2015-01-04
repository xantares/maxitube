from .common import HomepageSearchExtractor
import re

from youtube_dl.utils import unescapeHTML


class YouTubeSE(HomepageSearchExtractor):
    def parse_page(self, url):
        webpage = self._download_webpage(url, 'main')
        download_list_html = re.findall(r'<a href="/watch\?v=([^"]+)" class="[^"]+" data-sessionlink="[^"]+" title="([^"]+)"', webpage)
        result = []
        for expr in download_list_html:
            infos = {}
            infos['url'] = 'https://www.youtube.com/watch?v=' + expr[0]
            infos['title'] = unescapeHTML(expr[1])
            infos['thumbnail'] = 'https://i.ytimg.com/vi/'+ expr[0]+ '/mqdefault.jpg'
            result.append(infos)
        return result

    def _get_page_results(self, query=None, page=None):
        url = 'https://www.youtube.com'
        if query is not None:
            url += '/results?search_query='+'+'.join(query.split(' '))
            if page is not None and page>1:
                url += '&page='+str(page)
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'http://s.ytimg.com/yts/img/youtube_logo_stacked-vfl225ZTx.png'
