from .common import HomepageSearchExtractor
import re

from youtube_dl.utils import unescapeHTML

class LeQuotidienSE(HomepageSearchExtractor):

    def parse_page(self, url):
        webpage = self._download_webpage(url, 'main')
        print('parse_page')
        #url_thumb_list = re.findall(r'<a\s+href="([^"]+)"><img\s+width="\d+"\s+height="\d+"\s+src="([^"]+)"', webpage)
        url_list = re.findall(r'<a\s+href="([^"]+)"\s+class="videoLink', webpage)
        thumbnail_list = re.findall(r'data-srcset="([^ ]+) 1x', webpage)
        title_list = re.findall(r'<p class="title">([^<]+)</p><p class="stitle">', webpage)
        result = []
        url_size = len(url_list)
        thumbnail_size = len(thumbnail_list)
        title_size = len(title_list)
        for i in range(title_size):
            infos = {}
            infos['url'] = 'http://www.tf1.fr' + url_list[url_size-title_size+i]
            infos['title'] = unescapeHTML(title_list[i])
            infos['thumbnail'] = 'http:' + thumbnail_list[i*3]
            result.append(infos)
        return result

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.tf1.fr/tmc/quotidien-avec-yann-barthes/videos/'
        #if page is not None:
            #url += str(page)+'/'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'https://upload.wikimedia.org/wikipedia/fr/0/06/Quotidien-logo.png'
