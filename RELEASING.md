# Release procedure and permanent artifact naming

Starting with **v2.4.2**, Windows distribution names contain the version:

| Version | Installer | Standalone |
| --- | --- | --- |
| 2.4.2 | `Cropperio_Setup_v2_4_2.exe` | `Cropperio_v2_4_2.exe` |
| 2.5.0 | `Cropperio_Setup_v2_5_0.exe` | `Cropperio_v2_5_0.exe` |
| 3.0.0 | `Cropperio_Setup_v3_0_0.exe` | `Cropperio_v3_0_0.exe` |

`cropper/version.py` remains the only version metadata. The dependency-free
`cropper.release_artifacts` module derives both filenames, PyInstaller's output
base name, Inno Setup's output base name and the numeric Windows version from it.
The current version remains 2.4.1. Versions through 2.4.1 retain legacy names;
existing releases, download URLs and tags must not be renamed or overwritten.
The project currently accepts stable `major.minor.patch` versions only and has
no existing prerelease convention. Invalid versions fail before packaging.

The application is still installed as **Cropperio**, with **Cropperio.exe** as
its installed filename. Inno Setup uses `DestName` to keep this stable while
reading the versioned standalone distribution file. Application ID, registry
preferences, shortcuts and installation paths stay version independent.

## Local build and validation

Preview the current names without building or changing distribution files:

```powershell
powershell -NoProfile -File .\build.ps1 -Plan
```

For a future release, update the canonical version as part of its authorized
release changes, finalize tests/documentation and build from the release commit:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
powershell -ExecutionPolicy Bypass -File .\tools\test_installer.ps1
```

The build runs the complete suite, generates the correctly named standalone
executable directly with PyInstaller, runs frozen startup/processing checks and
compiles the correctly named Inno Setup installer directly. No manual rename is
needed. Without Inno Setup the standalone build is available, but release
preparation is incomplete: both binaries are required for publication.

After both binaries exist, `tools/prepare_release.ps1` verifies their actual PE
product versions against the canonical version and writes `dist/SHA256SUMS.txt`
and `dist/BUILD_INFO.json`. The build invokes it automatically after Inno Setup.
Run it again after any authorized signing step changes the final bytes:

```powershell
powershell -NoProfile -File .\tools\prepare_release.ps1
# Check names and PE versions without rewriting existing release manifests:
powershell -NoProfile -File .\tools\prepare_release.ps1 -ValidateOnly
```

The metadata records each exact filename, version, byte count, SHA-256 and the
source commit. This identifies inputs; it does not certify a clean checkout or
replace the release validation report. Check `git status`, run the installation
test in an isolated account/VM (the installer writes preferences), and record
test results before publishing. Never use stale unversioned files left in `dist`
as future release assets. The scripts select only the canonical pair.

For an installer-only compile after the standalone build, resolve all defines
from the helper rather than typing names or versions:

```powershell
$release = .\.venv\Scripts\python.exe -m cropper.release_artifacts names | ConvertFrom-Json
ISCC.exe "/DAppVersion=$($release.version)" "/DStandaloneFileName=$($release.standalone)" "/DSetupBaseName=$($release.installer_base)" installer\Cropperio.iss
```

## GitHub publication (only when explicitly authorized)

Follow the established Git/`gh` workflow: verify the release commit, push the
branch, create an annotated tag, push it, and inspect any existing tag/release
before proceeding. Do not overwrite tags or existing assets. Update the README
and release notes to link to the versioned assets for that release; retain
historical links as they are. Resolve the upload paths automatically:

```powershell
$release = .\.venv\Scripts\python.exe -m cropper.release_artifacts names | ConvertFrom-Json
$tag = 'v' + $release.version
$assets = @(
    (Join-Path 'dist' $release.standalone),
    (Join-Path 'dist' $release.installer),
    'dist/SHA256SUMS.txt',
    'dist/BUILD_INFO.json'
)
# Only after validation, tag verification, and publication authorization:
gh release create $tag @assets --repo papagori/cropperio --verify-tag --latest --title "Cropperio $($release.version)" --notes-file $releaseNotesPath
```

Set `$releaseNotesPath` to the reviewed release notes before using this example.
No publication command is run by the local build/preparation scripts. Download
the public assets anonymously and compare their hashes with `SHA256SUMS.txt`;
check the public release is stable and that the branch/tag resolve to the
intended commit.

## SourceForge publication (only when explicitly authorized)

Use the same verified binary pair and manifests listed in `$assets` above.
Create the `v<version>` folder alongside existing releases. Upload without
renaming the files and preserve older folders and links. SourceForge filenames
match GitHub filenames exactly.

In the versioned setup file's information/details panel, explicitly set
**Default download for: Windows**, save it, and confirm the previous installer
is no longer the Windows default. Never make a source archive, standalone
executable, checksum or metadata file the default Windows download.

After mirror propagation, verify
https://sourceforge.net/projects/cropperio/files/latest/download on Windows:

1. Follow redirects and confirm the path ends in the current versioned setup
   filename within the intended `v<version>` folder.
2. Download to a separate file and calculate its SHA-256.
3. Compare it with the setup entry in the published `SHA256SUMS.txt` and the
   GitHub installer hash. Also verify the standalone download.
4. Record SourceForge publication only after these checks pass. If upload access
   is unavailable, provide the exact `$assets` files and these manual steps;
   report SourceForge as pending.

The dynamic URL stays unchanged; its Windows default target is a manual release
setting, not something filename generation can guarantee. SourceForge documents
the file controls at https://sourceforge.net/p/forge/documentation/Files/.
