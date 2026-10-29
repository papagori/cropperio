import shutil
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image
from PySide6.QtCore import QMimeData, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QApplication

from cropper.discovery import OUTPUT_DIR, discover
from cropper.gui import MainWindow
from cropper.i18n import tr
from cropper.input_formats import EXTENSIONS, load_primary_image
from cropper.processing import process_image
from cropper.settings import MAXIMUM, ORIGINAL, OutputPreset, ProcessingOptions


FIXTURES = Path(__file__).parent / 'fixtures' / 'input_formats'
SIZES = {p.name: (96, 64) for p in FIXTURES.iterdir() if p.suffix in EXTENSIONS}
SIZES.update({'primary-second.heif': (80, 120), 'alpha.avif': (80, 120),
              'sample.ico': (64, 64)})


class InputFormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'été 東京'
        self.root.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, name):
        target = self.root / name
        shutil.copyfile(FIXTURES / name, target)
        return target

    def test_all_input_decoders_and_maximum_resolution(self):
        for name, size in SIZES.items():
            with self.subTest(name=name):
                source = self.fixture(name)
                before = source.read_bytes()
                with load_primary_image(source) as image:
                    self.assertEqual(image.size, size)
                result = process_image(source, ProcessingOptions(output=MAXIMUM))
                self.assertEqual(result.error, '')
                self.assertEqual(result.original_size, size)
                expected = {(96, 64): (85, 64), (80, 120): (80, 107),
                            (64, 64): (64, 48)}[size]
                self.assertEqual(result.size, expected)
                self.assertEqual(source.read_bytes(), before)
                with Image.open(result.output) as output:
                    self.assertEqual((output.format, output.size), ('JPEG', expected))

    def test_new_formats_crop_and_resize_through_existing_pipeline(self):
        for name, ratio, preset, fmt, expected in (
            ('sample.bmp', (1, 1), MAXIMUM, 'PNG', (64, 64)),
            ('oriented.heic', (4, 3), MAXIMUM, 'JPEG', (85, 64)),
            ('primary-second.heif', (16, 9), OutputPreset('small', 'small', long_edge=60),
             'PNG', (34, 60)),
            ('sequence.avif', (16, 9), MAXIMUM, 'TGA', (96, 54)),
            ('animated.gif', (1, 1), OutputPreset('small', 'small', dimensions=(32, 32)),
             'PNG', (32, 32)),
        ):
            with self.subTest(name=name, fmt=fmt):
                result = process_image(self.fixture(name), ProcessingOptions(
                    aspect_ratio=ratio, output=preset, output_format=fmt))
                self.assertEqual(result.error, '')
                self.assertEqual(result.size, expected)
                with Image.open(result.output) as output:
                    self.assertEqual((output.format, output.size), (fmt, expected))

    def test_gif_first_frame_and_alpha_in_all_outputs(self):
        source = self.fixture('animated.gif')
        with Image.open(source) as original:
            self.assertEqual(original.n_frames, 2)
        for fmt in ('JPEG', 'PNG', 'TGA'):
            with self.subTest(fmt=fmt):
                result = process_image(source, ProcessingOptions(
                    aspect_ratio=None, output=ORIGINAL, output_format=fmt))
                self.assertEqual(result.error, '')
                with Image.open(result.output) as output:
                    center = output.convert('RGB').getpixel((40, 30))
                    self.assertGreater(center[0], 200)
                    self.assertLess(center[1], 50)  # Never the green second frame.
                    if fmt == 'JPEG':
                        self.assertEqual(output.getpixel((2, 2)), (255, 255, 255))
                    else:
                        self.assertEqual(output.mode, 'RGBA')
                        self.assertEqual(output.getpixel((2, 2))[3], 0)

    def test_heif_uses_primary_index_one_and_preserves_alpha(self):
        source = self.fixture('primary-second.heif')
        with Image.open(source) as original:
            self.assertEqual(original.n_frames, 2)
            self.assertEqual(original.tell(), 1)
        for fmt in ('PNG', 'TGA', 'JPEG'):
            with self.subTest(fmt=fmt):
                result = process_image(source, ProcessingOptions(
                    aspect_ratio=None, output=ORIGINAL, output_format=fmt))
                self.assertEqual(result.error, '')
                with Image.open(result.output) as output:
                    self.assertEqual(output.size, (80, 120))
                    if fmt != 'JPEG':
                        self.assertEqual(output.mode, 'RGBA')
                        self.assertEqual(output.getpixel((40, 60))[3], 128)
                        self.assertEqual(output.getpixel((2, 2))[3], 0)
                    else:
                        self.assertEqual(output.getpixel((2, 2)), (255, 255, 255))

    def test_heic_orientation_is_not_applied_twice_and_metadata_survives(self):
        source = self.fixture('oriented.heic')
        with Image.open(source) as original:
            self.assertEqual(original.info['original_orientation'], 6)
            profile = original.info['icc_profile']
        for fmt in ('JPEG', 'PNG'):
            with self.subTest(fmt=fmt):
                result = process_image(source, ProcessingOptions(
                    aspect_ratio=None, output=ORIGINAL, output_format=fmt))
                self.assertEqual(result.error, '')
                with Image.open(result.output) as output:
                    self.assertEqual(output.size, (96, 64))
                    self.assertNotIn(274, output.getexif())
                    self.assertEqual(output.getexif()[315], 'Cropperio synthetic fixture')
                    self.assertEqual(output.info['icc_profile'], profile)
                    self.assertGreater(output.getpixel((80, 10))[2], 200)
                    self.assertGreater(output.getpixel((10, 10))[0], 200)

    def test_tiff_and_avif_use_only_first_page_or_frame(self):
        for name in ('pages.tiff', 'sequence.avif'):
            with self.subTest(name=name):
                source = self.fixture(name)
                with Image.open(source) as original:
                    self.assertEqual(original.n_frames, 2)
                result = process_image(source, ProcessingOptions(
                    aspect_ratio=None, output=ORIGINAL, output_format='PNG'))
                self.assertEqual(result.error, '')
                with Image.open(result.output) as output:
                    self.assertEqual(output.size, (96, 64))
                    self.assertGreater(output.getpixel((10, 10))[0], 200)
                    self.assertLess(output.getpixel((10, 10))[1], 50)

    def test_avif_and_ico_alpha_survives_png_and_tga(self):
        for name in ('alpha.avif', 'sample.ico'):
            for fmt in ('PNG', 'TGA'):
                with self.subTest(name=name, fmt=fmt):
                    source = self.fixture(name)
                    result = process_image(source, ProcessingOptions(
                        aspect_ratio=None, output=ORIGINAL, output_format=fmt))
                    self.assertEqual(result.error, '')
                    with Image.open(result.output) as output:
                        self.assertEqual(output.size, SIZES[name])
                        self.assertEqual(output.mode, 'RGBA')
                        self.assertEqual(output.getpixel((2, 2))[3], 0)
                        self.assertAlmostEqual(output.getpixel((40, 40))[3], 128, delta=1)

    def test_discovery_filters_recursive_scan_and_raw_exclusions(self):
        nested = self.root / 'subfolder'
        nested.mkdir()
        expected = []
        for name in SIZES:
            path = nested / name.upper()
            shutil.copyfile(FIXTURES / name, path)
            expected.append(path.resolve())
        jpeg_bytes = (FIXTURES / 'sample.jpg').read_bytes()
        for extension in ('.NEF', '.raf', '.cr2', '.cr3', '.arw', '.dng', '.orf', '.rw2',
                          '.psd', '.psb', '.exr', '.svg', '.pdf', '.ai'):
            path = nested / ('unsupported' + extension)
            path.write_bytes(jpeg_bytes)
            self.assertTrue(process_image(path).error)
        for name in (OUTPUT_DIR, 'PhotoCrop_Export', '4x3_cropped'):
            generated = nested / name
            generated.mkdir()
            shutil.copyfile(FIXTURES / 'oriented.heic', generated / 'ignored.heic')
        self.assertEqual(discover([self.root]).files, [])
        self.assertEqual(set(discover([self.root], recursive=True).files), set(expected))
        self.assertFalse(discover([nested / 'unsupported.NEF']).files)

    def test_unlisted_decoder_cannot_enter_through_supported_extension(self):
        path = self.root / 'disguised.png'
        Image.new('RGB', (32, 32)).save(path, format='PPM')
        self.assertTrue(process_image(path).error)

    def test_corrupt_metadata_does_not_reject_valid_pixels(self):
        source = self.fixture('sample.png')
        # EXIF orientation parsing can fail independently of pixel decoding.
        with patch('cropper.input_formats.ImageOps.exif_transpose', side_effect=ValueError('bad EXIF')):
            result = process_image(source)
            self.assertEqual(result.error, '')
        image = load_primary_image(source)
        image.info['dpi'] = 'invalid metadata'
        with patch('cropper.processing.load_primary_image', return_value=image):
            result = process_image(source)
            self.assertEqual(result.error, '')
            with Image.open(result.output) as output:
                output.load()
                self.assertEqual(output.size, (85, 64))


class InputFormatGuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_picker_drop_preview_and_worker_with_all_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = []
            for name in SIZES:
                path = root / name
                shutil.copyfile(FIXTURES / name, path)
                paths.append(path)
            raw = root / 'excluded.NEF'
            raw.write_bytes(b'not supported')
            settings = QSettings(str(root / 'settings.ini'), QSettings.Format.IniFormat)
            window = MainWindow(language='en', settings=settings)
            window.show()
            try:
                for language in ('en', 'fr', 'ja'):
                    for extension in EXTENSIONS:
                        self.assertIn('*' + extension, tr('image_filter', language))
                    self.assertNotIn('*.nef', tr('image_filter', language))
                mime = QMimeData()
                mime.setUrls([QUrl.fromLocalFile(str(path)) for path in paths + [raw]])
                drop = QDropEvent(QPointF(20, 20), Qt.DropAction.CopyAction, mime,
                                 Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier)
                window.drop.dropEvent(drop)

                def wait_idle():
                    deadline = time.monotonic() + 30
                    while window.busy and time.monotonic() < deadline:
                        self.app.processEvents()
                        time.sleep(0.005)
                    self.assertFalse(window.busy)

                wait_idle()
                self.assertEqual(set(window.paths), set(paths))
                for row, path in enumerate(window.paths):
                    window.table.selectRow(row)
                    self.app.processEvents()
                    self.assertEqual(window.preview.source_size, SIZES[path.name])
                    self.assertIsNotNone(window.preview.pixmap)
                    self.assertFalse(window.preview.pixmap.isNull())
                window.process.click()
                wait_idle()
                self.assertEqual((window.processed, window.errors), (len(paths), 0))
            finally:
                if window.worker is not None:
                    window.worker.wait()
                window.close()
