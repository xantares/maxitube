from .common import HomepageSearchExtractor
import re

from youtube_dl.utils import unescapeHTML

class GoldenMoustacheSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.goldenmoustache.com/videos/exclusives/', 'main')
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

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/463330574099156992/rspeNrqx_400x400.png'
        #<h3 class="internet-title"><a href="http://www.goldenmoustache.com/les-super-heros-baptgael-feat-vincent-tirel-57771/">Les Super-Héros &#8211; Bapt&#038;Gael feat Vincent Tirel</a></h3>
