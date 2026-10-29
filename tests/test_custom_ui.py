import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QValidator
from PySide6.QtWidgets import QApplication, QStyle

from cropper.branding import TAGLINE, DESCRIPTION, STARTING
from cropper.classic_icons import classic_icon
from cropper.geometry import output_size
from cropper.gui import MainWindow
from cropper.settings import (
    MAXIMUM, MAX_CUSTOM_DIMENSION, OUTPUT_PRESETS, OutputPreset,
    ProcessingOptions, custom_output,
)
from cropper.processing import process_image
from cropper.splash import StartupSplash
from cropper.startup import construct_window


ROOT = Path(__file__).resolve().parent.parent


class CustomSizingTests(unittest.TestCase):
    def test_catalog_has_no_duplicate_or_out_of_order_sizes(self):
        for ratio, presets in OUTPUT_PRESETS.items():
            with self.subTest(ratio=ratio):
                keys = [p.key for p in presets]
                self.assertEqual(len(keys), len(set(keys)))
                edges = [max(p.dimensions) if p.dimensions else p.long_edge
                         for p in presets if p.dimensions or p.long_edge]
                self.assertEqual(edges, sorted(set(edges)))
                self.assertEqual(keys[-1], 'custom')
        self.assertEqual(OUTPUT_PRESETS['4:3'][0], MAXIMUM)

    def test_width_and_height_use_oriented_four_by_three(self):
        for axis, portrait, expected in (
            ('width', False, (1200, 900)), ('width', True, (1200, 1600)),
            ('height', False, (1600, 1200)), ('height', True, (900, 1200)),
        ):
            with self.subTest(axis=axis, portrait=portrait):
                options = ProcessingOptions((4, 3), custom_output(axis, 1200), True)
                size = (1800, 2400) if portrait else (2400, 1800)
                self.assertEqual(output_size(size, options, portrait=portrait), (expected, False))

    def test_original_uses_each_images_actual_proportions(self):
        for axis, source, expected in (
            ('width', (600, 300), (120, 60)), ('width', (300, 600), (120, 240)),
            ('width', (400, 400), (120, 120)), ('height', (600, 300), (240, 120)),
            ('height', (300, 600), (60, 120)), ('height', (400, 400), (120, 120)),
        ):
            with self.subTest(axis=axis, source=source):
                options = ProcessingOptions(None, custom_output(axis, 120))
                self.assertEqual(output_size(source, options, portrait=source[1] > source[0]),
                                 (expected, False))

    def test_custom_obeys_no_upscaling_and_allow_upscaling(self):
        for allowed, expected, blocked in ((False, (600, 450), True),
                                           (True, (1200, 900), False)):
            options = ProcessingOptions((4, 3), custom_output('width', 1200), allowed)
            self.assertEqual(output_size((600, 450), options), (expected, blocked))

    def test_invalid_custom_values_are_refused_and_one_pixel_is_valid(self):
        for value in (0, -1, MAX_CUSTOM_DIMENSION + 1, 1.5, '1200', None, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                custom_output('width', value)
        with self.assertRaises(ValueError):
            custom_output('diagonal', 1200)
        with self.assertRaises(ValueError):
            output_size((600, 450), ProcessingOptions(output=OutputPreset('custom', 'Custom')))
        self.assertEqual(output_size((600, 450), ProcessingOptions(
            output=custom_output('width', 1))), ((1, 1), False))

    def test_custom_uses_one_existing_lanczos_resize_in_every_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'sample.png'
            Image.new('RGB', (200, 150), (20, 40, 80)).save(source)
            original_resize = Image.Image.resize
            for fmt in ('JPEG', 'PNG', 'TGA'):
                calls = []

                def resize(image, size, resample, **kwargs):
                    calls.append((size, resample, kwargs))
                    return original_resize(image, size, resample, **kwargs)

                with patch.object(Image.Image, 'resize', new=resize):
                    result = process_image(source, ProcessingOptions(
                        (4, 3), custom_output('height', 60), output_format=fmt))
                self.assertEqual(result.error, '')
                self.assertEqual(calls, [((80, 60), Image.Resampling.LANCZOS, {'reducing_gap': None})])
                with Image.open(result.output) as output:
                    self.assertEqual((output.size, output.format), ((80, 60), fmt))

    def test_custom_heic_and_primary_heif_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, expected in (('oriented.heic', (48, 36)),
                                   ('primary-second.heif', (48, 64))):
                source = Path(tmp) / name
                shutil.copyfile(ROOT / 'tests/fixtures/input_formats' / name, source)
                result = process_image(source, ProcessingOptions(
                    (4, 3), custom_output('width', 48), output_format='PNG'))
                self.assertEqual(result.error, '')
                self.assertEqual(result.size, expected)


class CustomGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.settings = QSettings(str(self.root / 'settings.ini'), QSettings.Format.IniFormat)
        self.window = MainWindow(language='en', settings=self.settings)
        self.window.open_when_finished.setChecked(False)
        self.window.show()
        self.app.processEvents()

    def tearDown(self):
        if self.window.worker is not None:
            self.window.worker.wait()
            self.app.processEvents()
        self.window.close()
        self.temp.cleanup()

    def choose_custom(self):
        for index in range(self.window.output_size.count()):
            if self.window.output_size.itemData(index).key == 'custom':
                self.window.output_size.setCurrentIndex(index)
                break
        self.app.processEvents()

    def add_images(self, sizes):
        for index, size in enumerate(sizes):
            Image.new('RGB', size, 'steelblue').save(self.root / f'input-{index}.png')
        self.window.add_paths([self.root])
        self.wait_idle()

    def wait_idle(self):
        deadline = time.monotonic() + 30
        while self.window.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.005)
        self.assertFalse(self.window.busy)

    def test_custom_controls_only_visible_when_selected_and_values_are_bounded(self):
        window = self.window
        self.assertTrue(window.custom_controls.isHidden())
        self.choose_custom()
        self.assertTrue(window.custom_controls.isVisible())
        self.assertTrue(window.upscaling.isEnabled())
        window.custom_value.setValue(0)
        self.assertEqual(window.current_options().output.value, 1)
        window.custom_value.setValue(MAX_CUSTOM_DIMENSION + 1)
        self.assertEqual(window.current_options().output.value, MAX_CUSTOM_DIMENSION)
        state, _, _ = window.custom_value.validate('1.5', 3)
        self.assertEqual(state, QValidator.State.Invalid)
        window.output_size.setCurrentIndex(0)
        self.assertTrue(window.custom_controls.isHidden())

    def test_preview_updates_width_height_portrait_and_landscape_immediately(self):
        self.add_images(((2400, 1800), (1800, 2400)))
        window = self.window
        self.choose_custom()
        window.custom_value.setValue(1200)
        window.table.selectRow(0)
        self.assertIn('1200 × 900', window.preview.details.text())
        window.table.selectRow(1)
        self.assertIn('1200 × 1600', window.preview.details.text())
        window.custom_dimension.setCurrentIndex(1)
        self.assertIn('900 × 1200', window.preview.details.text())
        window.table.selectRow(0)
        self.assertIn('1600 × 1200', window.preview.details.text())
        window.custom_value.setValue(240)
        self.assertIn('320 × 240', window.preview.details.text())

    def test_original_preview_and_mixed_proportions_batch_share_custom_snapshot(self):
        self.add_images(((300, 200), (200, 400)))
        window = self.window
        window.aspect.setCurrentIndex(0)
        self.choose_custom()
        window.custom_value.setValue(120)
        for row, expected in ((0, '120 × 80'), (1, '120 × 240')):
            window.table.selectRow(row)
            self.assertIn(expected, window.preview.details.text())
        window.process.click()
        self.assertFalse(window.custom_controls.isEnabled())
        snapshot = window.worker.options
        window.custom_value.setValue(40)
        self.assertEqual(snapshot.output.value, 120)
        self.wait_idle()
        self.assertEqual((window.processed, window.errors), (2, 0))
        for row, expected in ((0, (120, 80)), (1, (120, 240))):
            with Image.open(self.root / 'Cropperio_Export' / f'input-{row}.jpg') as output:
                self.assertEqual(output.size, expected)

    def test_custom_preferences_persist_and_survive_ratio_language_theme_changes(self):
        window = self.window
        self.choose_custom()
        window.custom_dimension.setCurrentIndex(1)
        window.custom_value.setValue(640)
        for language, text in (('en', 'Custom…'), ('fr', 'Personnalisé…'), ('ja', 'カスタム…')):
            window.language_combo.setCurrentIndex(window.language_combo.findData(language))
            self.assertEqual(window.output_size.currentText(), text)
            for theme in ('dark', 'light', 'classic'):
                window.theme_combo.setCurrentIndex(window.theme_combo.findData(theme))
                window.aspect.setCurrentIndex(0)
                self.assertEqual(window.current_options().output, custom_output('height', 640))
                self.assertEqual(window.tagline.text(), TAGLINE)
                self.assertEqual(window.subtitle.text(), DESCRIPTION)
        window.close()
        self.window = MainWindow(settings=self.settings)
        self.choose_custom()
        self.assertEqual(self.window.current_options().output, custom_output('height', 640))

    def test_wand_icons_have_distinct_modern_and_pixel_variants(self):
        window = self.window
        apply = window.style().standardIcon(QStyle.StandardPixmap.SP_DialogApplyButton).pixmap(24, 24).toImage()
        modern = None
        for theme in ('dark', 'light', 'classic'):
            window.theme_combo.setCurrentIndex(window.theme_combo.findData(theme))
            icon = window.process.icon()
            self.assertFalse(icon.isNull())
            rendered = icon.pixmap(24, 24).toImage()
            self.assertNotEqual(rendered, apply)
            if theme == 'dark':
                modern = rendered
            if theme == 'classic':
                self.assertNotEqual(rendered, modern)
                self.assertEqual(icon.pixmap(16, 16).toImage(), classic_icon('process').pixmap(16, 16).toImage())

    def test_custom_layout_keeps_preview_and_controls_inside_panels(self):
        self.choose_custom()
        for language in ('en', 'fr', 'ja'):
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            for theme in ('dark', 'light', 'classic'):
                self.window.theme_combo.setCurrentIndex(self.window.theme_combo.findData(theme))
                self.window.resize(920, 760)
                for _ in range(4):
                    self.app.processEvents()
                preview = self.window.preview
                self.assertLess(preview.canvas.geometry().bottom(), preview.details.geometry().top())
                self.assertLess(preview.details.geometry().bottom(), preview.height())
                controls = self.window.custom_controls
                self.assertLess(controls.geometry().bottom(), controls.parentWidget().height())


class SplashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_splash_identity_borderless_and_hidpi_size_in_three_languages(self):
        for language in ('en', 'fr', 'ja'):
            splash = StartupSplash(language)
            splash.show()
            splash.complete_branding()
            self.app.processEvents()
            self.assertTrue(splash.windowFlags() & Qt.WindowType.FramelessWindowHint)
            self.assertEqual(splash.pixmap().deviceIndependentSize().toSize().width(), 460)
            self.assertEqual(splash.pixmap().deviceIndependentSize().toSize().height(), 258)
            self.assertIn('Cropperio', STARTING[language])
            self.assertIn('Voilà.', TAGLINE)
            splash.close()

    def test_failed_window_initialization_closes_splash(self):
        splash = StartupSplash()
        splash.show()
        with self.assertRaises(RuntimeError):
            construct_window(splash, lambda: (_ for _ in ()).throw(RuntimeError('test failure')))
        self.assertFalse(splash.isVisible())

    def test_real_startup_shows_splash_before_heavy_imports_and_closes_when_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / 'startup.json'
            env = dict(os.environ, QT_QPA_PLATFORM='offscreen')
            result = subprocess.run([sys.executable, str(ROOT / 'main.py'), '--startup-test', str(report)],
                                    cwd=ROOT, env=env, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors='replace'))
            data = json.loads(report.read_text(encoding='utf-8'))
            self.assertTrue(data['passed'])
            self.assertTrue(data['imports_deferred'])
            self.assertTrue(data['splash_closed'])
            self.assertLess(data['phases_ms']['splash_visible'], data['phases_ms']['gui_imported'])
            self.assertEqual(data['tagline'], TAGLINE)
