from .canalplus import CanalPlusSE
import re

class ZappingSE(CanalPlusSE):

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.canalplus.fr/c-infos-documentaires/pid1830-c-zapping.html'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'http://rue89.nouvelobs.com/sites/news/files/styles/asset_img_full/public/assets/image/2007/09/Zapping_0.jpg'
