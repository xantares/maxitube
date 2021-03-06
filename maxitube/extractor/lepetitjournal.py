from .canalplus import CanalPlusSE
import re

class LePetitJournalSE(CanalPlusSE):

    def _get_page_results(self, query=None, page=None):
        url = 'http://www.canalplus.fr/c-divertissement/c-le-petit-journal/pid6515-emission.html'
        if query is not None:
            raise RuntimeError('Not implemented')
        return self.parse_page(url)

    def _get_icon_url(self):
        return 'http://upload.wikimedia.org/wikipedia/fr/e/eb/Logo_Petit_Journal.jpg'
