from .common import HomepageSearchExtractor
import re


class GoldenMoustacheSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.goldenmoustache.com/videos/exclusives/', 'main')
        download_list_html = re.findall(r'<a\s+href="([^"]+)"><img\s+width="\d+"\s+height="\d+"\s+src="([^"]+)"', webpage)
        result = []
        for expr in download_list_html:
            infos = {}
            infos['url'] = expr[0]
            #infos['title'] = expr[1]
            infos['thumbnail'] = expr[1]
            result.append(infos)
        return result

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/463330574099156992/rspeNrqx_400x400.png'
