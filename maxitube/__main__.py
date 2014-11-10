
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
import tempfile
import subprocess
import os
import dateutil.parser


class DownloadManagerFactory:
    instance_ = None

    def __init__(self):
        if not self.__class__.instance_:
            self.__class__.instance_ = DownloadManager()

    def GetInstance(self):
        return self.__class__.instance_

class DownloadManager(QStandardItemModel):
    def __init__(self):
        super(DownloadManager, self).__init__()
        self.initialized_ = True
        self.downloader_ = YoutubeDL()
        self.reader_ = 'vlc'
        self.downloader_.add_progress_hook(self.progress)
        self.queue_ = []
        self.simulateous_downloads_ = 1
        self.download_location_ = tempfile.gettempdir()
        self.downloader_.params['outtmpl'] = self.download_location_+'/%(title)s.%(ext)s'
        self.downloader_.params['noprogress'] = False

    @Slot(str)
    def add(self, vid):
        if not vid in self.queue_:
            self.queue_.append(vid)
            item = QStandardItem(vid)
            self.appendRow(item)
            self.update()

    def progress(self, percent):
        print(percent)

    def update(self):
        if len(self.queue_) > 0:
            self.downloader_.add_progress_hook(self.progress)
            vid = self.queue_.pop()
            print('DownloadManager.update', vid)

            infos = self.downloader_.extract_info(vid)
            title = infos['title']
            filename = self.download_location_ + '/' + title.replace('/','_') + '.flv'
            cmd_line = subprocess.list2cmdline(['vlc', filename])
            print('cmd_line=',cmd_line)
            os.system(cmd_line.encode())


class PlaylistItemDelegate(QItemDelegate):
    queueVid = Signal(str)
    fetchVid = Signal(str)

    def __init__(self):
        super(PlaylistItemDelegate, self).__init__()
        self.size_ = 128
        self.ratio_ = 114./64
        self.infos_cache_ = {}
        self.image_cache_ = {}
        dlm = DownloadManagerFactory().GetInstance()
        self.queueVid.connect(dlm.add)
        self.fetchVid.connect(self.fetch)

    @Slot(str)
    def fetch(self, key):
        if not key in self.infos_cache_:
            ydl = YoutubeDL()
            self.infos_cache_[key] = ydl.extract_info(key, download=False)

        if 'thumbnail' in self.infos_cache_[key] and not key in self.image_cache_:
            thumbnail = self.infos_cache_[key]['thumbnail']
            filename, headers = urllib.request.urlretrieve(thumbnail)
            image = QImage(filename)
            if image.height() > image.width():
                image = image.copy(0, 0, image.width(), int(image.width()/self.ratio_))
            image = image.scaledToHeight(self.size_)
            self.image_cache_[key] = image

    def paint(self, painter, option, index):
        key = index.data()
        self.fetchVid.emit(key)

        if key in self.image_cache_:
            image = self.image_cache_[key]
        else:
            image = QImage(int(self.ratio_*self.size_), self.size_, QImage.Format_Mono)

        painter.drawImage(option.rect.topLeft(), image)

        if key in self.infos_cache_:
            #print(self.infos_cache_[key])
            if 'title' in self.infos_cache_[key]:
                title = self.infos_cache_[key]['title']
                text = title
                painter.drawText(option.rect.topLeft().x()+int(128+self.size_), option.rect.topLeft().y()+16, text)
            if 'upload_date' in self.infos_cache_[key]:
                upload_date = self.infos_cache_[key]['upload_date']
                painter.drawText(option.rect.topLeft().x()+int(128+self.size_), option.rect.topLeft().y()+32, upload_date)

    def sizeHint(self, option, index):
        return QSize(int(2*self.ratio_*self.size_), self.size_)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QEvent.MouseButtonPress):
            self.queueVid.emit(index.data())
            return True
        return False


class PlaylistModel(QAbstractListModel):


    def __init__(self):
        super(PlaylistModel, self).__init__()
        self.downloader_ = YoutubeDL()
        self.extractors_ = extractor.gen_extractors()
        for ext in self.extractors_:
            ext.set_downloader(self.downloader_)
        self.vids_=[]

    def update(self, extractor_key='all', query=None):
        print('update q=', query, 'ext=', extractor_key)
        self.extractor_key_ = extractor_key
        self.query_ = query
        if self.extractor_key_ == 'all':
            current_extractors = self.extractors_
        else:
            raise ValueError('todo')
        self.vids_=[]
        for ext in current_extractors:
            if not self.query_:
                self.vids_.extend(ext._get_homepage_results())
            else:
                try:
                    self.vids_.extend(ext._get_n_results(self.query_, 10))
                except:
                    print('not supported')
                    raise ()
        self.modelReset.emit()

    def rowCount(self, parent):
        return len(self.vids_)

    def data(self, index, role):
        return self.vids_[index.row()]

class PlaylistView(QListView):
    def __init__(self):
        super(PlaylistView, self).__init__()
        self.setItemDelegate(PlaylistItemDelegate())

    def sizeHint(self):
        return QSize(256,800)


class MainWindow(QMainWindow):

    @Slot()
    def updateSearch(self):
        query = self.searchBar_.text()
        self.playlist_.update(query=query)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(1024, 768)
        extractors = extractor.gen_extractors()
        ydl = YoutubeDL()
        self.playlist_ = PlaylistModel()
        self.playlist_.update()
        mainWidget = QTabWidget()
        searchWidget = QWidget()
        searchLayout = QVBoxLayout()
        barLayout = QHBoxLayout()
        self.searchBar_ = QLineEdit()
        barLayout.addWidget(self.searchBar_)
        okButton = QPushButton('Ok')
        barLayout.addWidget(okButton)
        barLayout.addStretch()
        okButton.clicked.connect(self.updateSearch)
        searchLayout.addLayout(barLayout)
        #playlistView = PlaylistView()
        #playlistView.setModel(playlist)
        #searchLayout.addWidget(playlistView)
        searchView = PlaylistView()
        searchView.setModel(self.playlist_)
        searchLayout.addWidget(searchView)
        searchLayout.addStretch()
        searchWidget.setLayout(searchLayout)

        browseView = PlaylistView()
        browseView.setModel(self.playlist_)
        browseLayout = QVBoxLayout()

        browseLayout.addWidget(browseView)
        browseWidget = QWidget()
        browseWidget.setLayout(browseLayout)
        mainWidget.addTab(browseWidget, 'Browse') 
        mainWidget.addTab(searchWidget, 'Search')

        mainWidget
        self.setCentralWidget(mainWidget)


def main(argv=None):

    # Every Qt application must have one and only one QApplication object;
    # it receives the command line arguments passed to the script, as they
    # can be used to customize the application's appearance and behavior
    qt_app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    #qt_app.setMainWidget(mainWidget)
    # Run the application's event loop
    qt_app.exec_()
main()