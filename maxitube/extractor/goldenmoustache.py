from .common import HomepageSearchExtractor
import re

from youtube_dl.utils import unescapeHTML

class GoldenMoustacheSE(HomepageSearchExtractor):

    def parse_page(self, url):
        webpage = self._download_webpage(url, 'main')
        url_thumb_list = re.findall(r'<a\s+href="([^"]+)"><img\s+width="\d+"\s+height="\d+"\s+src="([^"]+)"', webpage)
        url_title_list = re.findall(r'<h3 class="internet-title"><a href="([^"]+)">([^<]+)<', webpage)
        result = []
        i = 0
        for expr in url_thumb_list:
            expr2 = url_title_list[i]
            infos = {}
            infos['url'] = expr[0]
            infos['title'] = unescapeHTML(expr2[1])
            infos['thumbnail'] = expr[1]
            result.append(infos)
            i += 1
        return result

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.goldenmoustache.com/videos/exclusives/'
        if page is not None:
            url += 'page/'+str(page)+'/'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/463330574099156992/rspeNrqx_400x400.png'
