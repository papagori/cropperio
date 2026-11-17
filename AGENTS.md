# Cropperio project rules

## Release artifacts (permanent)

- Starting with **v2.4.2**, every published Windows executable must have a
  versioned distribution filename: `Cropperio_v2_4_2.exe` (standalone) and
  `Cropperio_Setup_v2_4_2.exe` (installer). Use underscores between version parts.
- `cropper/version.py` is the sole version source. Resolve filenames through
  `cropper.release_artifacts`; never type a release version into build scripts,
  rename published binaries, or restore unversioned future distribution names.
- Keep the installed filename `Cropperio.exe`, product name, application ID,
  installation paths and preference paths independent of release versions.
- Use `build.ps1`, `tools/prepare_release.ps1` and `tools/test_installer.ps1`.
  GitHub and SourceForge must receive the same verified binaries and checksum
  manifest. Follow the permanent release procedure in `RELEASING.md`.
- Preserve published v2.4.1 and older assets, URLs and tags. The naming helper
  retains legacy names for those versions. Do not rebuild or republish them for
  this infrastructure change. Do not bump the application version just to test names.
- Explicitly set the versioned setup executable as SourceForge's Windows default;
  verify `files/latest/download` selects that version and its SHA-256 matches.
  Never assume SourceForge selected the installer automatically.
- Run the full automated suite and naming regressions. The project currently
  accepts stable `major.minor.patch` versions only; any future prerelease support
  must preserve its identifier in artifacts and define valid Windows metadata.
