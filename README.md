# Cropperio 2.3.0

**Drop. Crop. Export. Voilà.**

A lightweight open-source Windows utility for fast batch image cropping and resizing.

Choose a ratio, select an output size, preview the crop, and process your images without opening a full photo editor.

## Download for Windows

**Recommended release:** Cropperio 2.3.0

- **Release:** [Cropperio 2.3.0](https://github.com/papagori/cropperio/releases/tag/v2.3.0)
- **Installer:** [Download Cropperio_Setup.exe](https://github.com/papagori/cropperio/releases/download/v2.3.0/Cropperio_Setup.exe)
- **Installer SHA-256:** `273fa4c74a8511c581e0516a30c3dba3f81321d49ab583efdd0b33fe6c2f7ca9`
- **Standalone:** [Download Cropperio.exe](https://github.com/papagori/cropperio/releases/download/v2.3.0/Cropperio.exe)
- **Standalone SHA-256:** `4d42aa6687b581a5e02ae6135b2adca3b7eb00436d727fafa9f121a95ddf4a21`

Cropperio is the new name of PhotoCrop. The historical [v2.2.2 release](https://github.com/papagori/cropperio/releases/tag/v2.2.2) remains available under its original asset filenames. The installer is available in **English**, **Français**, and **日本語**.

## For users

The Windows installer includes everything required to run Cropperio, including HEIC/HEIF decoding. You do **not** need to install Python, PySide6, Pillow, a Windows HEIF codec, a Microsoft Store extension, libheif, the Microsoft Visual C++ Runtime, PyInstaller, or Inno Setup.

### Features

- Drag and drop image files or folders, with optional recursive folder scanning.
- Process many images in one batch without modifying the originals.
- Choose from **Original, 1:1, 3:2, 4:3, 5:4, 16:9, and 2:1** ratios.
- Use output presets that update dynamically for the selected ratio and reverse automatically for portrait images.
- Keep the largest possible crop with **Maximum Resolution**, or choose a standard output size.
- Preview the crop before processing, with an overlay showing the areas that will be removed.
- Export to **JPEG, PNG, or TGA**; PNG and TGA preserve source alpha transparency.
- Apply EXIF orientation before crop calculations.
- Preserve compatible ICC profiles and relevant metadata where supported.
- Resize in a single high-quality **LANCZOS** pass.
- Avoid upscaling by default, with an option to allow it when needed.
- Save exports beside each source in a `Cropperio_Export` folder.
- Optionally open the first output folder automatically after a successful batch.
- Switch between **Dark, Light, and Classic** themes; Classic uses its own retro low-color pixel icons.
- Use the application in **English**, **Français**, or **日本語**.

### Usage

1. Drag image files or a folder into Cropperio.
2. Select an aspect ratio.
3. Keep **Maximum Resolution** or select one of the sizes offered for that ratio.
4. Select JPEG, PNG, or TGA output.
5. Check the crop preview and overlay.
6. Click **Process**.
7. Find the exported files in `Cropperio_Export` beside the source images.

On first launch, Cropperio starts with **4:3** and **Maximum Resolution** selected. Choosing **Original** disables cropping and offers **Original Resolution** plus 800, 1200, 1600, 2000, 3000, 4000, 5000, 6000, and 8000 px long-edge choices.

For cropped ratios, **Maximum Resolution** keeps the largest centered crop without resizing. Standard presets depend on the selected ratio. If a requested size exceeds the available cropped image, Cropperio keeps the maximum available resolution unless **Allow Upscaling** is enabled.

### Smaller sizes and Custom

All earlier presets remain. These smaller choices are now included, without duplicates:

| Ratio | Added sizes (landscape) |
| --- | --- |
| 1:1 | 512 x 512 |
| 3:2 | 600 x 400, 900 x 600, 1200 x 800, 1800 x 1200 |
| 4:3 | 640 x 480, 800 x 600, 1200 x 900, 1600 x 1200, 2000 x 1500 |
| 5:4 | 800 x 640, 1200 x 960, 1600 x 1280, 2000 x 1600 |
| 16:9 | 640 x 360, 1280 x 720, 1600 x 900 |
| 2:1 | 800 x 400, 1200 x 600, 1600 x 800, 2400 x 1200 |
| Original | 800, 1200 and 1600 px long edge |

Select **Custom…** in Output Size to show a compact dimension row. Choose
**Width** or **Height**, then enter a whole number from **1 to 16000 px**.
The chosen dimension stays fixed; the other is calculated automatically:

| 4:3 request | Landscape output | Portrait output |
| --- | --- | --- |
| Width 1200 | 1200 x 900 | 1200 x 1600 |
| Height 1200 | 1600 x 1200 | 900 x 1200 |

With **Original**, Custom uses each source image's actual proportions. A mixed
batch therefore keeps the chosen width or height while calculating the other
individually. Source/Crop/Output in the preview updates immediately when the
dimension, value, ratio or selected image changes. Custom uses the same
single-pass LANCZOS pipeline and no-upscaling rule as normal presets.
The last Custom dimension and value are remembered; startup still defaults to
4:3 and Maximum Resolution.

The header and compact startup splash share the same Cropperio identity.
The splash is shown before image-library/main-window imports and closes as
soon as the application is ready, without a minimum display duration.
Process uses a drawn magic wand, with a pixel variant for Classic.

Existing filenames receive `_2`, `_3`, and subsequent suffixes. Current and legacy generated output folders are excluded from input scanning. The optional automatic folder opening occurs once, after a successful batch.

### Supported input formats

- JPEG (`.jpg`, `.jpeg`)
- PNG (`.png`)
- TIFF (`.tif`, `.tiff`)
- WebP (`.webp`)
- BMP (`.bmp`)
- HEIC / HEIF (`.heic`, `.heif`)
- AVIF (`.avif`)
- GIF (`.gif`)
- Windows icons (`.ico`, largest embedded representation)

Only one static image is processed: the first frame of GIF, AVIF and other animated inputs, the first page of multipage TIFF, and the primary image of HEIC/HEIF. HEIF depth/auxiliary images and Live Photo motion are not processed. No page or frame selection is needed.

### Output formats

JPEG, PNG and TGA only.

JPEG export uses quality 100, 4:4:4 sampling, and optimization; transparency is composited onto white. PNG is lossless, and PNG/TGA retain source alpha. Compatible ICC profiles, EXIF data, and DPI metadata are retained where the selected output format supports them.

### Not supported

Camera RAW files (including NEF, RAF, CR2/CR3, ARW, DNG, ORF and RW2) and specialized formats such as PSD/PSB, EXR, SVG, PDF and AI are not supported.

## For developers / Running from source

Python **3.10 or newer** is required only when running or developing Cropperio from source.

The Windows build is validated with Python 3.10.6, Pillow 12.3.0 and
`pillow-heif==1.8.1` (Python >=3.10, Pillow >=11.1). AVIF uses Pillow's native
decoder; no additional AVIF plugin is installed.

```powershell
git clone https://github.com/papagori/cropperio.git
cd cropperio
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### Tests and validation

Run the automated suite with:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Cropperio 2.3.0 release validation includes:

- **61 automated tests**, retaining the previous 45 tests and adding Custom sizing, presets, splash, branding and icon coverage.
- Frozen `Cropperio.exe` validation through its packaged self-test.
- Normal startup/splash checks in Python, frozen and installed modes.
- Installer install/run/uninstall validation in an isolated location.
- Real HEIC/HEIF and AVIF processing in the frozen executable and the installed application, using bundled native libraries.
- JPEG, PNG, and TGA output, including PNG/TGA alpha handling.
- The three application and installer languages: **English, Français, 日本語**.
- The three themes: **Dark, Light, Classic**.
- Crop geometry, dynamic presets, portrait inversion, preview dimensions, EXIF orientation, ICC/metadata handling, no-upscaling behavior, single-pass LANCZOS resizing, drag and drop, background batches, and output-folder behavior.

See [TEST_REPORT.md](TEST_REPORT.md) for the validation summary and fixture provenance in [tests/fixtures/input_formats/README.md](tests/fixtures/input_formats/README.md).

### Windows executable and installer builds

Install the development dependencies and run the complete build:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

The build script generates the shared icon, runs the automated suite, builds the one-file `dist\Cropperio.exe` binary with PyInstaller, and runs its frozen self-test, including HEIC/HEIF and AVIF. If Inno Setup 6 is installed, the script also builds `dist\Cropperio_Setup.exe` from `installer\Cropperio.iss`.

PyInstaller bundles the pillow-heif wheel's native DLLs and licenses, plus small self-test inputs. The installed application decodes HEIC directly through libheif/libde265.

To build only the executable with PyInstaller:

```powershell
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean Cropperio.spec
```

To compile the installer directly with Inno Setup 6 after building the executable:

```powershell
ISCC.exe /DAppVersion=2.3.0 installer\Cropperio.iss
```

The installer can be validated with a silent isolated install, frozen application self-test, and uninstall:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\test_installer.ps1
```

The release version is defined in `cropper/version.py` and reused by the application, Windows executable metadata, and installer build.

### Project structure

- `main.py`: application entry point and standalone self-test switch.
- `cropper/gui.py`: interface, dynamic menus, preview, and worker thread.
- `cropper/settings.py`: ratio-specific output catalog and processing options.
- `cropper/startup.py`, `cropper/splash.py`: early branded splash and startup validation.
- `cropper/branding.py`, `cropper/icons.py`: shared product copy and drawn modern wand.
- `cropper/geometry.py`: crop and output dimension calculations.
- `cropper/processing.py`: EXIF orientation, cropping, and single-pass resize pipeline.
- `cropper/export.py`: JPEG/PNG/TGA color, alpha, metadata, and output handling.
- `cropper/i18n.py`: English, Français, and 日本語 application text catalogs.
- `cropper/discovery.py`: input discovery and filtering.
- `cropper/input_formats.py`: supported input catalog and shared primary-image loader.
- `cropper/themes.py`: Dark, Light, and Classic theme definitions.
- `cropper/classic_icons.py`: retro low-color pixel icons used by the Classic theme.
- `cropper/smoke.py`: frozen executable validation.
- `cropper/version.py`: single application version source.
- `assets/cropperio.ico`: shared Windows application and installer icon.
- `Cropperio.spec`: PyInstaller configuration for the current technical binary name.
- `installer/Cropperio.iss`: Inno Setup installer configuration.
- `tools/test_installer.ps1`: isolated install/run/uninstall distribution test.
- `tests/`: automated test suite.

## License

Cropperio is licensed under the **GNU General Public License v3.0 only** (`GPL-3.0-only`). See [LICENSE](LICENSE) for the full license text.
