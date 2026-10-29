"""Resolution-independent wand drawn with Qt paths, without font glyphs."""
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def wand_icon():
    icon = QIcon()
    for size in (16, 24, 32, 48, 64):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.scale(size / 24, size / 24)
        painter.setPen(QPen(QColor('#ffffff'), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(4, 20), QPointF(16, 8))
        painter.setPen(QPen(QColor('#fde68a'), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(14, 10), QPointF(17, 7))
        painter.setPen(QPen(QColor('#fde68a'), 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        for x, y, radius in ((7, 5, 2), (20, 13, 2), (18, 3, 1)):
            painter.drawLine(QPointF(x - radius, y), QPointF(x + radius, y))
            painter.drawLine(QPointF(x, y - radius), QPointF(x, y + radius))
        painter.end()
        icon.addPixmap(pixmap)
    return icon
