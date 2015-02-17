from .canalplus import CanalPlusSE
import re

class GrolandSE(CanalPlusSE):

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.canalplus.fr/c-divertissement/pid1787-c-groland.html'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'http://imgcocktail.pole-esg.net/Extranet_dabovi_c08_made-in-groland.jpg'
