"""Per-source ratio, sizing, framing, and mixed-ratio worker regression tests."""
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import time
import unittest

from PIL import Image, ImageChops
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from cropper.geometry import (ManualCrop, crop_box, crop_size, image_options,
                              output_size, resolve_crop, zoom_crop)
from cropper.gui import MainWindow
from cropper.input_formats import load_primary_image
from cropper.settings import ProcessingOptions, OutputPreset, custom_output


class RatioGeometryTests(unittest.TestCase):
    def setUp(self):
        self.options = ProcessingOptions((1, 1), OutputPreset('size', '', dimensions=(1200, 1200)), True)

    def test_no_override_keeps_batch_options_identical(self):
        self.assertIs(image_options((600, 400), self.options), self.options)
        self.assertIs(image_options((600, 400), self.options, ManualCrop()), self.options)

    def test_numeric_long_edge_adapts_to_every_ratio_and_orientation(self):
        for ratio, landscape in (('1:1', (1200, 1200)), ('4:3', (1200, 900)),
                                  ('2:1', (1200, 600)), ('Original', (1200, 800))):
            for portrait in (False, True):
                size = (400, 600) if portrait else (600, 400)
                state = ManualCrop(ratio_override=ratio, framing=False)
                options = image_options(size, self.options, state)
                box = resolve_crop(size, self.options, state)
                target, blocked = output_size(crop_size(box), options, portrait=portrait)
                self.assertEqual(target, landscape[::-1] if portrait else landscape)
                self.assertFalse(blocked)

    def test_long_edge_preset_from_original_batch_adapts_to_fixed_override(self):
        batch = ProcessingOptions(None, OutputPreset('edge', '', long_edge=1200), True)
        state = ManualCrop(ratio_override='4:3')
        options = image_options((600, 400), batch, state)
        self.assertEqual(output_size((400, 300), options), ((1200, 900), False))

    def test_custom_width_and_height_keep_reference_axis(self):
        for axis, portrait, expected in (('width', False, (1200, 900)),
                                          ('height', False, (1600, 1200)),
                                          ('width', True, (1200, 1600)),
                                          ('height', True, (900, 1200))):
            size = (400, 600) if portrait else (600, 400)
            batch = replace(self.options, output=custom_output(axis, 1200))
            options = image_options(size, batch, ManualCrop(ratio_override='4:3'))
            self.assertEqual(output_size(size, options, portrait=portrait), (expected, False))

    def test_ratio_only_override_is_exactly_automatic_even_with_odd_dimensions(self):
        size = (601, 400)
        state = ManualCrop(ratio_override='4:3', framing=False)
        self.assertEqual(resolve_crop(size, self.options, state), crop_box(*size, (4, 3)))

    def test_override_minimum_uses_adapted_output_size(self):
        state = ManualCrop(scale=.01, ratio_override='4:3')
        batch = replace(self.options, allow_upscaling=False)
        self.assertEqual(crop_size(resolve_crop((6000, 4000), batch, state)), (1200, 900))

    def test_zoom_preserves_ratio_override_and_allows_upscaling(self):
        state = zoom_crop((600, 400), self.options, ManualCrop(ratio_override='2:1'), 100)
        self.assertEqual(state.ratio_override, '2:1')
        w, h = crop_size(resolve_crop((600, 400), self.options, state))
        self.assertLess(w, 1200)
        self.assertLessEqual(abs(w / 2 - h), .5)


class RatioGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for index, size in enumerate(((600, 400),) * 4 + ((400, 600),)):
            Image.effect_noise(size, 100).convert('RGB').save(self.root / f'{index}.png')
        shutil.copyfile(Path(__file__).parent / 'fixtures/input_formats/oriented.heic', self.root / '5.heic')
        self.window = MainWindow(language='en', theme='dark', settings=QSettings(str(self.root / 'prefs.ini'), QSettings.Format.IniFormat))
        self.window.open_when_finished.setChecked(False)
        self.window.show()
        self.window.add_paths([self.root])
        self.wait_idle()
        self.window.aspect.setCurrentText('1:1')
        self.window.output_format.setCurrentText('PNG')
        self.window.table.selectRow(0)
        self.app.processEvents()

    def tearDown(self):
        self.wait_idle()
        self.window.close()
        self.temp.cleanup()

    def wait_idle(self):
        deadline = time.monotonic() + 30
        while self.window.busy and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(.005)
        self.assertFalse(self.window.busy)

    def override(self, row, ratio):
        self.window.table.selectRow(row)
        combo = self.window.preview.image_ratio
        combo.setCurrentIndex(combo.findData(ratio))

    def configure_mixed(self):
        for row, ratio in ((1, '4:3'), (2, '2:1'), (3, 'Original'), (4, '4:3'), (5, 'Original')):
            self.override(row, ratio)

    def test_initial_batch_square_without_states(self):
        self.assertEqual(self.window.manual_crops, {})
        for row in range(6):
            self.window.table.selectRow(row)
            self.assertEqual(self.window.preview.image_ratio.currentData(), None)
            w, h = crop_size(self.window.preview.canvas.crop)
            self.assertEqual(w, h)

    def test_selection_restores_individual_ratio_crop_and_zoom(self):
        self.configure_mixed()
        self.override(1, '4:3')
        self.window.zoom_preview_crop(8)
        self.window.move_preview_crop(self.window.preview.canvas.crop, 20, -30)
        box = self.window.preview.canvas.crop
        self.override(2, '2:1')
        self.window.table.selectRow(1)
        self.assertEqual(self.window.preview.image_ratio.currentData(), '4:3')
        self.assertEqual(self.window.preview.canvas.crop, box)
        self.assertNotIn(self.window.paths[0], self.window.manual_crops)

    def test_global_ratio_changes_only_inherited_images(self):
        self.configure_mixed()
        before = {}
        for row in range(1, 6):
            self.window.table.selectRow(row)
            self.window.zoom_preview_crop(5)
            before[row] = self.window.preview.canvas.crop
        self.window.aspect.setCurrentText('4:3')
        for row, box in before.items():
            self.window.table.selectRow(row)
            self.assertEqual(self.window.preview.canvas.crop, box)
        self.window.table.selectRow(0)
        self.assertEqual(self.window.preview.canvas.crop, crop_box(600, 400, (4, 3)))
        self.assertIn('(4:3)', self.window.preview.image_ratio.itemText(0))

    def test_remove_override_preserves_framing_and_uses_current_batch(self):
        self.override(1, '2:1')
        self.window.zoom_preview_crop(10)
        state = self.window.manual_crops[self.window.paths[1]]
        self.override(1, None)
        current = self.window.manual_crops[self.window.paths[1]]
        self.assertIsNone(current.ratio_override)
        self.assertAlmostEqual(state.scale, current.scale)
        w, h = crop_size(self.window.preview.canvas.crop)
        self.assertEqual(w, h)

    def test_remove_ratio_only_override_removes_sparse_state(self):
        self.override(1, 'Original')
        self.override(1, None)
        self.assertNotIn(self.window.paths[1], self.window.manual_crops)
        self.assertEqual(self.window.preview.canvas.crop, crop_box(600, 400, (1, 1)))

    def test_change_individual_ratio_retains_valid_center_and_zoom(self):
        self.window.zoom_preview_crop(20)
        self.window.move_preview_crop(self.window.preview.canvas.crop, 10, 15)
        state = self.window.manual_crops[self.window.paths[0]]
        self.override(0, '4:3')
        changed = self.window.manual_crops[self.window.paths[0]]
        self.assertAlmostEqual(changed.scale, state.scale)
        self.assertAlmostEqual(changed.center_x, state.center_x, delta=1/600)
        self.assertAlmostEqual(changed.center_y, state.center_y, delta=1/400)

    def test_reset_preserves_override_and_other_images(self):
        self.override(1, '4:3')
        self.window.zoom_preview_crop(8)
        self.override(2, '2:1')
        self.window.zoom_preview_crop(4)
        other = self.window.manual_crops[self.window.paths[2]]
        self.window.table.selectRow(1)
        self.window.preview.reset_crop.click()
        self.assertEqual(self.window.preview.image_ratio.currentData(), '4:3')
        self.assertEqual(self.window.preview.canvas.crop, crop_box(600, 400, (4, 3)))
        self.assertFalse(self.window.preview.reset_crop.isEnabled())
        self.assertEqual(self.window.manual_crops[self.window.paths[2]], other)

    def test_minimum_constraints_update_unselected_override(self):
        self.override(1, '4:3')
        self.window.zoom_preview_crop(20)
        self.window.table.selectRow(0)
        self.window.custom_value.setValue(500)
        self.window.output_size.setCurrentIndex(self.window.output_size.count() - 1)
        self.window.table.selectRow(1)
        self.assertEqual(crop_size(self.window.preview.canvas.crop), (500, 375))
        self.assertEqual(self.window.preview.image_ratio.currentData(), '4:3')

    def test_mixed_ratio_maximum_batch_matches_preview_pixels_including_heic(self):
        self.configure_mixed()
        expected = {}
        for row in range(6):
            self.window.table.selectRow(row)
            if row in (1, 2, 5):
                self.window.zoom_preview_crop(5 + row)
                self.window.move_preview_crop(self.window.preview.canvas.crop, 10, 8)
            expected[row] = self.window.preview.canvas.crop
        self.window.start_processing()
        snapshot = dict(self.window.worker.crops)
        self.window.manual_crops.clear()
        self.assertEqual(self.window.worker.crops, snapshot)
        self.wait_idle()
        self.assertEqual((self.window.processed, self.window.errors), (6, 0))
        for row, box in expected.items():
            with load_primary_image(self.window.paths[row]) as source, Image.open(self.window.table.item(row, 1).toolTip()) as output:
                self.assertEqual(output.size, crop_size(box))
                self.assertIsNone(ImageChops.difference(source.crop(box).convert('RGBA'), output.convert('RGBA')).getbbox(alpha_only=False))

    def test_numeric_mixed_ratio_batch_uses_shared_long_edge(self):
        self.configure_mixed()
        self.window.output_size.setCurrentIndex(1)  # 512 x 512 batch preset.
        self.window.upscaling.setChecked(True)
        self.window.start_processing()
        self.wait_idle()
        expected = ((512, 512), (512, 384), (512, 256), (512, 341), (384, 512), (512, 341))
        for row, size in enumerate(expected):
            with Image.open(self.window.table.item(row, 1).toolTip()) as output:
                self.assertEqual(output.size, size)
            self.window.table.selectRow(row)
            self.assertIn(f'{size[0]} × {size[1]}', self.window.preview.details.text())

    def test_custom_width_height_mixed_ratio_exports(self):
        self.configure_mixed()
        self.window.custom_value.setValue(120)
        self.window.output_size.setCurrentIndex(self.window.output_size.count() - 1)
        for axis, sizes in (('width', ((120, 120), (120, 90), (120, 60), (120, 80), (120, 160), (120, 80))),
                            ('height', ((120, 120), (160, 120), (240, 120), (180, 120), (90, 120), (180, 120)))):
            self.window.upscaling.setChecked(True)
            self.window.custom_dimension.setCurrentIndex(self.window.custom_dimension.findData(axis))
            self.window.start_processing()
            self.wait_idle()
            for row, size in enumerate(sizes):
                with Image.open(self.window.table.item(row, 1).toolTip()) as output:
                    self.assertEqual(output.size, size)

    def test_ratio_ui_in_all_languages_and_themes(self):
        self.override(1, 'Original')
        for language in ('en', 'fr', 'ja'):
            self.window.language_combo.setCurrentIndex(self.window.language_combo.findData(language))
            for theme in ('dark', 'light', 'classic'):
                self.window.theme_combo.setCurrentIndex(self.window.theme_combo.findData(theme))
                self.window.resize(920, 760)
                self.app.processEvents()
                panel = self.window.preview
                self.assertEqual(panel.image_ratio.currentData(), 'Original')
                self.assertFalse(panel.image_ratio.toolTip() == '')
                self.assertLess(panel.image_ratio.geometry().right(), panel.width())
                self.assertLess(panel.image_ratio.geometry().bottom(), panel.canvas.geometry().top())
                self.assertGreaterEqual(panel.canvas.height(), 100)
