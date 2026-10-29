"""Show the splash first, import the application, then finish as soon as ready."""
import json
import sys
import time
from pathlib import Path

from PySide6.QtCore import QLocale, QSettings, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from .branding import TAGLINE, DESCRIPTION
from .resources import resource_path
from .splash import StartupSplash
from .version import __version__


def initial_language():
    current = QSettings('papagori', 'Cropperio').value('language', '')
    legacy = QSettings('PhotoCrop', 'PhotoCropV2').value('language', '')
    value = str(current or legacy or QLocale.system().name()).lower()
    return 'ja' if value.startswith(('ja', 'jp')) else 'fr' if value.startswith('fr') else 'en'


def construct_window(splash, factory):
    """A failed import/initialization must never leave an orphan splash."""
    try:
        window = factory()
        window.show()
        splash.finish(window)
        return window
    except Exception:
        splash.close()
        raise


def run(startup_report=None):
    started = time.perf_counter()
    phases = {}

    def mark(name):
        phases[name] = round((time.perf_counter() - started) * 1000, 2)

    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName('Cropperio')
    app.setApplicationDisplayName('Cropperio')
    app.setApplicationVersion(__version__)
    app.setOrganizationName('papagori')
    app.setStyle('Fusion')
    mark('qt_ready')
    deferred = all(name not in sys.modules for name in ('cropper.gui', 'PIL.Image', 'pillow_heif'))
    splash = StartupSplash(initial_language())
    splash.show()
    app.processEvents()
    mark('splash_visible')
    splash.complete_branding()
    app.processEvents()
    mark('branding_ready')
    report_path = Path(startup_report).resolve() if startup_report else None
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        splash.grab().save(str(report_path.with_name(report_path.stem + '-splash.png')))
    try:
        from .gui import MainWindow
        mark('gui_imported')
        app.setWindowIcon(QIcon(str(resource_path('assets/cropperio.ico'))))
        window = construct_window(splash, MainWindow)
        mark('window_ready')
    except Exception:
        splash.close()
        raise

    if report_path:
        # Opt-in startup probe follows the normal launch path. No timer or
        # artificial minimum duration is used for normal application startup.
        def finish_probe():
            app.processEvents()
            passed = deferred and window.isVisible() and not splash.isVisible()
            report = {'passed': passed, 'version': __version__,
                      'frozen': bool(getattr(sys, 'frozen', False)),
                      'imports_deferred': deferred, 'splash_closed': not splash.isVisible(),
                      'window_ready': window.isVisible(), 'phases_ms': phases,
                      'tagline': TAGLINE, 'description': DESCRIPTION}
            window.grab().save(str(report_path.with_suffix('.png')))
            report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
            window.close()
            app.exit(0 if passed else 1)
        QTimer.singleShot(0, finish_probe)
    return app.exec()
