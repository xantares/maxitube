
# Allow access to command-line arguments
import sys
# Import the core and GUI elements of Qt

from PySide.QtCore import *
from PySide.QtGui import *

    #from PyQt4.QtCore import *
    #from PyQt4.QtGui import *

from youtube_dl import YoutubeDL
import maxitube.extractor as extractor
#from urllib.request import urlretrieve
import urllib
import tempfile
import subprocess
import os
import signal
import concurrent.futures
import math as m
from urllib.error import URLError
from youtube_dl.utils import DownloadError

try:
    from whoosh.fields import Schema, TEXT, ID, STORED
    from whoosh.index import create_in
    from whoosh import scoring
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
    def __init__(self, manager, vid):
        super(DownloadWorker, self).__init__()
        self.manager_ = manager
        self.vid_ = vid

    def doWork(self):
        self.manager_.start_download(self.vid_)
        self.finished.emit()

class DownloadManager(QAbstractTableModel):
    #requestUpdateLine = Signal(int, str, str)

    def __init__(self):
        super(DownloadManager, self).__init__()
        self.initialized_ = True
        self.downloader_ = YoutubeDL()
        self.reader_ = 'vlc'
        self.downloader_.add_progress_hook(self.progress)
        self.workerThreads_ = []
        self.vids_ = []
        self._max_simulateous_downloads = 1
        self.download_location_ = tempfile.gettempdir()+'/maxitube'
        self.downloader_.params['outtmpl'] = self.download_location_+'/%(autonumber)s'
        self.downloader_.params['noprogress'] = False
        #self.setHorizontalHeaderLabels(['name', "status", "progress", "file"])
        #self.requestUpdateLine.connect(self.updateLine)

    @Slot(str)
    def add(self, vid):
        #print('--add',vid)
        vid['status'] = 'queued'
        index = len(self.vids_)-1
        self.beginInsertRows(QModelIndex(), index, index)
        self.vids_.append(vid)
        self.endInsertRows()
        #self.insertRows(self.rowCount(), 1)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))
        #url = vid['url']
        #item = QStandardItem(url)
        #self.appendRow([item, QStandardItem('queued'), QStandardItem(''), QStandardItem('')])
        self.update()

    def columnCount(self, parent=QModelIndex()):
        return 4

    def rowCount(self, parent=QModelIndex()):
        return len(self.vids_)

    def data(self, index, role):
        data = None
        if role == Qt.DisplayRole:
            row = index.row()
            vid = self.vids_[row]
            section = index.column()
            if section == 0:
                data = vid['url']
            elif section == 1 and 'status' in vid:
                data = vid['status']
            elif section == 2 and '_percent_str' in vid:
                data = vid['_percent_str']
            elif section == 3 and 'filename' in vid:
                data = vid['filename']
        return data

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        data = None
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section == 0:
                data = 'Url'
            elif section == 1:
                data = 'Status'
            elif section == 2:
                data = 'Progress'
            elif section == 3:
                data = 'File'
        return data

    def update(self):
        simulateous_downloads = 0
        first_queued = None
        # FIXME iterate over self.vids_
        for index in range(self.rowCount()):
            vid = self.vids_[index]
            status = vid['status']
            if status == 'downloading':
                simulateous_downloads += 1
            elif status == 'queued':
                if not first_queued:
                    first_queued = vid

        if first_queued and (simulateous_downloads < self._max_simulateous_downloads):
            self.worker_ = DownloadWorker(self, first_queued)
            self.worker_.finished.connect(self.update)
            thread = QThread()
            self.worker_.moveToThread(thread)
            thread.started.connect(self.worker_.doWork)
            self.worker_.finished.connect(thread.quit)
            thread.finished.connect(self.worker_.deleteLater)
            #self.workerThread_.finished.connect(self.workerThread_.deleteLater)
            thread.start()
            self.workerThreads_.append(thread)

    def progress(self, dl_infos):
        filename = None
        if 'tmpfilename' in dl_infos:
            filename = dl_infos['tmpfilename']
        elif 'filename' in dl_infos:
            filename = dl_infos['filename']
        if filename:
            index = int(os.path.splitext(os.path.basename(filename))[0])-1
            self.vids_[index]['filename'] = filename
            self.vids_[index]['status'] = dl_infos['status']
            if '_percent_str' in dl_infos:
                self.vids_[index]['_percent_str']= dl_infos['_percent_str']
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))

    def start_download(self, vid):
        self.downloader_.add_progress_hook(self.progress)
        url = vid['url']
        print('-- downloading:',url)
        try:
            infos = self.downloader_.extract_info(url)
        except DownloadError:
            for index in range(len(self.vids_)):
                if url == self.vids_[index]['url']:
                    self.vids_[index]['status'] = 'error'
                    self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))

class DownloadManagerView(QTableView):
    def __init__(self):
        super(DownloadManagerView, self).__init__()
        dlm = DownloadManagerFactory().GetInstance()
        self.setModel(dlm)
        self.setItemDelegate(DownloadManagerItemDelegate())

    def sizeHint(self):
        return QSize(256,200)

class DownloadManagerItemDelegate(QItemDelegate):
    def __init__(self):
        super(DownloadManagerItemDelegate, self).__init__()

    def editorEvent(self, event, model, option, index):
        if (event.type() == QEvent.MouseButtonPress):
            dlm = DownloadManagerFactory().GetInstance()
            vid = dlm.vids_[index.row()]
            if 'status' in vid:
                status = vid['status']
                filename = None
                if status == 'finished':
                    #filename = self.download_location_ + '/' + ('%05d' % self.downloader_._num_downloads)
                    filename = vid['filename']
                elif status == 'downloading':
                    filename = vid['filename']
                if not filename is None:
                    cmd_line = subprocess.list2cmdline(['vlc', '--fullscreen', filename])
                    print('-- run player:', cmd_line)
                    p = subprocess.Popen(['vlc', '--fullscreen', filename])
        return False


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
                print ('-- could not get',  image_url)
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
    queueVid = Signal(dict)

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

        if 'url' in infos:
            url = infos['url']
            painter.drawText(option.rect.topLeft().x()+int(128+self.height_), option.rect.topLeft().y()+32, url)

        if 'upload_date' in infos:
            upload_date = infos['upload_date']
            painter.drawText(option.rect.topLeft().x()+int(128+self.height_), option.rect.topLeft().y()+40, upload_date)

    def sizeHint(self, option, index):
        return QSize(int(2*self.ratio_*self.height_), self.height_)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QEvent.MouseButtonPress):
            self.queueVid.emit(index.data())
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
                if i < len(self.model_.vids_):
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
        self.workerThreads_ = []

    def run_extractor(self, ext, search_text):
        return ext._get_n_results(search_text, 100)

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
        if search_text and len(self.vids_)>250 and whoosh_available:
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
                print('--', len(results), 'final results')
                if len(results)>10:
                    self.vids_ = []
                    for result in results:
                        #print('--', result)
                        self.vids_.append(result['vid'])

        self.worker_ = CacheWorker(self)
        thread = QThread()
        self.worker_.moveToThread(thread)
        thread.started.connect(self.worker_.doWork)
        self.worker_.finished.connect(thread.quit)
        #self.workerThread_.finished.connect(self.worker_.deleteLater)
        #self.workerThread_.finished.connect(self.workerThread_.deleteLater)
        thread.start()
        self.workerThreads_.append(thread)
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
        rows = m.ceil(1.0*len(extractors)/cols)
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

if __name__ == '__main__':
    import maxitube
    maxitube.main()