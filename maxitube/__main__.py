
# Allow access to command-line arguments
import sys
# Import the core and GUI elements of Qt
from PySide.QtCore import *
from PySide.QtGui import *
import extractor

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
    enginesTab = QTabWidget()
    searchLayout.addWidget(enginesTab)
    mainWidget.show()

    #qt_app.setMainWidget(mainWidget)
    # Run the application's event loop
    qt_app.exec_()
main()