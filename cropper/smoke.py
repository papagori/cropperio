"""Opt-in standalone build verification with temporary synthetic inputs."""
import json
import shutil
import sys
import tempfile
import time
import traceback
from pathlib import Path

import PIL
import PySide6
import pillow_heif
import _pillow_heif
from PIL import Image, ImageChops, features
from PySide6.QtCore import QLibraryInfo, QSettings
from PySide6.QtWidgets import QApplication
from .branding import TAGLINE, DESCRIPTION

from .gui import MainWindow
from .discovery import OUTPUT_DIR
from .input_formats import EXTENSIONS
from .input_formats import load_primary_image
from .geometry import crop_size, image_options, output_size
from .resources import resource_path
from .version import __version__


def run(report_path):
    report_path = Path(report_path).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    frozen = bool(getattr(sys, 'frozen', False))
    report = {'passed': False, 'frozen': frozen, 'version': __version__,
              'pillow': PIL.__version__, 'pyside6': PySide6.__version__, 'batches': [],
              'pillow_heif': pillow_heif.__version__,
              'heif_backend': pillow_heif.libheif_info(),
              'native_avif': features.check('avif'),
              'runtime': {
                  'executable': Path(sys.executable).name,
                  'external_python_required': False,
                  'icon_bundled': resource_path('assets/cropperio.ico').is_file(),
                  'qt_plugins_available': Path(
                      QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)).is_dir(),
              }}
    app = QApplication.instance() or QApplication([])
    app.setStyle('Fusion')
    # Validation must not change the user's language/theme/folder preference.
    settings_directory = tempfile.TemporaryDirectory(prefix='cropperio-smoke-settings-')
    settings = QSettings(str(Path(settings_directory.name) / 'settings.ini'), QSettings.Format.IniFormat)
    window = MainWindow(language='en', theme='dark', settings=settings)

    def wait_idle():
        deadline = time.monotonic() + 30
        while window.busy and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.005)
        if window.busy:
            raise TimeoutError('Qt worker did not complete within 30 seconds')

    def select_output(key):
        for index in range(window.output_size.count()):
            preset = window.output_size.itemData(index)
            if preset is not None and preset.key == key:
                window.output_size.setCurrentIndex(index)
                return
        raise AssertionError(f'Missing preset {key}')

    try:
        if frozen:
            assert Path(sys.executable).name.lower() == 'cropperio.exe'
            assert report['runtime']['icon_bundled']
            assert report['runtime']['qt_plugins_available']
            assert Path(_pillow_heif.__file__).is_relative_to(Path(sys._MEIPASS))
        assert report['native_avif']
        assert report['heif_backend']['decoders']
        with tempfile.TemporaryDirectory(prefix='cropperio-') as directory:
            root = Path(directory) / 'Été 東京'
            root.mkdir()
            Image.new('RGB', (600, 400), 'steelblue').save(root / 'landscape.jpg')
            Image.new('RGBA', (400, 600), (255, 128, 30, 128)).save(root / 'portrait.png')
            (root / 'broken.jpg').write_bytes(b'intentionally corrupt test image')
            window.show()
            for language, expected in (('en', 'Process'), ('fr', 'Traiter'), ('ja', '処理開始')):
                window.language_combo.setCurrentIndex(window.language_combo.findData(language))
                assert window.process.text() == expected
            for theme in ('dark', 'light', 'classic'):
                window.theme_combo.setCurrentIndex(window.theme_combo.findData(theme))
                assert window.theme == theme and window.styleSheet()
            report['ui'] = {'languages': ['en', 'fr', 'ja'],
                            'themes': ['dark', 'light', 'classic'],
                            'footer': window.footer_gpl.text(),
                            'github': 'https://github.com/papagori/cropperio',
                            'tagline': window.tagline.text(),
                            'description': window.subtitle.text()}
            assert window.tagline.text() == TAGLINE
            assert window.subtitle.text() == DESCRIPTION
            assert not window.process.icon().isNull()
            window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
            window.theme_combo.setCurrentIndex(window.theme_combo.findData('dark'))
            window.add_paths([root])
            wait_idle()
            assert len(window.paths) == 3
            window.aspect.setCurrentText('16:9')
            for batch, key, upscaling, expected in (
                (1, 'maximum', False, (600, 338)),
                (2, 'exact_1920_1080', True, (1920, 1080)),
                (3, 'exact_2400_1600', True, (2400, 1600)),
            ):
                if batch == 3:
                    window.aspect.setCurrentText('3:2')
                select_output(key)
                window.upscaling.setChecked(upscaling)
                assert window.aspect.isEnabled()
                window.process.click()
                wait_idle()
                assert (window.processed, window.errors) == (2, 1)
                suffix = '' if batch == 1 else f'_{batch}'
                for name, size in (('landscape', expected), ('portrait', expected[::-1])):
                    with Image.open(root / 'Cropperio_Export' / f'{name}{suffix}.jpg') as result:
                        assert result.size == size, (result.size, size)
                        assert result.format == 'JPEG'
                report['batches'].append({'preset': key, 'allow_upscaling': upscaling,
                    'landscape': expected, 'portrait': expected[::-1], 'processed': 2, 'expected_errors': 1})
            window.aspect.setCurrentText('1:1')
            select_output('exact_1024_1024')
            window.upscaling.setChecked(True)
            for output_format, extension, expected_mode in (
                ('PNG', '.png', ('RGB', 'RGBA')),
                ('TGA', '.tga', ('RGB', 'RGBA')),
            ):
                window.output_format.setCurrentText(output_format)
                window.process.click()
                wait_idle()
                assert (window.processed, window.errors) == (2, 1)
                for name, mode in zip(('landscape', 'portrait'), expected_mode):
                    with Image.open(root / 'Cropperio_Export' / f'{name}{extension}') as result:
                        assert result.size == (1024, 1024)
                        assert result.format == output_format
                        assert result.mode == mode
                report['batches'].append({'preset': 'exact_1024_1024',
                    'allow_upscaling': True, 'format': output_format,
                    'landscape': (1024, 1024), 'portrait': (1024, 1024),
                    'processed': 2, 'expected_errors': 1})

            # Decode versioned fixtures (not files encoded by this executable).
            # This catches missing native HEVC/AVIF libraries after packaging.
            fixture_root = (resource_path('validation-inputs') if frozen else
                            resource_path('tests/fixtures/input_formats'))
            input_root = root / 'formats'
            input_root.mkdir()
            for fixture in fixture_root.iterdir():
                if fixture.suffix.lower() in EXTENSIONS:
                    shutil.copyfile(fixture, input_root / fixture.name)
            shutil.copyfile(input_root / 'sample.jpg', input_root / 'unsupported.NEF')
            window.clear.click()
            window.add_paths([input_root])
            wait_idle()
            assert len(window.paths) == 14
            assert all(path.suffix.lower() in EXTENSIONS for path in window.paths)
            window.aspect.setCurrentIndex(window.aspect.findData(None))
            select_output('original')
            expected_sizes = {'primary-second.heif': (80, 120), 'alpha.avif': (80, 120),
                              'sample.ico': (64, 64)}
            input_checks = []
            for row, path in enumerate(window.paths):
                size = expected_sizes.get(path.name, (96, 64))
                window.table.selectRow(row)
                app.processEvents()
                assert window.preview.source_size == size, path.name
                assert window.preview.pixmap and not window.preview.pixmap.isNull(), path.name
                input_checks.append({'file': path.name, 'size': size, 'preview': True})
            for output_format, extension in (('JPEG', '.jpg'), ('PNG', '.png'), ('TGA', '.tga')):
                window.output_format.setCurrentText(output_format)
                window.process.click()
                wait_idle()
                assert (window.processed, window.errors) == (14, 0)
                for check in input_checks:
                    path = input_root / OUTPUT_DIR / (Path(check['file']).stem + extension)
                    # sample.jpg/jpeg/png/etc share a stem; collision suffixes
                    # are validated by the baseline batches. Use unique fixtures
                    # for detailed codec/alpha/first-image output checks here.
                    if check['file'].startswith('sample.'):
                        continue
                    with Image.open(path) as output:
                        output.load()
                        assert output.size == check['size'], check['file']
                        assert output.format == output_format
                        if check['file'] in ('oriented.heic', 'pages.tiff', 'sequence.avif'):
                            red = output.convert('RGB').getpixel((10, 10))
                            assert red[0] > 200 and red[1] < 50, (check['file'], red)
                        if check['file'] in ('primary-second.heif', 'alpha.avif', 'animated.gif'):
                            if output_format != 'JPEG':
                                assert output.mode == 'RGBA'
                                assert output.getpixel((2, 2))[3] == 0
                            else:
                                assert output.getpixel((2, 2)) == (255, 255, 255)
            report['input_validation'] = {'files': input_checks,
                                          'output_formats': ['JPEG', 'PNG', 'TGA'],
                                          'raw_ignored': True,
                                          'heif_binding': Path(_pillow_heif.__file__).name,
                                          'windows_codec_required': False}
            custom_checks = []
            window.upscaling.setChecked(False)
            window.output_format.setCurrentText('PNG')
            for ratio in ('4:3', 'Original'):
                window.aspect.setCurrentIndex(0 if ratio == 'Original' else window.aspect.findText(ratio))
                select_output('custom')
                assert window.custom_controls.isVisible()
                for axis, value in (('width', 32), ('height', 24)):
                    window.custom_dimension.setCurrentIndex(window.custom_dimension.findData(axis))
                    window.custom_value.setValue(value)
                    window.process.click()
                    wait_idle()
                    assert (window.processed, window.errors) == (14, 0)
                    for row, check in enumerate(input_checks):
                        width, height = check['size']
                        a, b = ((width, height) if ratio == 'Original' else
                                (3, 4) if height > width else (4, 3))
                        expected = ((value, max(1, round(value * b / a))) if axis == 'width' else
                                    (max(1, round(value * a / b)), value))
                        output_path = window.table.item(row, 1).toolTip()
                        with Image.open(output_path) as output:
                            assert output.size == expected, (check['file'], ratio, axis)
                        window.table.selectRow(row)
                        app.processEvents()
                        assert f'{expected[0]} × {expected[1]}' in window.preview.details.text()
                    custom_checks.append({'ratio': ratio, 'dimension': axis,
                                          'value': value, 'processed': 14, 'errors': 0})
            report['custom_validation'] = custom_checks
            # Exercise the same manual states/snapshot in source, frozen and
            # installed builds, including the bundled HEIC/HEIF decoder.
            window.aspect.setCurrentText('2:1')
            select_output('maximum')
            interactive_checks = []
            expected_pixels = {}
            for row, path in enumerate(window.paths):
                window.table.selectRow(row)
                window.zoom_preview_crop(8 + row / 2)
                window.move_preview_crop(window.preview.canvas.crop, 10, -10)
                box = window.preview.canvas.crop
                with load_primary_image(path) as original:
                    expected_pixels[row] = original.crop(box).convert('RGBA')
                interactive_checks.append({'file': path.name, 'box': box,
                                           'output': crop_size(box)})
            window.process.click()
            wait_idle()
            assert (window.processed, window.errors) == (14, 0)
            for row, expected in expected_pixels.items():
                with Image.open(window.table.item(row, 1).toolTip()) as output:
                    assert output.size == expected.size
                    assert ImageChops.difference(expected, output.convert('RGBA')).getbbox(alpha_only=False) is None
            before_reset = len(window.manual_crops)
            window.preview.reset_crop.click()
            assert len(window.manual_crops) == before_reset - 1
            report['interactive_validation'] = {'files': interactive_checks,
                'pixel_identical': True, 'reset_is_local': True, 'processed': 14, 'errors': 0}
            window.manual_crops.clear()
            window.aspect.setCurrentText('1:1')
            select_output('maximum')
            ratios = (None, '4:3', '2:1', 'Original')
            for row in range(len(window.paths)):
                window.table.selectRow(row)
                key = ratios[row % len(ratios)]
                window.preview.image_ratio.setCurrentIndex(window.preview.image_ratio.findData(key))
                if key is not None:
                    window.zoom_preview_crop(4 + row / 2)
                    window.move_preview_crop(window.preview.canvas.crop, 5, -5)
            ratio_checks = []
            window.upscaling.setChecked(True)
            for preset, axis, value in (('maximum', None, None), ('exact_512_512', None, None),
                                         ('custom', 'width', 32), ('custom', 'height', 24)):
                select_output(preset)
                if axis:
                    window.custom_dimension.setCurrentIndex(window.custom_dimension.findData(axis))
                    window.custom_value.setValue(value)
                expected_by_row = {}
                files = []
                for row, path in enumerate(window.paths):
                    window.table.selectRow(row)
                    box = window.preview.canvas.crop
                    size = window.preview.source_size
                    options = image_options(size, window.current_options(), window.manual_crops.get(path))
                    target, _ = output_size(crop_size(box), options, portrait=size[1] > size[0])
                    with load_primary_image(path) as source:
                        pixels = source.crop(box).convert('RGBA')
                    if pixels.size != target:
                        pixels = pixels.resize(target, Image.Resampling.LANCZOS)
                    expected_by_row[row] = pixels
                    files.append({'file': path.name, 'ratio': ratios[row % 4], 'output': target})
                window.process.click()
                wait_idle()
                assert (window.processed, window.errors) == (14, 0)
                for row, expected in expected_by_row.items():
                    with Image.open(window.table.item(row, 1).toolTip()) as output:
                        assert output.size == expected.size
                        assert ImageChops.difference(expected, output.convert('RGBA')).getbbox(alpha_only=False) is None
                ratio_checks.append({'preset': preset, 'axis': axis, 'files': files,
                                     'processed': 14, 'errors': 0, 'pixel_identical': True})
            report['ratio_validation'] = ratio_checks
            window.grab().save(str(report_path.with_suffix('.png')))
            report['passed'] = True
    except Exception:
        report['error'] = traceback.format_exc()
    finally:
        if window.worker is not None:
            window.worker.wait()
            app.processEvents()
        window.close()
        settings_directory.cleanup()
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    return 0 if report['passed'] else 1
