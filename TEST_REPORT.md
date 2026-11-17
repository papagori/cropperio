# Cropperio 2.4.1 — Final release validation

Validation date: 2026-11-17, Windows x64.

- All 120 automated tests passed (23.117 seconds), including existing crop,
  resize, image format, interactive framing and ratio-override regressions.
- All 9 localization tests also passed with native Windows Qt rendering
  (37.788 seconds). All six catalogs have 85/85 keys with matching placeholders:
  EN, FR, JA, ZH-CN, RU and DE. Language selection/restart persistence, Qt dialog
  catalogs and all 18 language/theme combinations pass.
- Source self-test and startup probe passed at version 2.4.1; startup defers image
  codec imports and closes the splash when the main window is ready.
- A real Qt mouse activation reached Windows' actual default-browser launcher,
  which returned success for https://www.matthieutuffet.com/software/.
  Browser content was not visually inspected by the assistant in this run.
- Dependency validation (`pip check`) passed.
- The user confirmed manual installer/application visual QA with no visible
  layout, translation or glyph issues. The previous Computer Use limitation is
  explicitly accepted as non-blocking. This is user-provided visual acceptance;
  see [INSTALLER_VISUAL_QA_2.4.1.md](INSTALLER_VISUAL_QA_2.4.1.md).
- The changes since v2.4.0 are limited to six-language localization, the discreet
  footer catalog link, supporting layout/font safeguards, packaging, tests and
  release documentation. Image processing algorithms and dependencies are unchanged.
- Final binaries are rebuilt after the release commit, using `build.ps1`, and
  validated through frozen startup/self-tests and `tools/test_installer.ps1`.
  The exact commit, final build results, file sizes and SHA-256 hashes are recorded
  with the GitHub Release and its SHA256SUMS.txt asset, avoiding self-referential
  source hashes in this document. Publication requires those checks to pass.
- SourceForge upload has no established authenticated workflow in this checkout.
  Its latest-download redirect was checked and still selected
  `v2.4.0/Cropperio_Setup.exe` before publication. Manual upload instructions and
  the same final binaries will be prepared separately; no SourceForge v2.4.1
  publication is claimed here.

Evidence (generated/ignored): `test-results/release-2.4.1-tests.log`,
`release-2.4.1-native-localization.log`, `release-2.4.1-source.json`,
`release-2.4.1-startup-source.json`, `release-2.4.1-browser.json`,
`release-2.4.1-prebuild.log`, `release-2.4.1-build.log`,
`release-2.4.1-installer.log`, `compiled-v2.json`, `startup-frozen.json`,
`installer-smoke.json`, `startup-installed.json`.

The following records are historical. Their former pending/unpublished status
and review-build hashes are superseded by the final validation and release assets.

---

# Cropperio 2.4.1 — Historical local review validation (2026-11-16)

Validated on Windows x64, 2026-11-16. Unpublished review build.

- 120 automated tests passed (111 existing tests plus 9 focused localization/link tests).
- The 9 focused tests also passed using native Windows Qt rendering.
- All six catalogs contain 85/85 keys (100%): EN, FR, JA, zh-CN, ru-RU, de-DE.
  Format placeholders, empty strings, replacement characters and duplicate literal
  keys are checked. English fallback and old locale preferences are covered.
- Language selection, localized controls/tooltips and existing result rows, restart persistence, startup
  language normalization and Qt standard-dialog catalogs pass for all six languages.
- Eighteen language/theme layout combinations pass. Every Chinese and Russian
  application catalog string is shaped using Qt's actual font fallback: no missing
  glyphs. Native captures were generated for all 18 combinations; Chinese Dark,
  Russian Light and German Classic were visually reviewed. Chinese and Russian
  splash captures were also reviewed and are readable.
- Longer descriptions wrap; the preview panel enforces its layout minimum to
  prevent overlap. Long output-size labels have complete text in their tooltip
  and dropdown. The existing window can expand to fit translated controls.
- The single footer link is beside GitHub, uses the existing accessible LinkLabel,
  and supports mouse and keyboard activation. Tests assert the exact HTTPS URL,
  no launch on startup/language switching, false-return and exception handling.
- A real mouse-activation test using Qt reached the native Windows browser launcher
  successfully. Firefox's window title changed to “Software and Plugins — Creative
  Tools by Matthieu Tuffet”. Browser content inspection was denied by Computer Use.
- PyInstaller executable built successfully; source, frozen and installed startup
  and processing self-tests passed. Packaged Qt dialog translations load for all
  five non-English languages. Existing image formats, crop, resize and export
  checks pass, including bundled HEIC/HEIF and AVIF codecs.
- Inno Setup installer compiled successfully without translation warnings. The
  final compile encountered the open review installer's file lock. The same sources
  compiled successfully into `dist/review-v2.4.1`; after closing the test process,
  that final installer was copied to the standard `dist/Cropperio_Setup.exe` path.
- Existing isolated installation/run/uninstallation test passed. Additional silent
  installs in paths containing Chinese and Cyrillic characters passed for Chinese,
  Russian and German, with each correct initial registry language and successful
  installed startup. Prior language preferences were restored after the tests.
- Static installer-font checks shaped 296 entries each for Chinese, Russian and
  German, plus their three Cropperio-specific messages each, with no missing glyphs;
  Microsoft YaHei UI and Segoe UI are installed.
  These checks do not establish native installer page layout correctness.

## Installer visual review

Pending: Computer Use rejected access to Cropperio_Setup.tmp with
“Computer Use was not approved to use cropperio_setup.tmp”. Native installer page
rendering and overflow in Chinese, Russian and German must be visually reviewed
before release. **v2.4.1 remains unpublished pending this final validation.**

Follow [the manual visual QA checklist](INSTALLER_VISUAL_QA_2.4.1.md), which also
records the application-identity investigation and official approval-flow retry.
The temporary child is a separate reported application identity. Its current
allow-list entry is present, but the latest official launcher attempt exposed no
targetable installer window. The remaining cause is unconfirmed; the installer
has not been changed to work around Computer Use restrictions.

## Review artifacts

- `dist/Cropperio.exe`: 56,733,017 bytes, SHA-256
  `4fc66ee341a5b9e2f34f6e7570e730dd1b0446d2a81f9828400493712c7e40d2`.
- `dist/Cropperio_Setup.exe`: 58,136,812 bytes, SHA-256
  `53c67ac8f9e108cf4b4783824809f52ba4cd8594c1a5b2f1c94d55ca4b080ca9`.
- Both Windows product versions are 2.4.1.
- Evidence (generated/ignored): `test-results/v2.4.1-build.log`,
  `v2.4.1-localization-native.log`, `v2.4.1-source-smoke.json`,
  `v2.4.1-installer-build.log`, `v2.4.1-installer-test.log`,
  `v2.4.1-installer-languages.json`, `v2.4.1-installer-fonts.json`,
  `v2.4.1-browser.json`, `compiled-v2.json`, `startup-frozen.json`,
  `installer-smoke.json`, `startup-installed*.json`, `ui-*.png`, `splash-*.png`.

## Modified files

- `cropper/i18n.py`: six complete catalogs, link/startup/presentation strings,
  locale aliases and lazy image-filter formatting to retain deferred codec imports.
- `cropper/gui.py`: language choices, translated Qt dialogs, footer link with safe
  browser failure handling, description wrapping preview layout constraints and live translation of existing result rows.
- `cropper/branding.py`, `splash.py`, `startup.py`, `themes.py`: shared translated
  startup text, six-language startup selection and preferred Chinese UI fonts.
- `cropper/version.py`: single release version updated to 2.4.1.
- `cropper/smoke.py`: packaged six-language, link and Qt translation checks.
- `installer/Cropperio.iss`: six language entries, custom translated messages,
  Chinese font fallback and installer-to-app preference mapping.
- `installer/ChineseSimplified.isl`, `ChineseOverrides.isl`, `TRANSLATIONS.md`:
  pinned official Chinese catalog, font settings and provenance.
- `installer/JapaneseOverrides.isl`: UTF-8 BOM for explicit Unicode detection;
  original Japanese font settings unchanged.
- `tests/test_localization.py`: 9 focused regression tests.
- `tests/test_options.py`, `test_custom_ui.py`, `test_distribution.py`: updated
  assertions for six catalogs, localized presentation and installer configuration.
- `tools/capture_ui.py`: captures all 18 language/theme combinations.
- `README.md`, `RELEASE_NOTES_2.4.1.md`, `TEST_REPORT.md`: unreleased status,
  proposed notes, validation evidence and limitations. Published download links
  remain on v2.4.0.

## Limits

Native Windows file-picker buttons follow Windows display language. Qt fallback
file dialogs use the application's selected language. External OS/codec diagnostics
and the original English GPL legal text remain verbatim. Existing log history keeps
the language in which its entries were generated. A native-speaker editorial review
is still advisable. Nothing was committed, tagged, pushed or published.

---

# Cropperio 2.4.0 — Interactive Crop validation

Validated on Windows x64, 2026-10-29. Functional acceptance, including physical mouse/touchpad testing, was confirmed by the user before the release freeze. The 2.3.0 report below is retained as historical context. Final binary hashes and exact sizes are recorded in the [2.4.0 release notes](https://github.com/papagori/cropperio/releases/tag/v2.4.0) after rebuilding and validating the release commit.

## Per-image Ratio Override addition

- Version remains **2.4.0**. No dependency, format, preset catalog, theme, language, splash, drag or wheel algorithm change.
- `ManualCrop` now also stores `ratio_override` and `framing`. `None` inherits the global ratio, while the explicit string `Original` selects the source ratio. `framing=False` represents a ratio-only override with the exact automatic crop, including historical odd-pixel centering. Sparse states remain keyed by source `Path` and copied into the worker snapshot.
- Shared `image_options` resolves effective ratio and output request in preview and processing. Numeric presets keep their long edge, derive the short edge from the individual ratio with nearest-pixel rounding, and reverse dimensions for portrait sources. Original uses oriented source proportions. Custom keeps its requested width/height. Maximum/Original Resolution performs no resize. Inherited images retain previous output calculations unchanged.
- The compact EN/FR/JA Image ratio selector displays the current batch ratio in its inherit choice. An explicit selected ratio is the override indicator. Changing it preserves valid center/zoom, then clamps and enforces output constraints. A global change leaves explicit overrides intact. Returning to batch removes only the ratio override; valid manual framing remains.
- Reset crop is unambiguous: center and maximize the current image using its effective ratio, retaining the ratio override. The tooltip explains how to remove the ratio separately. Reset becomes disabled for an already automatic crop even if a ratio override exists.
- **111 tests passed**, including all previous **92** and **19 new tests**. The 19 ratio tests also passed separately with native Windows Qt rendering: square batch, 4:3/2:1/Original overrides, selection restore, independent framing, global changes, override removal, Reset, unselected minimum constraints, numeric/Custom/Maximum exports, landscape/portrait, HEIC and exact preview/export pixels.
- Source, frozen and installed self-tests each passed **four mixed-ratio batches of 14 images**: Maximum, numeric 512 px, Custom Width 32 px, Custom Height 24 px. Every batch contains inherited 1:1 plus 4:3, 2:1 and Original overrides. All 56 PNG exports per runtime were compared pixel for pixel with expected preview geometry, including HEIC/HEIF/AVIF fixtures.
- Rebuilt `dist/Cropperio.exe` and `dist/Cropperio_Setup.exe`; frozen startup, installed startup, isolated installation, installed frozen self-test and uninstall passed. `git diff --check` passed.
- Nine native captures exercise all theme/language combinations with a batch 1:1 and portrait override 4:3. Light/FR and Classic/JA captures were visually reviewed, alongside the automated nine-combination layout checks.
- Direct desktop input validation was attempted with the computer-use skill, but the helper returned **`failed to activate captured window`** on activation/click, including its recovery attempt. Qt GUI tests and native captures passed. The user subsequently confirmed successful physical mouse/touchpad testing and full functional acceptance before authorizing publication. The earlier Interactive Crop input results below describe the preceding implementation stage.
- New evidence: `test-results/ratio-tests.log`, `ratio-native-tests.log`, `ratio-source-smoke.json`, `ratio-build.log`, `ratio-installer.log`; refreshed `compiled-v2.json`, `installer-smoke.json`, startup reports and native UI captures.

## Interactive Crop baseline architecture and behavior

- `geometry.py`: immutable `ManualCrop(center_x, center_y, scale)` relative to the EXIF-oriented source and the largest crop for the active ratio. `resolve_crop` is the sole source of integer crop coordinates for both preview and export. Automatic `crop_box` behavior is unchanged.
- `MainWindow.manual_crops`: sparse dictionary keyed by discovered source `Path`; only interacted-with images acquire a state. Known oriented source sizes permit constraint updates on unselected images too. Selection restores each state. Reset removes manual framing for the selected image and retains any ratio override; Clear removes all session states.
- Worker receives a copied dictionary of immutable states and frozen processing options. Later UI changes cannot affect the running batch. No crop preferences are persisted across application sessions.
- Drag maps the displayed image rectangle back to oriented source coordinates, moves from the press anchor, and clamps all four edges. Open hand in the crop; closed hand while dragging; normal cursor outside. No corner/side handles.
- Wheel uses `exp(-0.04 * steps)` (about 4% per notch), with angle deltas /120 and touchpad pixel deltas /40. Continuous zoom and center prevent fractional-delta loss and cumulative pixel-rounding drift. Repaints use a cached thumbnail with no full-image decode/encode.
- Maximum is the existing automatic crop. Minimum without upscaling fits the requested preset/Custom dimensions; if the source itself is insufficient, keep the largest available crop and existing blocked-upscaling behavior. Safety floor is 16 source pixels on the short edge, capped by the source's available dimensions.
- Output/Custom changes preserve valid framing and enlarge insufficient crops around their center, clamping at the source. Ratio changes rederive dimensions from the new ratio while preserving relative center/zoom as far as valid. Integer dimensions use nearest-pixel rounding; maximum retains historical rounding exactly.
- Maximum Resolution (and Original Resolution with an interactive crop) exports the selected source pixels without a resize. Output presets/Custom use the existing single-pass LANCZOS pipeline. Formats and orientation loading are unchanged.

## Interactive Crop baseline automated and distribution results

- **92 tests pass**: the previous 61 plus 31 interactive tests. Coverage includes default geometry, horizontal/vertical/two-axis movement, all four clamps, zoom in/out, maximum/minimum, upscaling safety, 1:1 / 2:1 / 4:3 landscape and portrait, Custom width/height exports, ratio/size changes, independent crops, local reset, worker snapshot, EXIF/HEIC/HEIF and exact preview/export pixel comparisons.
- Source self-test: passed, with manual crop PNG pixel comparisons for all 14 bundled fixtures covering every supported input format.
- `Cropperio.exe` built successfully using `build.ps1`; frozen startup and frozen self-test passed, version **2.4.0**. `interactive_validation`: 14 processed, zero errors, exact pixels, local reset passed.
- `Cropperio_Setup.exe` built successfully with Inno Setup. Isolated install, installed startup, installed frozen self-test (including interactive HEIC/HEIF/AVIF), and uninstall all passed. PATH was restricted during installed tests, so developer Python/codecs were not required.
- The sandbox profile initially failed Inno Setup's `localappdata` expansion. Re-running the same isolated test in the normal Windows user context passed; no installer code workaround was introduced.
- `git diff --check`: passed at the pre-release validation checkpoint.

## Earlier Interactive Crop UI and Windows input results

- Nine native Windows captures: all combinations of Dark/Light/Classic and EN/FR/JA, with an adjusted portrait crop. The three theme/language representative captures were visually reviewed; crop border, dark overlay, dimensions and translated Reset control are visible. Automated layout checks also exercise all nine combinations at 920 × 760.
- Desktop input injection via the computer-use skill exercised left-button dragging and wheel input in the running Qt window. Landscape crop moved from `(0, 75, 900, 525)` to `(0, 127, 900, 577)`; one wheel-up notch selected `(18, 136, 883, 568)`; a two-axis drag clamped left at zero. Wheel down returned to maximum dimensions. Portrait drag changed `(75, 0, 525, 900)` to `(127, 0, 577, 900)`. HEIC preview loaded oriented at 96 × 64.
- The test desktop batch retained distinct landscape and portrait states while untouched images remained automatic. Automated batch exports verify independent framing and per-image reset.
- **Physical hardware acceptance:** Windows input injection and Qt angle/pixel-delta tests passed. Physical mouse and touchpad behavior was subsequently tested and accepted by the user before the release freeze.

Evidence (generated/ignored): `test-results/interactive-tests.log`, `interactive-build.log`, `interactive-source-smoke.json`, `compiled-v2.json`, `startup-frozen.json`, `interactive-installer.log`, `installer-setup.log`, `installer-smoke.json`, `startup-installed.json`, and `ui-{theme}-{language}-preview.png`.

## Historical Cropperio 2.3.0 validation

Validated on Windows x64 on 2026-10-29.
Base checkpoint: `52d53e112c0242df7db5d4a5f29709b1c392f36c`.
Prepared on branch `feat/input-formats-2.3.0` for the `v2.3.0` release.
Existing v2.2.2 assets are preserved.

## Environment and dependencies

- Python 3.10.6, Pillow 12.3.0, PySide6 6.11.0.
- PyInstaller 6.20.0; Inno Setup 6.7.3.
- Added `pillow-heif==1.8.1`, using its CPython 3.10 Windows x64 wheel.
- Installed wheel metadata requires Python >=3.10 and Pillow >=11.1.0.
- Bundled HEIF backend: libheif 1.23.6 with libde265 1.1.3 HEVC decoder.
- The wheel also ships libx265, which is bundled with its native dependencies.
- AVIF uses Pillow's native AVIF decoder. No AVIF plugin, RAW library or Windows codec was added.
- Existing Pillow/PySide6/PyInstaller versions were not changed. `pip check` passed.

Compatibility references: [pillow-heif 1.8.1 on PyPI](https://pypi.org/project/pillow-heif/1.8.1/)
and [official Pillow plugin documentation](https://pillow-heif.readthedocs.io/en/stable/pillow-plugin.html).

## Operational input formats

All 12 extensions passed discovery, opening, preview and batch tests:
`.jpg`, `.jpeg`, `.png`, `.tif`, `.tiff`, `.webp`, `.bmp`, `.heic`, `.heif`, `.avif`, `.gif`, `.ico`.
No requested format was abandoned. ICO uses the largest embedded representation.

- HEIC/HEIF: primary image only, including a fixture whose primary index is 1.
  Thumbnail, depth and auxiliary image loading is disabled. No Live Photo motion processing.
  The HEIF plugin handles container orientation; the normal EXIF orientation stage remains shared.
- AVIF: first frame only, through Pillow's native decoder.
- GIF: first frame only, including palette transparency. No animation reconstruction.
- Multipage TIFF: first page only, replacing the former rejection of multipage inputs.
- Other animated supported raster files likewise use their initial frame.
- RAW (NEF, RAF, CR2, CR3, ARW, DNG, ORF, RW2) and PSD/PSB, EXR, SVG, PDF, AI
  are excluded. Direct processing of these extensions also refuses them.

The shared loader is used by preview and processing. Centered crop geometry,
existing ratios/presets, Maximum Resolution and single-pass LANCZOS resizing
are retained. Output sizing now also supports Custom and smaller presets.
Preview and batch share that same sizing function. Output formats remain
JPEG, PNG and TGA. The existing high-bit-depth JPEG guard is retained.
Metadata is preserved when valid and supported; invalid EXIF or save metadata
can be discarded without losing otherwise valid pixel data.

## UI/UX additions in 2.3.0

All earlier presets are retained without duplicates. These sizes are added:

| Ratio | Added sizes |
| --- | --- |
| 1:1 | 512 x 512 |
| 3:2 | 600 x 400; 900 x 600; 1200 x 800; 1800 x 1200 |
| 4:3 | 640 x 480; 800 x 600; 1200 x 900; 1600 x 1200; 2000 x 1500 |
| 5:4 | 800 x 640; 1200 x 960; 1600 x 1280; 2000 x 1600 |
| 16:9 | 640 x 360; 1280 x 720; 1600 x 900 |
| 2:1 | 800 x 400; 1200 x 600; 1600 x 800; 2400 x 1200 |
| Original | 800; 1200; 1600 px long edge |

Maximum Resolution remains first for cropped ratios; Original Resolution remains
first for Original. Custom is last in every ratio's list.

Custom shows a compact reference-dimension row only while selected. Width/Height
and the integer value (1 to 16000 px) are remembered in the current preferences.
Invalid values are bounded/refused by the spinbox and validated by the immutable
processing request. Startup still defaults to 4:3 and Maximum Resolution.

| 4:3 request | Landscape | Portrait |
| --- | --- | --- |
| Width 1200 | 1200 x 900 | 1200 x 1600 |
| Height 1200 | 1600 x 1200 | 900 x 1200 |

Original uses each oriented source's actual proportions, independently in a mixed
batch. The other dimension is rounded to the nearest pixel (minimum one pixel).
The existing no-upscaling policy returns the maximum crop when the target would
enlarge it; Allow Upscaling enables the requested target. Preview changes
immediately and the worker captures an immutable request for the whole batch.
All resizing still enters the single existing LANCZOS call in processing.py.

The exact requested tagline and description are shared by header and splash,
including the accent in "Voilà.". The header makes the tagline stronger than
the description. Spacing and panel minimum constraints prevent overlap when
Custom is visible. Native checks cover all themes/languages and a narrow window.
Process uses a Qt-drawn white/gold wand for Dark/Light and a separate original
16-pixel low-color wand for Classic. Neither variant uses emoji/font glyphs.

The borderless splash is 460 x 258 logical pixels, centered and painted at the
screen's device-pixel ratio (native captures at 150% are 690 x 387 pixels).
It first paints a dark background, then logo, identity, version and localized
starting text. It is shown before importing gui, Pillow or pillow-heif and closes
as soon as the main window is shown. No minimum duration or fake progress is
introduced. Qt initialization and one-file bootloader extraction necessarily
precede the splash. Construction errors close it. Normal startup has no test
capture/timer overhead; the opt-in --startup-test probe follows the real path
and exits immediately after readiness.

## Automated and source validation

**61 tests passed**: all previous 45 tests retained (catalog expectations updated),
plus 16 Custom/preset/branding/icon/layout/startup tests.

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe main.py --self-test test-results\source-2.3.0.json
```

Coverage includes all input extensions, first-frame/page selection, nonzero HEIF
primary index, HEIC orientation/author/ICC preservation, GIF/HEIF/AVIF/ICO alpha,
JPEG white flattening, corrupt metadata fallback, 1:1/4:3/16:9 crops, Maximum
Resolution and resize, all three outputs, file picker filters in all three
languages, drag and drop, recursive scan exclusions, RAW refusal and disallowed
decoders behind a supported suffix. Existing geometry, theme, language,
upscaling and one-pass LANCZOS tests pass.

Fourteen small original synthetic fixtures are versioned in
`tests/fixtures/input_formats/`, with provenance and regeneration instructions.
They do not depend on private files or codecs outside the project dependencies.

The Python entry-point self-test passed. The native Windows GUI also launched
with HEIC, HEIF, AVIF, GIF and BMP inputs. Native screenshots verified the
Cropperio 2.3.0 header and Custom previews in Dark/English, Light/French and
Classic/Japanese. Width/Height, landscape/portrait and HEIC were exercised.
The small-preset menu was inspected. A narrow-window check confirms that controls,
canvas and Source/Crop/Output remain within their panels without overlap.
The native source startup probe passed with deferred imports and a closed splash.

## Frozen executable

The build script completed successfully. Its frozen self-test reported
`passed: true`, `frozen: true`, `version: 2.3.0`.

- Five original batch scenarios still pass, including JPEG/PNG/TGA and deliberate bad input.
- Fourteen versioned input fixtures each pass preview and all three output formats.
- Actual HEIC, HEIF and AVIF outputs were checked for dimensions and expected pixels/alpha.
- RAW is ignored. The HEIF extension module is loaded from the frozen extraction directory.
- Four additional Custom batches (Width/Height, 4:3/Original) each process all
  14 fixtures successfully; actual dimensions and the corresponding preview are checked.
- The normal frozen startup probe passes with imports deferred until after the
  splash, correct identity and splash closure at window readiness.
- Archive inspection confirms `_pillow_heif`, libheif, libde265, libx265,
  both pillow-heif license files and all validation fixtures are bundled.

Evidence: `test-results/compiled-v2.json` (the existing build report filename;
its content and executable version are 2.3.0).

## Installer validation

`tools/test_installer.ps1` passed the full isolated install/run/process/uninstall cycle.
The installed application's startup probe verified splash -> application readiness.
Its self-test processed real HEIC, HEIF and AVIF fixtures
and verified JPEG/PNG/TGA outputs. During launch, PATH contained only Windows
system directories, without developer Python or codec directories. HEIC decoding
uses bundled libheif/libde265 directly, not Windows HEIF/Store codecs.
The installed executable metadata and reported version both equal 2.3.0.
Silent uninstallation removed the isolated installation directory completely.
Evidence: `test-results/installer-smoke.json` (`passed: true`, `frozen: true`).
All four Custom batches also passed after installation. Startup evidence:
`test-results/startup-source-native.json`, `startup-frozen.json` and
`startup-installed.json`, all `passed: true`. Frozen and installed native splash
captures are pixel-identical. Native UI captures are `custom-dark-en.png`,
`custom-light-fr.png`, `custom-classic-ja.png`, `custom-minimum-window.png` and
`small-presets-popup.png` under test-results.

## Release artifacts

| Artifact | Bytes | MiB | SHA-256 |
| --- | ---: | ---: | --- |
| `dist/Cropperio.exe` | 56,719,467 | 54.09 | `4d42aa6687b581a5e02ae6135b2adca3b7eb00436d727fafa9f121a95ddf4a21` |
| `dist/Cropperio_Setup.exe` | 58,110,181 | 55.42 | `273fa4c74a8511c581e0516a30c3dba3f81321d49ab583efdd0b33fe6c2f7ca9` |

## Changed files

The complete 2.3.0 change set, including the input-format and UI/UX work:

- Entry point: `main.py`.
- New UI modules: `cropper/branding.py`, `cropper/icons.py`, `cropper/splash.py`, `cropper/startup.py`.
- UI/sizing: `cropper/gui.py`, `cropper/settings.py`, `cropper/geometry.py`,
  `cropper/i18n.py`, `cropper/themes.py`, `cropper/classic_icons.py`.
- Input/processing: `cropper/input_formats.py`, `cropper/discovery.py`,
  `cropper/processing.py`, `cropper/export.py`.
- Version/validation: `cropper/version.py`, `cropper/smoke.py`.
- Packaging: `requirements.txt`, `Cropperio.spec`, `build.ps1`, `tools/test_installer.ps1`.
- Tests: `tests/test_cropper.py`, `tests/test_distribution.py`, `tests/test_options.py`,
  `tests/test_input_formats.py`, `tests/test_custom_ui.py`.
- Fixtures: `tests/fixtures/input_formats/` (14 images and README),
  `tools/generate_input_fixtures.py`.
- Documentation: `README.md`, `TEST_REPORT.md`.

Builds, screenshots, generated reports and caches remain ignored by Git.
The release commit contains only the 2.3.0 code, fixtures, packaging, tests and
documentation changes. `git diff --check` passed.
