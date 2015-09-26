from .canalplus import CanalPlusSE
import re

class GrolandSE(CanalPlusSE):

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.canalplus.fr/c-divertissement/pid1787-c-groland.html'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'https://upload.wikimedia.org/wikipedia/fr/3/36/Made_in_Groland_2012_logo.png'
