from .common import HomepageSearchExtractor
import re


class GoldenMoustacheHSE(HomepageSearchExtractor):

    def _get_homepage_results(self, n=10):

        webpage = self._download_webpage('http://www.goldenmoustache.com/videos/exclusives/', 'main')
        print(webpage)
        download_list_html = re.findall(r'<h3 class="internet-title"><a href="([^"]+)"', webpage)
        # remove duplicates whilst preserving the order
        #seen = set()
        #download_list_html = [ x for x in download_list_html if not (x in seen or seen.add(x))]

        #download_list_html = list(set(download_list_html))
        return download_list_html

    def _get_icon_url(self):
        return 'https://pbs.twimg.com/profile_images/463330574099156992/rspeNrqx_400x400.png'