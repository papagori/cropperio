# Cropperio validation

Rename validation completed on 2026-10-29. The existing repository was renamed to
https://github.com/papagori/cropperio and the local HTTPS remote was updated.
Starting commit: `c89dfe847eeae5b240aceb4dedc8f6065bdcbfb0`.
At validation time, `main` tracked `origin/main` at that starting commit.
Fetch and push dry-run succeeded. The rebranding was prepared locally
without pushing code changes.

The existing `v2.2.2` release is still published under its historical title
and asset filenames. Its tag and assets were neither replaced nor deleted.
No new release was created. The new Cropperio builds are local artifacts.
The `main` and `feat/windows-ui-packaging` branches remain accessible.

Validated on Windows x64 with Python 3.10.6, Pillow 12.3.0, PySide6 6.11.0, PyInstaller 6.20.0, and Inno Setup 6.7.3.

## Automated validation

Run from the repository root:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

All **34 tests passed**. Coverage includes crop and resize geometry, the 1024/2048/4096/8192 square presets, portrait inversion, upscaling on/off, one-pass LANCZOS resizing, JPEG/PNG/TGA export, PNG/TGA alpha, metadata and color handling, English/French/Japanese UI, Dark/Light/Classic themes, language and theme persistence, stable panel geometry, emphasized dropdowns, Classic-only pixel icons, themed toggles, GPL footer, GitHub link dispatch, output-folder timing, input discovery, Qt drag and drop, preview dimensions, worker batches, and Windows distribution configuration. A dedicated matrix verifies that 1:1, 4:3, and 16:9 exports in JPEG, PNG, and TGA all use `Cropperio_Export`.

New exports are written beside each source folder under `Cropperio_Export`. Collision suffixing remains active, source originals remain untouched, and the current directory plus legacy `PhotoCrop_Export` and `4x3_cropped` directories are excluded from recursive discovery. The batch completion test confirms that Explorer receives the first processed group's `Cropperio_Export` path once, after processing finishes.

The centered crop and preview geometry remain shared, and every requested resize still uses one direct LANCZOS pass.

A separate isolated settings check verified that language, theme, and the
open-output-folder preference are copied from the legacy settings only when
missing in the new settings. Existing Cropperio preferences take precedence,
and the legacy settings file remains unchanged.

## Frozen executable

`Cropperio.exe` was built from the versioned `Cropperio.spec` as a one-file windowed application. Its explicit `--self-test` completed with exit code 0 and reported:

- `passed: true`
- `frozen: true`
- version `2.2.2`
- bundled application icon found
- Qt plugin directory found
- no external Python required

The frozen self-test verified the three languages, three themes, footer, and GitHub target. Its five processing batches produced the expected landscape and portrait outputs in JPEG, PNG, and TGA and continued correctly after a deliberately corrupt input.

The earlier packaging archive inspection covered the following runtime dependencies; the dependency configuration is unchanged by the rename:

- `python310.dll` and the Python standard library archive
- PySide6 and Qt runtime DLLs
- the Windows platform plugin `qwindows.dll`
- Qt image format plugins for JPEG, TIFF, WEBP, ICO, GIF, and SVG
- Pillow imaging, color-management, AVIF, and WEBP extensions
- `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll`, and required MSVC C++ DLLs
- `assets/cropperio.ico`

The outer executable imports only standard Windows system libraries such as KERNEL32, USER32, GDI32, ADVAPI32, and COMCTL32. A separate Microsoft Visual C++ Redistributable installation is not required.

## Installer

Inno Setup produced `dist\Cropperio_Setup.exe` with English, French, and Japanese choices. A fresh choice initializes the application language through its normal persisted setting. The installer was tested with a silent isolated installation under the system temporary directory, without using the development virtual environment. The installed `Cropperio.exe` passed the same frozen self-test, the uninstaller was present, and silent uninstallation removed the test installation directory completely.

## Visual review

Native Windows captures were generated for empty and populated/preview states in all three themes. The reviewed combinations were Dark/English, Light/French, and Classic/Japanese. Additional Light captures verify the focused dropdown and its open menu. Header controls, settings, file list, preview, progress, status, log, and footer retain stable alignment between empty and populated states. Classic uses its own original low-color pixel icons; Dark and Light continue to use the modern Qt/Windows set.

Inno Setup is required only on the development machine to compile the installer. It is not installed or invoked on an end-user machine.

Generated executables, installers, reports, screenshots, caches, virtual environments, and local backups remain excluded from Git.
