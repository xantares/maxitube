import sys
import signal
from PySide.QtGui import QApplication
from maxitube.__main__ import MainWindow

def _real_main(argv=None):
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

def main(argv=None):
    try:
        _real_main(argv)
    except KeyboardInterrupt:
        sys.exit('\nERROR: Interrupted by user')

__all__ = ['main']
