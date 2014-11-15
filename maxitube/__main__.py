
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
import signal


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
            print('-- downloading:',vid)
            infos = self.downloader_.extract_info(vid)
            title = infos['title']
            filename = self.download_location_ + '/' + title.replace('/','_') + '.flv'
            cmd_line = subprocess.list2cmdline(['vlc', '--fullscreen', filename])
            print('-- run player:', cmd_line)
            p = subprocess.Popen(['vlc', '--fullscreen', filename])


class ThumbnailCache(object):
    def __init__(self, height, ratio):
        super(ThumbnailCache, self).__init__()
        self.cache_ = {}
        self.height_ = height
        self.ratio_ = ratio

    def __call__(self, image_url):
        if not image_url in self.cache_:
            filename, headers = urllib.request.urlretrieve(image_url)
            srcImage = QImage(filename)

            # column images
            if srcImage.height() > 4*srcImage.width():
                srcImage = srcImage.copy(0, 0, srcImage.width(), int(srcImage.width()/self.ratio_))

            # black borders
            ratio = 1.0*srcImage.width()/srcImage.height()
            if ratio > self.ratio_:
                srcImage = srcImage.scaledToWidth(self.height_/self.ratio_)
                destPos = QPoint(0, (self.height_-srcImage.height())//2)
            else:
                srcImage = srcImage.scaledToHeight(self.height_)
                destPos = QPoint(int(self.ratio_*self.height_-srcImage.width())//2, 0)
            destImage = QImage(self.ratio_*self.height_, self.height_, srcImage.format())
            painter = QPainter(destImage)
            painter.fillRect(painter.window (), QColor('black'))
            painter.drawImage(destPos, srcImage)
            painter.end()

            self.cache_[image_url] = destImage
        return self.cache_[image_url]

class PlaylistItemDelegate(QItemDelegate):
    queueVid = Signal(str)

    def __init__(self):
        super(PlaylistItemDelegate, self).__init__()
        self.height_ = 96
        self.ratio_ = 16./9.
        self.image_cache_ = ThumbnailCache(self.height_, self.ratio_)
        dlm = DownloadManagerFactory().GetInstance()
        self.queueVid.connect(dlm.add)

    def paint(self, painter, option, index):
        infos = index.data()

        if 'thumbnail' in infos:
            image_url = infos['thumbnail']
            image = self.image_cache_(image_url)
            painter.drawImage(option.rect.topLeft(), image)

        if 'title' in infos:
            title = infos['title']
            painter.drawText(option.rect.topLeft().x()+int(128+self.height_), option.rect.topLeft().y()+16, title)

        if 'upload_date' in infos:
            upload_date = infos['upload_date']
            painter.drawText(option.rect.topLeft().x()+int(128+self.height_), option.rect.topLeft().y()+32, upload_date)

    def sizeHint(self, option, index):
        return QSize(int(2*self.ratio_*self.height_), self.height_)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QEvent.MouseButtonPress):
            url = index.data()['url']
            self.queueVid.emit(url)
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

    def update(self, extractor_name=None, query=None):
        print('-- update query=', query, 'extractor_name=', extractor_name)
        self.query_ = query
        current_extractors = self.extractors_
        if extractor_name:
            for ext in current_extractors:
                if ext.IE_NAME == extractor_name:
                    current_extractors = [ext]
                    break
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


class SiteTable(QTableWidget):
    requestBrowse = Signal(str)

    def __init__(self, extractors):
        super(SiteTable, self).__init__()
        self.setRowCount(len(extractors))
        self.setColumnCount(1)
        row = 0
        cache = ThumbnailCache(64, 1.)
        for extractor in extractors:
            item = QTableWidgetItem()
            icon_url = extractor._get_icon_url()
            image = cache(icon_url)
            icon = QIcon(QPixmap.fromImage(image))
            item.setIcon(icon)
            item.setText(extractor.IE_NAME)
            self.setItem (row, 0, item)
            row += 1
        #connect(self, SIGNAL(cellClicked(int,int)), this, SLOT(previousWeek()));
        self.cellClicked.connect(self.onCellClick) 

    @Slot(int, int)
    def onCellClick(self, row, col):
        extractor_name = self.item(row, col).text()
        self.requestBrowse.emit(extractor_name)

    def sizeHint(self):
        return QSize(256,800)


class MainWindow(QMainWindow):

    @Slot()
    def onSearch(self):
        query = self.searchBar_.text()
        self.playlist_.update(query=query)

    @Slot(str)
    def onBrowse(self, extractor_name):
        self.playlist_.update(extractor_name)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.resize(1024, 768)
        extractors = extractor.gen_extractors()
        ydl = YoutubeDL()
        self.playlist_ = PlaylistModel()
        panelWidget = QTabWidget()
        searchWidget = QWidget()
        searchLayout = QVBoxLayout()
        barLayout = QHBoxLayout()
        self.searchBar_ = QLineEdit()
        barLayout.addWidget(self.searchBar_)
        okButton = QPushButton('Ok')
        barLayout.addWidget(okButton)
        barLayout.addStretch()
        okButton.clicked.connect(self.onSearch)
        searchLayout.addLayout(barLayout)
        #playlistView = PlaylistView()
        #playlistView.setModel(playlist)
        #searchLayout.addWidget(playlistView)
        searchLayout.addStretch()
        searchWidget.setLayout(searchLayout)

        browseLayout = QVBoxLayout()

        browseLayout.addStretch()
        browseWidget = SiteTable(extractors)
        browseWidget.requestBrowse.connect(self.onBrowse)
        browseWidget.setLayout(browseLayout)
        panelWidget.addTab(browseWidget, 'Browse') 
        panelWidget.addTab(searchWidget, 'Search')

        mainLayout = QHBoxLayout()
        mainLayout.addWidget(panelWidget)
        searchView = PlaylistView()
        searchView.setModel(self.playlist_)
        mainLayout.addWidget(searchView)
        mainWidget = QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)


def main(argv=None):


    signal.signal(signal.SIGINT, signal.SIG_DFL)
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