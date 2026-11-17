"""Release regressions for catalog completeness, Unicode, preferences and links."""
import ast
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from string import Formatter
from unittest.mock import patch

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QTextLayout
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cropper.gui import MainWindow, SOFTWARE_URL
from cropper.discovery import Discovery
from cropper.processing import Result
from cropper.i18n import LANGUAGES, TRANSLATIONS, normalize_language, tr
from cropper.splash import StartupSplash
from cropper.startup import initial_language


ROOT = Path(__file__).resolve().parent.parent


class CatalogTests(unittest.TestCase):
    def test_complete_keys_and_matching_format_fields(self):
        def fields(text):
            return sorted(field for _, field, _, _ in Formatter().parse(text) if field is not None)
        baseline = TRANSLATIONS['en']
        self.assertEqual(set(LANGUAGES), set(TRANSLATIONS))
        for language, catalog in TRANSLATIONS.items():
            self.assertEqual(set(catalog), set(baseline), language)
            for key, text in catalog.items():
                with self.subTest(language=language, key=key):
                    self.assertTrue(text.strip())
                    self.assertNotIn('\ufffd', text)
                    self.assertEqual(fields(text), fields(baseline[key]))

    def test_catalog_has_no_duplicate_literal_keys(self):
        tree = ast.parse((ROOT / 'cropper/i18n.py').read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = [key.value for key in node.keys if isinstance(key, ast.Constant)]
                self.assertEqual(len(keys), len(set(keys)))

    def test_normalization_preserves_existing_preferences_and_accepts_locales(self):
        for raw, expected in (('en-US', 'en'), ('fr_FR', 'fr'), ('jp', 'ja'),
                              ('ja_JP', 'ja'), ('zh_CN', 'zh-CN'), ('ru_RU', 'ru-RU'),
                              ('de_DE', 'de-DE'), ('Chinese (Simplified)_China', 'zh-CN'),
                              ('Russian_Russia', 'ru-RU'), ('German_Germany', 'de-DE'),
                              ('unknown', 'en'), (None, 'en')):
            self.assertEqual(normalize_language(raw), expected)
        with patch.dict(TRANSLATIONS['de-DE'], {}, clear=True):
            self.assertEqual(tr('process', 'de-DE'), 'Process')

    def test_startup_uses_same_language_without_loading_image_codecs(self):
        for language in LANGUAGES:
            with patch('cropper.startup.QSettings') as settings:
                settings.return_value.value.return_value = language
                self.assertEqual(initial_language(), language)
        result = subprocess.run([sys.executable, '-c',
            "import sys; from cropper.i18n import tr; tr('starting', 'zh-CN'); "
            "assert 'PIL.Image' not in sys.modules and 'pillow_heif' not in sys.modules"],
            cwd=ROOT, capture_output=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stderr)


class LocalizedGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = str(Path(self.temp.name) / 'preferences.ini')
        self.settings = QSettings(self.path, QSettings.Format.IniFormat)
        self.window = MainWindow(language='en', settings=self.settings)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        self.window.close()
        self.temp.cleanup()

    def test_switching_and_restart_preserve_all_six_languages(self):
        window = self.window
        self.assertEqual(window.language_combo.count(), 6)
        window.language_combo.setCurrentIndex(window.language_combo.findData('fr'))
        for language, name in LANGUAGES.items():
            with self.subTest(language=language):
                index = window.language_combo.findData(language)
                self.assertEqual(window.language_combo.itemText(index), name)
                window.language_combo.setCurrentIndex(index)
                self.assertEqual(window.process.text(), tr('process', language))
                self.assertEqual(window.footer_software.text(), tr('more_software', language))
                self.assertEqual(window.drop.hint.text(), tr('drop_hint', language))
                self.assertEqual(window.preview.reset_crop.toolTip(), tr('reset_crop_tip', language))
                self.settings.sync()
                restarted = MainWindow(settings=QSettings(self.path, QSettings.Format.IniFormat))
                self.assertEqual(restarted.language, language)
                self.assertEqual(restarted.process.text(), tr('process', language))
                restarted.close()
                splash = StartupSplash(language)
                splash.complete_branding()
                self.assertEqual(splash.windowTitle(), tr('starting', language))
                splash.close()

    def test_footer_activation_uses_default_browser_and_handles_failures(self):
        with patch('cropper.gui.QDesktopServices.openUrl', return_value=True) as browser:
            for language in LANGUAGES:
                self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            browser.assert_not_called()
            self.window.footer_software.setFocus()
            QTest.keyClick(self.window.footer_software, Qt.Key.Key_Return)
            self.assertEqual(browser.call_args.args[0].toString(), SOFTWARE_URL)
            self.assertEqual(SOFTWARE_URL, 'https://www.matthieutuffet.com/software/')
            browser.reset_mock()
            QTest.mouseClick(self.window.footer_software, Qt.MouseButton.LeftButton)
            browser.assert_called_once()
        for outcome in (False, OSError('no browser'), RuntimeError('launch failed')):
            with patch('cropper.gui.QDesktopServices.openUrl') as browser:
                if isinstance(outcome, Exception):
                    browser.side_effect = outcome
                else:
                    browser.return_value = outcome
                self.assertFalse(self.window.open_software())
                self.assertTrue(self.window.isVisible())

    def test_all_themes_layout_and_chinese_cyrillic_glyphs(self):
        window = self.window
        for language in LANGUAGES:
            window.language_combo.setCurrentIndex(window.language_combo.findData(language))
            for theme in ('dark', 'light', 'classic'):
                with self.subTest(language=language, theme=theme):
                    window.theme_combo.setCurrentIndex(window.theme_combo.findData(theme))
                    window.resize(920, 760)
                    for _ in range(4):
                        self.app.processEvents()
                    panel = window.preview
                    self.assertLess(panel.canvas.geometry().bottom(), panel.details.geometry().top())
                    for widget in (window.footer_software, window.preview.reset_crop,
                                   window.recursive, window.open_when_finished, window.drop.title,
                                   window.process):
                        self.assertGreaterEqual(widget.width(), widget.sizeHint().width(), widget.text())
                    if language in ('zh-CN', 'ru-RU'):
                        # QTextLayout resolves Qt's actual fallback font per glyph run.
                        for key, text in TRANSLATIONS[language].items():
                            layout = QTextLayout(text.replace('\n', ' '), window.process.font())
                            layout.beginLayout()
                            line = layout.createLine()
                            line.setLineWidth(100000)
                            layout.endLayout()
                            runs = layout.glyphRuns()
                            self.assertTrue(runs, key)
                            for run in runs:
                                self.assertNotIn(0, run.glyphIndexes(), (language, theme, key))

    def test_qt_standard_dialog_translations_are_loaded(self):
        for language in ('fr', 'ja', 'zh-CN', 'ru-RU', 'de-DE'):
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            self.assertFalse(self.app._cropperio_translator.isEmpty(), language)

    def test_existing_result_rows_switch_language_without_losing_paths(self):
        source = Path(self.temp.name) / '中文-Русский.png'
        self.window.on_discovered(Discovery(files=[source]))
        item = self.window.table.item(0, 1)
        for language in LANGUAGES:
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            self.assertEqual(item.text(), tr('item_ready', language))
        self.window.on_result(0, Result(source, error='codec details'))
        for language in LANGUAGES:
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            self.assertEqual(item.text(), tr('error', language))
            self.assertEqual(item.toolTip(), 'codec details')
        output = source.with_name('output.png')
        self.window.on_result(0, Result(source, output, (80, 60), (40, 30),
                                        cropped_size=(80, 60)))
        for language in LANGUAGES:
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            self.assertEqual(item.text(), '40 × 30 • ' + ', '.join(
                tr(key, language) for key in ('no_crop', 'resized')))
            self.assertEqual(item.toolTip(), str(output))


if __name__ == '__main__':
    unittest.main()
