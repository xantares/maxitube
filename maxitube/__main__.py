
# Allow access to command-line arguments
import sys
# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *

#from PyQt4.QtCore import *
#from PyQt4.QtGui import *
from youtube_dl import YoutubeDL
import extractor
#from urllib.request import urlretrieve
import urllib

def main(argv=None):

    # Every Qt application must have one and only one QApplication object;
    # it receives the command line arguments passed to the script, as they
    # can be used to customize the application's appearance and behavior
    qt_app = QApplication(sys.argv)

    mainWidget = QWidget()

    searchLayout = QVBoxLayout()
    searchBar = QLineEdit('lept')
    searchLayout.addWidget(searchBar)

    mainWidget.setLayout(searchLayout)
    table = QTableWidget(10,2)
    extractors = extractor.gen_extractors()
    i = 0
    ydl = YoutubeDL()
    for ext in extractors:
        ext.set_downloader(ydl)
        res = ext._get_homepage_results()
        print(res)
        for vid in res:
            infos = ydl.extract_info(vid, download=False)
                #def extract_info(self, url, download=True, ie_key=None, extra_info={},
                     #process=True):
            print(infos)
            if 'title' in infos:
                item = QTableWidgetItem(infos['title'])
                table.setItem(i, 0, item)

            if 'thumbnail' in infos:
                filename, headers = urllib.request.urlretrieve(infos['thumbnail'])
                pixmap = QPixmap(filename)
                label = QLabel()
                label.setPixmap(pixmap)
                table.setCellWidget(i,1,label)
                #item = QTableWidgetItem(infos['thumbnail'])
                #table.setItem(i, 1, item)

            #if i >= 10:
                #break
            i += 1

            #table.setRowCount(i)

            item = QTableWidgetItem('XXX'+vid)
            table.setItem(i, 0, item)
            print (table.item(i,0))
            #table.item(i,0).setText('EEEE')
            print (i, vid)

    tab1 = QScrollArea()
    tab1.setWidget(table)
    tab1.setWidgetResizable(True)
    searchLayout.addWidget(tab1)
    
    mainWidget.show()
    
    #qt_app.setMainWidget(mainWidget)
    # Run the application's event loop
    qt_app.exec_()
main()