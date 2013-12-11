import sys
import webbrowser
import requests

from PySide import QtGui, QtCore

SHUTDOWN_AFTER = 4
RUNNING_CHECK = 3

ICON_UPDATE = 5

class SystemTrayIcon(QtGui.QSystemTrayIcon):
    def __init__(self, base_addr, parent=None):
        QtGui.QSystemTrayIcon.__init__(self, self._make_icon(1), parent)

        self._base_addr = base_addr

        self.activated.connect(self._on_click)
        menu = QtGui.QMenu(parent)

        exitAction = QtGui.QAction("&Exit", self, triggered=self._on_exit_clicked)
        menu.addAction(exitAction)

        self.setContextMenu(menu)

        self._icon_timer = QtCore.QTimer()
        self._icon_timer.timeout.connect(self._update_icon)
        self._icon_timer.start(ICON_UPDATE * 1000)

        self._shutdown_timer = QtCore.QTimer()
        self._shutdown_timer.timeout.connect(self._check_shutdown)
        self._shutdown_timer.start(RUNNING_CHECK * 1000)

        self._shutdown_ticker = 0

    def _on_exit_clicked(self):
        requests.get('%s/shutdown' % self._base_addr)
        QtGui.qApp.quit()

    def _check_shutdown(self):
        try:
            requests.get('%s/status' % self._base_addr)
            self._shutdown_ticker = 0
        except requests.exceptions.ConnectionError:
            self._shutdown_ticker += 1

        if self._shutdown_ticker > SHUTDOWN_AFTER/RUNNING_CHECK:
            QtGui.qApp.quit()

    def _update_icon(self):
        total = 0.0
        current = 0.0
        try:
            req = requests.get('%s/downloading' % self._base_addr)
            data = req.json()

            for d in data['active_downloads']:
                current += d['total_downloaded_kb']
                total += d['file_size_kb']
        except requests.exceptions.ConnectionError:
            pass

        try:
            self.setIcon(QtGui.QIcon(self._make_icon(current/total)))
        except ZeroDivisionError:
            self.setIcon(QtGui.QIcon(self._make_icon(1)))

    def _on_click(self, reason):
        if reason == 3:
            webbrowser.open(self._base_addr)

    def _make_icon(self, percent_done):
        percent_done = min(1, max(0, percent_done))

        size = 20
        green_size = int(size * percent_done)

        pixmap = QtGui.QPixmap(20, 20)
        pixmap.fill(QtGui.QColor('red'))

        paint = QtGui.QPainter(pixmap)
        paint.setPen(QtGui.QColor('green'))
        paint.fillRect(0,0, 20, green_size, QtGui.QColor('green'))

        return pixmap

def system_tray_app(base_addr):
    app = QtGui.QApplication(sys.argv)

    w = QtGui.QWidget()

    trayIcon = SystemTrayIcon(base_addr, w)

    trayIcon.show()
    sys.exit(app.exec_())
