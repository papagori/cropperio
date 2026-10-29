"""Small Qt-only splash, safe to import before Pillow/HEIF/the main window."""
from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from .branding import TAGLINE, DESCRIPTION, STARTING
from .resources import resource_path
from .version import __version__


class StartupSplash(QSplashScreen):
    def __init__(self, language='en'):
        self.language = language if language in STARTING else 'en'
        screen = QApplication.primaryScreen()
        dpr = screen.devicePixelRatio() if screen else 1.0
        self.logical_size = (460, 258)
        pixmap = QPixmap(round(460 * dpr), round(258 * dpr))
        pixmap.setDevicePixelRatio(dpr)
        pixmap.fill(QColor('#101a2b'))
        super().__init__(pixmap, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle('Cropperio startup')
        if screen:
            self.move(screen.availableGeometry().center() - self.rect().center())

    def complete_branding(self):
        pixmap = self.pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, 460, 258)
        gradient.setColorAt(0, QColor('#101a2b'))
        gradient.setColorAt(1, QColor('#193c61'))
        painter.fillRect(QRectF(0, 0, 460, 258), gradient)
        painter.setPen(QColor('#446584'))
        painter.drawRect(QRectF(0.5, 0.5, 459, 257))
        icon = QIcon(str(resource_path('assets/cropperio.ico')))
        logo = icon.pixmap(QSize(52, 52), pixmap.devicePixelRatio())
        painter.drawPixmap(33, 29, logo)
        painter.setFont(QFont('Segoe UI', 25, QFont.Weight.DemiBold))
        painter.setPen(QColor('#ffffff'))
        painter.drawText(QRectF(102, 23, 330, 58), Qt.AlignmentFlag.AlignVCenter, 'Cropperio')
        painter.setFont(QFont('Segoe UI', 13, QFont.Weight.DemiBold))
        painter.setPen(QColor('#badaff'))
        painter.drawText(QRectF(33, 98, 394, 30), Qt.AlignmentFlag.AlignVCenter, TAGLINE)
        painter.setFont(QFont('Segoe UI', 10))
        painter.setPen(QColor('#d2deec'))
        painter.drawText(QRectF(33, 138, 394, 48), Qt.TextFlag.TextWordWrap, DESCRIPTION)
        painter.setFont(QFont('Segoe UI', 9))
        painter.setPen(QColor('#9eb7d1'))
        painter.drawText(QRectF(33, 213, 75, 22), Qt.AlignmentFlag.AlignVCenter, f'v{__version__}')
        painter.drawText(QRectF(115, 213, 312, 22),
                         Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                         STARTING[self.language])
        painter.end()
        self.setPixmap(pixmap)
        self.repaint()
