
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
import concurrent.futures
from urllib.error import HTTPError

try:
    from whoosh.fields import Schema, TEXT, ID, STORED
    from whoosh.index import create_in
    from whoosh.qparser import QueryParser
    whoosh_available = True
except:
    whoosh_available = False


class DownloadManagerFactory:
    instance_ = None

    def __init__(self):
        if not self.__class__.instance_:
            self.__class__.instance_ = DownloadManager()

    def GetInstance(self):
        return self.__class__.instance_

class DownloadWorker(QObject):
    finished = Signal()
    def __init__(self, manager):
        super(DownloadWorker, self).__init__()
        self.manager_ = manager

    def doWork(self):
        self.manager_.update()
        self.finished.emit()

class DownloadManager(QStandardItemModel):
    def __init__(self):
        super(DownloadManager, self).__init__()
        self.initialized_ = True
        self.downloader_ = YoutubeDL()
        self.reader_ = 'vlc'
        self.downloader_.add_progress_hook(self.progress)
        self.queue_ = []
        self.simulateous_downloads_ = 1
        self.download_location_ = tempfile.gettempdir()+'/maxitube'
        self.downloader_.params['outtmpl'] = self.download_location_+'/%(autonumber)s'
        self.downloader_.params['noprogress'] = False

    @Slot(str)
    def add(self, vid):
        if not vid in self.queue_:
            self.queue_.append(vid)
            item = QStandardItem(vid)
            self.appendRow([item, QStandardItem('queued'), QStandardItem('0%')])

            self.worker_ = DownloadWorker(self)
            self.workerThread_ = QThread()
            self.worker_.moveToThread(self.workerThread_)
            self.workerThread_.started.connect(self.worker_.doWork)
            self.worker_.finished.connect(self.workerThread_.quit)
            self.workerThread_.finished.connect(self.worker_.deleteLater)
            self.workerThread_.finished.connect(self.workerThread_.deleteLater)
            self.workerThread_.start()
            #self.update()

    def progress(self, dl_infos):
        if 'filename' in dl_infos:
            filename = dl_infos['filename']
            index = int(os.path.basename(filename))-1
            if 'total_bytes' in dl_infos and 'downloaded_bytes' in dl_infos:
                total_bytes = dl_infos['total_bytes']
                downloaded_bytes = dl_infos['downloaded_bytes']
                percent = (1.0 * downloaded_bytes) / total_bytes
                self.item(index,2).setText('%.2f %%' % percent)
        self.dataChanged.emit(self.indexFromItem(self.item(index,0)), self.indexFromItem(self.item(index,2)))

    def update(self):
        if len(self.queue_) > 0:
            self.downloader_.add_progress_hook(self.progress)
            vid = self.queue_.pop()
            print('-- downloading:',vid)
            infos = self.downloader_.extract_info(vid)
            filename = self.download_location_ + '/' + ('%05d' % self.downloader_._num_downloads)
            cmd_line = subprocess.list2cmdline(['vlc', '--fullscreen', filename])
            print('-- run player:', cmd_line)
            p = subprocess.Popen(['vlc', '--fullscreen', filename])

    #def rowCount(self):
        #return len(self.queue_)

    #def columnCount(self):
        #return 3

    #def data(self, index, role):
        #vid = self.queue_[index.row()]
        #if (index.column()==0):
            #return vid['title']
        ##if (index.column()==1):
            ##return vid['title']
        #return ''


class DownloadManagerView(QTableView):
    def __init__(self):
        super(DownloadManagerView, self).__init__()
        dlm = DownloadManagerFactory().GetInstance()
        self.setModel(dlm)

    def sizeHint(self):
        return QSize(256,200)


class ThumbnailCache(object):
    def __init__(self, height=96, ratio=16./9, defaultBackground='black'):
        super(ThumbnailCache, self).__init__()
        self.cache_ = {}
        self.height_ = height
        self.ratio_ = ratio
        self.defaultBackground_ = defaultBackground
    def __call__(self, image_url):
        if not image_url in self.cache_:

            try:
                filename, headers = urllib.request.urlretrieve(image_url)
                srcImage = QImage(filename)
            except:
                srcImage = QImage(self.ratio_*self.height_, self.height_, QImage.Format.Format_RGB32)
                srcImage.fill(QColor(self.defaultBackground_))

            # column images
            if srcImage.height() > 4*srcImage.width():
                srcImage = srcImage.copy(0, 0, srcImage.width(), int(srcImage.width()/self.ratio_))

            # black borders
            ratio = 1.0*srcImage.width()/srcImage.height()
            if ratio > self.ratio_:
                srcImage = srcImage.scaledToWidth(self.height_*self.ratio_)
                destPos = QPoint(0, (self.height_-srcImage.height())//2)
            else:
                srcImage = srcImage.scaledToHeight(self.height_)
                destPos = QPoint(int(self.ratio_*self.height_-srcImage.width())//2, 0)
            destImage = QImage(self.ratio_*self.height_, self.height_, QImage.Format.Format_RGB32)
            painter = QPainter(destImage)
            painter.fillRect(painter.window (), QColor(self.defaultBackground_))
            painter.drawImage(destPos, srcImage)
            painter.end()

            self.cache_[image_url] = destImage
        return self.cache_[image_url]

class PlaylistItemDelegate(QItemDelegate):
    queueVid = Signal(str)

    def __init__(self, height=96, ratio=16./9):
        super(PlaylistItemDelegate, self).__init__()
        self.height_ = height
        self.ratio_ = ratio
        dlm = DownloadManagerFactory().GetInstance()
        self.queueVid.connect(dlm.add)

    def paint(self, painter, option, index):
        infos = index.data()

        if 'qimage' in infos:
            image = infos['qimage']
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


class CacheWorker(QObject):
    finished = Signal()

    def __init__(self, model):
        super(CacheWorker, self).__init__() 
        self.model_ = model

    @Slot()
    def doWork(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = dict((executor.submit(self.model_.populateCache, i), i)
                                for i in range(len(self.model_.vids_)))

            for future in concurrent.futures.as_completed(future_to_url):
                i = future_to_url[future]
                url = self.model_.vids_[i]['thumbnail']
                if future.exception() is not None:
                    print('%s generated an exception: %s' % (url,
                                                            future.exception()))
        self.finished.emit()

class PlaylistModel(QAbstractListModel):
    def __init__(self):
        super(PlaylistModel, self).__init__()
        self.downloader_ = YoutubeDL()
        self.extractors_ = extractor.gen_extractors()
        for ext in self.extractors_:
            ext.set_downloader(self.downloader_)
        self.vids_ = []
        self.image_cache_ = ThumbnailCache()

    def run_extractor(self, ext, search_text):
        if not search_text:
            return ext._get_homepage_results()
        else:
            return ext._get_n_results(search_text, 10)

    def update(self, extractor_name=None, search_text=None):
        print('-- update search_text=', search_text, 'extractor_name=', extractor_name)
        current_extractors = self.extractors_
        if extractor_name:
            for ext in current_extractors:
                if ext.IE_NAME == extractor_name:
                    current_extractors = [ext]
                    break
        self.vids_ = []
        #for ext in current_extractors:
            #try:
                #vids = self.run_extractor(ext,search_text)
                #self.vids_.extend(vids)
            #except:
                #print('-- extraction failed for', ext.IE_NAME)
                #pass


        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            future_to_url = dict((executor.submit(self.run_extractor, ext, search_text), ext)
                                for ext in current_extractors)

            for future in concurrent.futures.as_completed(future_to_url):
                ext = future_to_url[future]
                if future.exception() is not None:
                    print('%s generated an exception: %s' % (ext.IE_NAME,
                                                            future.exception()))
                else:
                    vids = future.result()
                    print(ext.IE_NAME, 'returned ', len(vids))
                    #vids = future.result()
                    self.vids_.extend(vids)


        print('--', len(self.vids_), 'preliminary results')
        if search_text and len(self.vids_)>100 and whoosh_available:
            schema = Schema(title=TEXT(stored=True), vid=STORED)
            if not os.path.exists("index"):
                os.mkdir("index")
            ix = create_in("index", schema)
            writer = ix.writer()
            for vid in self.vids_:
                writer.add_document(title=vid['title'], vid=vid)
            writer.commit()

            with ix.searcher() as searcher:
                qp = QueryParser('title', schema=ix.schema)
                query = qp.parse(search_text)
                results = searcher.search(query, limit=100)
                print('--', results)
                if len(results)>0:
                    self.vids_ = []
                    for result in results:
                        print('--', result)
                        self.vids_.append(result['vid'])

        self.worker_ = CacheWorker(self)
        self.workerThread_ = QThread()
        self.worker_.moveToThread(self.workerThread_)
        self.workerThread_.started.connect(self.worker_.doWork)
        self.worker_.finished.connect(self.workerThread_.quit)
        self.workerThread_.finished.connect(self.worker_.deleteLater)
        self.workerThread_.finished.connect(self.workerThread_.deleteLater)
        self.workerThread_.start()
        self.modelReset.emit()

    def rowCount(self, parent):
        return len(self.vids_)

    def populateCache(self, index):
        vid = self.vids_[index]
        if not 'qimage' in vid:
            vid['qimage'] = self.image_cache_(vid['thumbnail'])

    def data(self, index, role):
        self.populateCache(index.row())
        vid = self.vids_[index.row()]
        return vid

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
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setDefaultSectionSize(160)
        self.verticalHeader().setResizeMode(QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(64)
        cols = 2
        rows = len(extractors)/cols
        self.setColumnCount(cols)
        self.setRowCount(rows)
        cache = ThumbnailCache(64, 1., defaultBackground='white')
        self.setIconSize(QSize(100, 100))
        for i in range(len(extractors)):
            item = QTableWidgetItem()
            icon_url = extractors[i]._get_icon_url()
            image = cache(icon_url)
            icon = QIcon(QPixmap.fromImage(image))
            item.setIcon(icon)
            item.setSizeHint(QSize(100, 100))
            item.setText(extractors[i].IE_NAME)
            self.setItem (i/cols, i%cols, item)
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
        search_text = self.searchBar_.text()
        index = self.siteBar_.currentIndex()
        extractor_name = self.siteBar_.itemData(index)
        self.playlist_.update(search_text=search_text, extractor_name=extractor_name)

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
        siteLayout = QHBoxLayout()
        self.siteBar_ = QComboBox()
        siteLayout.addWidget(QLabel('site:'))
        siteLayout.addWidget(self.siteBar_)
        self.siteBar_.addItem('All', None)
        for ext in extractors:
            self.siteBar_.addItem(ext.IE_NAME, ext.IE_NAME)
        siteLayout.addStretch()
        searchLayout.addLayout(siteLayout)
        barLayout = QHBoxLayout()
        self.searchBar_ = QLineEdit()
        barLayout.addWidget(self.searchBar_)
        okButton = QPushButton('Ok')
        barLayout.addWidget(okButton)
        barLayout.addStretch()
        okButton.clicked.connect(self.onSearch)
        searchLayout.addLayout(barLayout)
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

        dock = QDockWidget(self)
        #dock.setAllowedAreas(LeftDockWidgetArea | RightDockWidgetArea)
        downloadWidget = DownloadManagerView()
        dock.setWidget(downloadWidget)
        self.addDockWidget(Qt.BottomDockWidgetArea, dock)


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
