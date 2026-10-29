"""Interactive source geometry, Qt events, and pixel-identical exports."""
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from cropper.geometry import (ManualCrop, crop_box, crop_size, crop_adjustment,
                              resolve_crop, move_crop, zoom_crop)
from cropper.gui import MainWindow
from cropper.i18n import tr
from cropper.input_formats import load_primary_image
from cropper.processing import process_image
from cropper.settings import MAXIMUM, ProcessingOptions, custom_output, OutputPreset


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.size = (6000, 4000)
        self.options = ProcessingOptions((2, 1))

    def test_automatic_is_unchanged_for_all_ratios_and_orientations(self):
        for size in (self.size, self.size[::-1], (101, 101), (1, 2)):
            for ratio in (None, (1, 1), (2, 1), (4, 3), (16, 9)):
                options = replace(self.options, aspect_ratio=ratio)
                self.assertEqual(resolve_crop(size, options), crop_box(*size, ratio))

    def test_drag_horizontal(self):
        options = replace(self.options, aspect_ratio=(1, 1))
        self.assertEqual(move_crop(self.size, options, crop_box(*self.size, (1, 1)), 200, 100),
                         (1200, 0, 5200, 4000))

    def test_drag_vertical(self):
        self.assertEqual(move_crop(self.size, self.options, (0, 500, 6000, 3500), 100, -200),
                         (0, 300, 6000, 3300))

    def test_drag_both_axes(self):
        box = resolve_crop(self.size, self.options, ManualCrop(scale=.5))
        self.assertEqual(move_crop(self.size, self.options, box, 200, 300), (1700, 1550, 4700, 3050))

    def test_clamp_left(self):
        self.assertEqual(move_crop(self.size, self.options, (1500, 1250, 4500, 2750), -9000, 0)[0], 0)

    def test_clamp_right(self):
        self.assertEqual(move_crop(self.size, self.options, (1500, 1250, 4500, 2750), 9000, 0)[2], 6000)

    def test_clamp_top(self):
        self.assertEqual(move_crop(self.size, self.options, (1500, 1250, 4500, 2750), 0, -9000)[1], 0)

    def test_clamp_bottom(self):
        self.assertEqual(move_crop(self.size, self.options, (1500, 1250, 4500, 2750), 0, 9000)[3], 4000)

    def test_wheel_zoom_in(self):
        state = zoom_crop(self.size, self.options, None, 1)
        self.assertAlmostEqual(state.scale, .960789439)
        self.assertLess(crop_size(resolve_crop(self.size, self.options, state))[0], 6000)

    def test_wheel_zoom_out(self):
        state = zoom_crop(self.size, self.options, ManualCrop(scale=.5), -1)
        self.assertGreater(state.scale, .5)

    def test_maximum_crop(self):
        state = zoom_crop(self.size, self.options, ManualCrop(scale=.5), -100)
        self.assertEqual(resolve_crop(self.size, self.options, state), crop_box(*self.size, (2, 1)))

    def test_minimum_without_upscaling(self):
        options = replace(self.options, output=OutputPreset('test', '', dimensions=(1200, 600)))
        state = zoom_crop(self.size, options, None, 100)
        self.assertEqual(crop_size(resolve_crop(self.size, options, state)), (1200, 600))

    def test_upscaling_allows_crop_below_output_but_keeps_safety_floor(self):
        options = replace(self.options, output=custom_output('width', 1200), allow_upscaling=True)
        state = ManualCrop()
        for _ in range(5):
            state = zoom_crop(self.size, options, state, 100)
        size = crop_size(resolve_crop(self.size, options, state))
        self.assertEqual(size[1], 16)
        self.assertLess(size[0], 1200)

    def test_ratio_lock_has_only_integer_pixel_rounding(self):
        for source, ratio, expected in (((6000, 4000), (1, 1), 1),
                                        ((6000, 4000), (2, 1), 2),
                                        ((6000, 4000), (4, 3), 4/3),
                                        ((4000, 6000), (4, 3), 3/4)):
            options = replace(self.options, aspect_ratio=ratio)
            for scale in (.9, .734, .5, .123):
                w, h = crop_size(resolve_crop(source, options, ManualCrop(scale=scale)))
                self.assertLessEqual(abs(h - w / expected), .5)

    def test_custom_width_minimum(self):
        options = ProcessingOptions((4, 3), custom_output('width', 1200))
        self.assertEqual(crop_size(resolve_crop(self.size, options, ManualCrop(scale=.001))), (1200, 900))

    def test_custom_height_minimum_portrait(self):
        options = ProcessingOptions((4, 3), custom_output('height', 1200))
        self.assertEqual(crop_size(resolve_crop(self.size[::-1], options, ManualCrop(scale=.001))), (900, 1200))

    def test_undersized_source_retains_maximum(self):
        options = replace(self.options, output=custom_output('width', 9000))
        self.assertEqual(resolve_crop(self.size, options, ManualCrop(scale=.01)), crop_box(*self.size, (2, 1)))

    def test_ratio_change_preserves_relative_center_and_zoom(self):
        state = ManualCrop(.6, .4, .5)
        box = resolve_crop(self.size, replace(self.options, aspect_ratio=(4, 3)), state)
        self.assertEqual(crop_size(box), (2666, 2000))
        self.assertAlmostEqual((box[0] + box[2]) / 2, 3600)
        self.assertAlmostEqual((box[1] + box[3]) / 2, 1600)

    def test_fractional_wheel_deltas_accumulate(self):
        state = None
        for _ in range(120):
            state = zoom_crop(self.size, self.options, state, 1/120)
        one = zoom_crop(self.size, self.options, None, 1)
        self.assertAlmostEqual(state.scale, one.scale)
        self.assertEqual(resolve_crop(self.size, self.options, state), resolve_crop(self.size, self.options, one))

    def test_tiny_sources_never_produce_empty_crops(self):
        for source in ((1, 1), (1, 100), (100, 1), (8, 4)):
            box = resolve_crop(source, self.options, ManualCrop(-5, 10, .00001))
            self.assertGreater(box[2] - box[0], 0)
            self.assertGreater(box[3] - box[1], 0)
            self.assertTrue(0 <= box[0] < box[2] <= source[0])
            self.assertTrue(0 <= box[1] < box[3] <= source[1])


class InteractiveGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for index, size in enumerate(((600, 400), (400, 600), (600, 400))):
            Image.effect_noise(size, 100).convert('RGB').save(self.root / f'{index}.png')
        self.window = MainWindow(settings=QSettings(str(self.root / 'prefs.ini'), QSettings.Format.IniFormat))
        self.window.open_when_finished.setChecked(False)
        self.window.show()
        self.window.add_paths([self.root])
        self.wait_idle()
        self.window.aspect.setCurrentText('2:1')
        self.window.output_format.setCurrentText('PNG')
        self.window.table.selectRow(0)
        self.app.processEvents()

    def wait_idle(self):
        deadline = time.monotonic() + 30
        while self.window.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertFalse(self.window.busy)

    def tearDown(self):
        self.wait_idle()
        self.window.close()
        self.temp.cleanup()

    def wheel(self, delta=120, pixels=0):
        canvas = self.window.preview.canvas
        position = canvas.rect().center()
        event = QWheelEvent(QPointF(position), QPointF(canvas.mapToGlobal(position)),
                            QPoint(0, pixels), QPoint(0, delta), Qt.MouseButton.NoButton,
                            Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.ScrollUpdate, False)
        QApplication.sendEvent(canvas, event)

    def test_real_qt_drag_and_cursor(self):
        canvas = self.window.preview.canvas
        center = canvas.crop_rect().center().toPoint()
        QTest.mouseMove(canvas, center)
        self.assertEqual(canvas.cursor().shape(), Qt.CursorShape.OpenHandCursor)
        before = canvas.crop
        QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=center)
        self.assertEqual(canvas.cursor().shape(), Qt.CursorShape.ClosedHandCursor)
        QTest.mouseMove(canvas, center + QPoint(0, 15))
        QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=center + QPoint(0, 15))
        self.assertGreater(canvas.crop[1], before[1])
        QTest.mouseMove(canvas, canvas.image_rect().topLeft().toPoint() + QPoint(1, 1))
        self.assertEqual(canvas.cursor().shape(), Qt.CursorShape.ArrowCursor)

    def test_wheel_events_high_resolution_and_touchpad_pixel_delta(self):
        before = self.window.preview.canvas.crop
        for _ in range(120):
            self.wheel(1)
        after = self.window.preview.canvas.crop
        self.assertLess(crop_size(after)[0], crop_size(before)[0])
        self.wheel(0, 20)
        self.assertLess(crop_size(self.window.preview.canvas.crop)[0], crop_size(after)[0])
        self.wheel(-120)
        self.assertGreater(crop_size(self.window.preview.canvas.crop)[0], crop_size(after)[0] - 1)

    def test_batch_restores_independent_crops_and_reset_is_local(self):
        window = self.window
        window.zoom_preview_crop(5)
        first = window.preview.canvas.crop
        window.table.selectRow(1)
        self.assertNotIn(window.paths[1], window.manual_crops)
        window.zoom_preview_crop(10)
        second = window.preview.canvas.crop
        window.table.selectRow(0)
        self.assertEqual(window.preview.canvas.crop, first)
        window.preview.reset_crop.click()
        self.assertNotIn(window.paths[0], window.manual_crops)
        self.assertIn(window.paths[1], window.manual_crops)
        window.table.selectRow(1)
        self.assertEqual(window.preview.canvas.crop, second)
        window.table.selectRow(2)
        self.assertEqual(window.preview.canvas.crop, crop_box(600, 400, (2, 1)))

    def test_output_change_grows_crop_and_preserves_center(self):
        window = self.window
        window.zoom_preview_crop(20)
        window.custom_value.setValue(500)
        window.output_size.setCurrentIndex(window.output_size.count() - 1)
        self.assertEqual(crop_size(window.preview.canvas.crop), (500, 250))
        window.custom_value.setValue(100)
        self.assertEqual(crop_size(window.preview.canvas.crop), (500, 250))

    def test_ratio_change_updates_unselected_manual_images(self):
        window = self.window
        window.zoom_preview_crop(10)
        window.table.selectRow(1)
        window.aspect.setCurrentText('1:1')
        window.table.selectRow(0)
        w, h = crop_size(window.preview.canvas.crop)
        self.assertEqual(w, h)

    def test_drag_and_wheel_do_not_decode_or_encode_images(self):
        with patch('cropper.gui.load_primary_image', side_effect=AssertionError('Decoded during drag')), \
                patch.object(Image.Image, 'save', side_effect=AssertionError('Encoded during drag')):
            self.window.zoom_preview_crop(5)
            self.window.move_preview_crop(self.window.preview.canvas.crop, 20, 20)

    def test_maximum_export_matches_preview_pixel_for_pixel_batch_snapshot(self):
        window = self.window
        expected = {}
        for row, steps in ((0, 10), (1, 6), (2, 0)):
            window.table.selectRow(row)
            if steps:
                window.zoom_preview_crop(steps)
                window.move_preview_crop(window.preview.canvas.crop, 20, 30)
            expected[row] = window.preview.canvas.crop
        window.start_processing()
        snapshot = dict(window.worker.crops)
        window.manual_crops.clear()
        self.assertEqual(window.worker.crops, snapshot)
        self.wait_idle()
        self.assertEqual((window.processed, window.errors), (3, 0))
        for row, box in expected.items():
            with Image.open(window.paths[row]) as original, Image.open(window.table.item(row, 1).toolTip()) as output:
                self.assertEqual(output.size, crop_size(box))
                self.assertIsNone(ImageChops.difference(original.crop(box), output).getbbox(alpha_only=False))

    def test_three_languages_and_themes_with_manual_crop(self):
        self.window.zoom_preview_crop(5)
        box = self.window.preview.canvas.crop
        for language in ('en', 'fr', 'ja'):
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            self.assertEqual(self.window.preview.reset_crop.text(), tr('reset_crop', language))
            for theme in ('dark', 'light', 'classic'):
                self.window.theme_combo.setCurrentIndex(self.window.theme_combo.findData(theme))
                self.window.resize(920, 760)
                self.app.processEvents()
                self.assertEqual(self.window.preview.canvas.crop, box)
                panel = self.window.preview
                self.assertLess(panel.reset_crop.geometry().right(), panel.width())
                self.assertLess(panel.canvas.geometry().bottom(), panel.details.geometry().top())
                self.assertFalse(panel.grab().isNull())

    def test_clear_removes_all_adjustments(self):
        self.window.zoom_preview_crop(5)
        self.window.clear_all()
        self.assertEqual(self.window.manual_crops, {})
        self.assertFalse(self.window.preview.reset_crop.isEnabled())


class OrientedExportTests(unittest.TestCase):
    def test_manual_custom_width_height_and_upscaling_exports(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / 'source.png'
            Image.effect_noise((600, 400), 100).convert('RGB').save(source)
            for dimension, value, upscale, expected in (
                ('width', 240, False, (240, 180)),
                ('height', 180, False, (240, 180)),
                ('width', 1200, True, (1200, 900)),
            ):
                options = ProcessingOptions((4, 3), custom_output(dimension, value), upscale, 'PNG')
                state = ManualCrop(.6, .4, .5)
                box = resolve_crop((600, 400), options, state)
                result = process_image(source, options, state)
                self.assertEqual(result.error, '')
                self.assertEqual(result.size, expected)
                with Image.open(source) as original, Image.open(result.output) as output:
                    pixels = original.crop(box).resize(expected, Image.Resampling.LANCZOS)
                    self.assertIsNone(ImageChops.difference(pixels, output).getbbox(alpha_only=False))

    def test_exif_and_heic_manual_crop_share_oriented_geometry(self):
        fixtures = Path(__file__).parent / 'fixtures/input_formats'
        with tempfile.TemporaryDirectory() as tmp:
            for name in ('oriented.heic', 'oriented.jpg', 'primary-second.heif'):
                source = Path(tmp) / name
                if name == 'oriented.jpg':
                    image = Image.effect_noise((120, 80), 100).convert('RGB')
                    exif = Image.Exif()
                    exif[274] = 6
                    image.save(source, exif=exif)
                else:
                    shutil.copyfile(fixtures / name, source)
                options = ProcessingOptions((4, 3), MAXIMUM, output_format='PNG')
                manual = ManualCrop(.65, .4, .6)
                with load_primary_image(source) as oriented:
                    expected = oriented.crop(resolve_crop(oriented.size, options, manual)).convert('RGBA')
                result = process_image(source, options, manual)
                self.assertEqual(result.error, '')
                self.assertEqual(result.size, expected.size)
                with Image.open(result.output) as output:
                    self.assertIsNone(ImageChops.difference(expected, output.convert('RGBA')).getbbox(alpha_only=False))
                    self.assertIsNone(output.getexif().get(274))
