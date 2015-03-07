
# Allow access to command-line arguments
import sys
# Import the core and GUI elements of Qt

from PySide import QtCore
from PySide import QtGui

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

try:
    import vlc
    vlc_available = True
except:
    vlc_available = False


class DownloadManagerFactory:
    instance_ = None

    def __init__(self):
        if not self.__class__.instance_:
            self.__class__.instance_ = DownloadManager()

    def GetInstance(self):
        return self.__class__.instance_

class DownloadWorker(QtCore.QObject):
    finished = QtCore.Signal()
    def __init__(self, manager, vid):
        super(DownloadWorker, self).__init__()
        self.manager_ = manager
        self.vid_ = vid

    def doWork(self):
        self.manager_.start_download(self.vid_)
        self.finished.emit()

class DownloadManager(QtCore.QAbstractTableModel):
    playVid = QtCore.Signal(str)

    def __init__(self):
        super(DownloadManager, self).__init__()
        self.initialized_ = True
        self.downloader_ = YoutubeDL()
        self.downloader_.add_progress_hook(self.progress)
        self.workerThreads_ = []
        self.vids_ = []
        self._max_simulateous_downloads = 1
        self.download_location_ = tempfile.gettempdir()+'/maxitube'
        self.downloader_.params['outtmpl'] = self.download_location_+'/%(autonumber)s'
        self.downloader_.params['noprogress'] = False
        #self.setHorizontalHeaderLabels(['name', "status", "progress", "file"])
        #self.requestUpdateLine.connect(self.updateLine)

    @QtCore.Slot(str)
    def add(self, vid):
        for vid2 in self.vids_:
            if vid['url'] == vid2['url']:
                return
        vid['status'] = 'queued'
        index = len(self.vids_)-1
        self.beginInsertRows(QtCore.QModelIndex(), index, index)
        self.vids_.append(vid)
        self.endInsertRows()
        #self.insertRows(self.rowCount(), 1)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))
        #url = vid['url']
        #item = QStandardItem(url)
        #self.appendRow([item, QStandardItem('queued'), QStandardItem(''), QStandardItem('')])
        self.update()

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 4

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.vids_)

    def data(self, index, role):
        data = None
        if role == QtCore.Qt.DisplayRole:
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

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        data = None
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
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
        first_index = None
        # FIXME iterate over self.vids_
        for index in range(self.rowCount()):
            vid = self.vids_[index]
            status = vid['status']
            if status == 'downloading':
                simulateous_downloads += 1
            elif status == 'queued':
                if not first_queued:
                    first_queued = vid
                    first_index = index

        if first_queued and (simulateous_downloads < self._max_simulateous_downloads):
            self.vids_[first_index]['status']='downloading'
            self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount()-1, self.columnCount()-1))
            self.worker_ = DownloadWorker(self, first_queued)
            self.worker_.finished.connect(self.update)
            thread = QtCore.QThread()
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

class DownloadManagerView(QtGui.QTableView):
    def __init__(self):
        super(DownloadManagerView, self).__init__()
        dlm = DownloadManagerFactory().GetInstance()
        self.setModel(dlm)
        self.setItemDelegate(DownloadManagerItemDelegate())

    def sizeHint(self):
        return QtCore.QSize(256,200)

class DownloadManagerItemDelegate(QtGui.QItemDelegate):
    def __init__(self):
        super(DownloadManagerItemDelegate, self).__init__()

    def editorEvent(self, event, model, option, index):
        if (event.type() == QtCore.QEvent.MouseButtonPress):
            dlm = DownloadManagerFactory().GetInstance()
            vid = dlm.vids_[index.row()]
            if 'status' in vid:
                status = vid['status']
                filename = None
                if status == 'finished':
                    dlm.vids_[index.row()]['progress'] = '100%'
                    #filename = self.download_location_ + '/' + ('%05d' % self.downloader_._num_downloads)
                    filename = vid['filename']
                elif status == 'downloading':
                    filename = vid.get('filename')
                if not filename is None:
                    dlm.playVid.emit(filename)

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
                srcImage = QtGui.QImage(filename)
            except:
                print ('-- could not get',  image_url)
                srcImage = QtGui.QImage(self.ratio_*self.height_, self.height_, QtGui.QImage.Format.Format_RGB32)
                srcImage.fill(QtGui.QColor(self.defaultBackground_))

            # column images
            if srcImage.height() > 4*srcImage.width():
                srcImage = srcImage.copy(0, 0, srcImage.width(), int(srcImage.width()/self.ratio_))

            # black borders
            ratio = 1.0*srcImage.width()/srcImage.height()
            if ratio > self.ratio_:
                srcImage = srcImage.scaledToWidth(self.height_*self.ratio_)
                destPos = QtCore.QPoint(0, (self.height_-srcImage.height())//2)
            else:
                srcImage = srcImage.scaledToHeight(self.height_)
                destPos = QtCore.QPoint(int(self.ratio_*self.height_-srcImage.width())//2, 0)
            destImage = QtGui.QImage(self.ratio_*self.height_, self.height_, QtGui.QImage.Format.Format_RGB32)
            painter = QtGui.QPainter(destImage)
            painter.fillRect(painter.window (), QtGui.QColor(self.defaultBackground_))
            painter.drawImage(destPos, srcImage)
            painter.end()

            self.cache_[image_url] = destImage
        return self.cache_[image_url]

class PlaylistItemDelegate(QtGui.QItemDelegate):
    queueVid = QtCore.Signal(dict)

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
        return QtCore.QSize(int(2*self.ratio_*self.height_), self.height_)

    def editorEvent(self, event, model, option, index):
        if (event.type() == QtCore.QEvent.MouseButtonPress):
            self.queueVid.emit(index.data())
            return True
        return False


class CacheWorker(QtCore.QObject):
    finished = QtCore.Signal()

    def __init__(self, model):
        super(CacheWorker, self).__init__() 
        self.model_ = model

    @QtCore.Slot()
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

class PlaylistModel(QtCore.QAbstractListModel):
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
        thread = QtCore.QThread()
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

class PlaylistView(QtGui.QListView):
    def __init__(self):
        super(PlaylistView, self).__init__()
        self.setItemDelegate(PlaylistItemDelegate())

    def sizeHint(self):
        return QtCore.QSize(256,800)


class SiteTable(QtGui.QTableWidget):
    requestBrowse = QtCore.Signal(str)

    def __init__(self, extractors):
        super(SiteTable, self).__init__()
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setVisible(False)
        self.horizontalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.horizontalHeader().setDefaultSectionSize(160)
        self.verticalHeader().setResizeMode(QtGui.QHeaderView.Fixed)
        self.verticalHeader().setDefaultSectionSize(64)
        cols = 2
        rows = m.ceil(1.0*len(extractors)/cols)
        self.setColumnCount(cols)
        self.setRowCount(rows)
        cache = ThumbnailCache(64, 1., defaultBackground='white')
        self.setIconSize(QtCore.QSize(100, 100))
        for i in range(len(extractors)):
            item = QtGui.QTableWidgetItem()
            icon_url = extractors[i]._get_icon_url()
            image = cache(icon_url)
            icon = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
            item.setIcon(icon)
            item.setSizeHint(QtCore.QSize(100, 100))
            item.setText(extractors[i].IE_NAME)
            self.setItem (i/cols, i%cols, item)
        #connect(self, SIGNAL(cellClicked(int,int)), this, SLOT(previousWeek()));
        self.cellClicked.connect(self.onCellClick) 

    @QtCore.Slot(int, int)
    def onCellClick(self, row, col):
        extractor_name = self.item(row, col).text()
        self.requestBrowse.emit(extractor_name)

    def sizeHint(self):
        return QtCore.QSize(256,800)


class PlayerWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(PlayerWidget, self).__init__(parent)
        if vlc_available:
            videoLayout = QtGui.QVBoxLayout()
            self.instance = vlc.Instance()
            self.mediaplayer = self.instance.media_player_new()
            # In this widget, the video will be drawn
            if sys.platform == "darwin": # for MacOS
                self.videoframe = QtGui.QMacCocoaViewContainer(0)
            else:
                self.videoframe = QtGui.QFrame(self)
            self.palette = self.videoframe.palette()
            self.palette.setColor (QtGui.QPalette.Window,
                                QtGui.QColor(0,0,0))
            self.videoframe.setPalette(self.palette)
            self.videoframe.setAutoFillBackground(True)

            self.positionslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
            self.positionslider.setToolTip("Position")
            self.positionslider.setMaximum(1000)
            self.positionslider.sliderMoved.connect(self.setPosition)

            self.hbuttonbox = QtGui.QHBoxLayout()
            self.playbutton = QtGui.QPushButton("Play")
            self.hbuttonbox.addWidget(self.playbutton)
            self.playbutton.clicked.connect(self.PlayPause)

            self.stopbutton = QtGui.QPushButton("Stop")
            self.hbuttonbox.addWidget(self.stopbutton)
            self.stopbutton.clicked.connect(self.Stop)

            self.hbuttonbox.addStretch(1)
            self.volumeslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
            self.volumeslider.setMaximum(100)
            self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
            self.volumeslider.setToolTip("Volume")
            self.hbuttonbox.addWidget(self.volumeslider)
            self.volumeslider.valueChanged.connect(self.setVolume)


            self.vboxlayout = QtGui.QVBoxLayout()
            self.vboxlayout.addWidget(self.videoframe)
            self.vboxlayout.addWidget(self.positionslider)
            self.vboxlayout.addLayout(self.hbuttonbox)

            self.setLayout(self.vboxlayout)

    @QtCore.Slot(str)
    def PlayPause(self):
        """Toggle play/pause status
        """
        if vlc_available:
            if self.mediaplayer.is_playing():
                self.mediaplayer.pause()
                self.playbutton.setText("Play")
                self.isPaused = True
            else:
                if self.mediaplayer.play() == -1:
                    self.OpenFile()
                    return
                self.mediaplayer.play()
                self.playbutton.setText("Pause")
                #self.timer.start()
                self.isPaused = False

    @QtCore.Slot()
    def Stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")

    @QtCore.Slot(int)
    def setVolume(self, Volume):
        """Set the volume
        """
        self.mediaplayer.audio_set_volume(Volume)

    @QtCore.Slot(int)
    def setPosition(self, position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)


    @QtCore.Slot(str)
    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        if not filename:
            return

        if vlc_available:
            # create the media
            self.media = self.instance.media_new(filename)
            # put the media in the media player
            self.mediaplayer.set_media(self.media)

            # parse the metadata of the file
            self.media.parse()
            # set the title of the track as window title
            #self.setWindowTitle(self.media.get_meta(0))

            # the media player has to be 'connected' to the QFrame
            # (otherwise a video would be displayed in it's own window)
            # this is platform specific!
            # you have to give the id of the QFrame (or similar object) to
            # vlc, different platforms have different functions for this
            if sys.platform.startswith('linux'): # for Linux using the X Server
                self.mediaplayer.set_xwindow(self.videoframe.winId())
            elif sys.platform == "win32": # for Windows
                self.mediaplayer.set_hwnd(self.videoframe.winId())
            elif sys.platform == "darwin": # for MacOS
                self.mediaplayer.set_nsobject(self.videoframe.winId())
            self.PlayPause()
        else:
            cmd_list = ['vlc', '--fullscreen', filename]
            cmd_line = subprocess.list2cmdline(cmd_list)
            print('-- run player:', cmd_line)
            p = subprocess.Popen(cmd_list)


class MainWindow(QtGui.QMainWindow):
    @QtCore.Slot()
    def onSearch(self):
        search_text = self.searchBar_.text()
        index = self.siteBar_.currentIndex()
        extractor_name = self.siteBar_.itemData(index)
        self.playlist_.update(search_text=search_text, extractor_name=extractor_name)
        self.showResults()

    @QtCore.Slot(str)
    def onBrowse(self, extractor_name):
        self.playlist_.update(extractor_name)
        self.showResults()

    def showResults(self):
        self.panelWidget_.setCurrentIndex(2)

    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle('maxitube')
        self.resize(1024, 768)
        extractors = extractor.gen_extractors()
        ydl = YoutubeDL()
        self.playlist_ = PlaylistModel()
        self.panelWidget_ = QtGui.QTabWidget()
        searchWidget = QtGui.QWidget()
        searchLayout = QtGui.QVBoxLayout()
        siteLayout = QtGui.QHBoxLayout()
        self.siteBar_ = QtGui.QComboBox()
        siteLayout.addWidget(QtGui.QLabel('site:'))
        siteLayout.addWidget(self.siteBar_)
        self.siteBar_.addItem('All', None)
        for ext in extractors:
            self.siteBar_.addItem(ext.IE_NAME, ext.IE_NAME)
        siteLayout.addStretch()
        searchLayout.addLayout(siteLayout)
        barLayout = QtGui.QHBoxLayout()
        self.searchBar_ = QtGui.QLineEdit()
        barLayout.addWidget(self.searchBar_)
        okButton = QtGui.QPushButton('Ok')
        barLayout.addWidget(okButton)
        barLayout.addStretch()
        okButton.clicked.connect(self.onSearch)
        searchLayout.addLayout(barLayout)
        searchLayout.addStretch()
        searchWidget.setLayout(searchLayout)

        browseLayout = QtGui.QVBoxLayout()

        browseLayout.addStretch()
        browseWidget = SiteTable(extractors)
        browseWidget.requestBrowse.connect(self.onBrowse)
        browseWidget.setLayout(browseLayout)


        searchView = PlaylistView()
        searchView.setModel(self.playlist_)

        self.panelWidget_.addTab(browseWidget, 'Browse') 
        self.panelWidget_.addTab(searchWidget, 'Search')
        self.panelWidget_.addTab(searchView, 'Results')

        playerWidget = PlayerWidget()
        dlm = DownloadManagerFactory().GetInstance()
        dlm.playVid.connect(playerWidget.OpenFile)

        mainLayout = QtGui.QHBoxLayout()
        mainLayout.addWidget(self.panelWidget_)
        mainLayout.addWidget(playerWidget)

        #mainLayout.addWidget(searchView)

        mainWidget = QtGui.QWidget()
        mainWidget.setLayout(mainLayout)
        self.setCentralWidget(mainWidget)

        dock = QtGui.QDockWidget(self)
        #dock.setAllowedAreas(LeftDockWidgetArea | RightDockWidgetArea)
        downloadWidget = DownloadManagerView()
        dock.setWidget(downloadWidget)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

if __name__ == '__main__':
    import maxitube
    maxitube.main()