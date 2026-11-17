"""Release naming, packaging and checksum regressions without rebuilding binaries."""
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from cropper import release_artifacts
from cropper.release_artifacts import artifact_names, release_manifest, write_manifest
from cropper.version import __version__


ROOT = Path(__file__).resolve().parent.parent


class ReleaseArtifactTests(unittest.TestCase):
    def test_legacy_releases_keep_their_names(self):
        for version in ('2.3.0', '2.4.0', '2.4.1'):
            names = artifact_names(version)
            self.assertEqual(names['standalone'], 'Cropperio.exe')
            self.assertEqual(names['installer'], 'Cropperio_Setup.exe')

    def test_every_future_release_uses_its_own_version(self):
        for version in ('2.4.2', '2.4.3', '2.5.0', '3.0.0', '12.34.56'):
            names = artifact_names(version)
            suffix = '_v' + version.replace('.', '_')
            self.assertEqual(names['standalone'], 'Cropperio' + suffix + '.exe')
            self.assertEqual(names['installer'], 'Cropperio_Setup' + suffix + '.exe')
            self.assertEqual(names['windows_version'], list(map(int, version.split('.'))) + [0])
            self.assertEqual(names['installed'], 'Cropperio.exe')

    def test_default_tracks_canonical_version(self):
        self.assertEqual(artifact_names(), artifact_names(__version__))
        with patch.object(release_artifacts, '__version__', '3.0.0'):
            self.assertEqual(artifact_names()['installer'], 'Cropperio_Setup_v3_0_0.exe')

    def test_invalid_and_unsupported_versions_fail_closed(self):
        # Existing metadata/tests allow stable x.y.z only; no prerelease support is removed.
        for version in ('v2.4.2', '2.4', '2.04.2', '../2.4.2', '2.4.2-rc.1', '65536.0.0'):
            with self.subTest(version=version), self.assertRaises(ValueError):
                artifact_names(version)

    def test_pyinstaller_output_and_embedded_version_follow_metadata(self):
        for version in ('2.4.1', '2.4.2', '3.0.0'):
            calls = []
            fake_analysis = SimpleNamespace(pure=[], scripts=[], binaries=[], datas=[])
            with patch('cropper.version.__version__', version), patch.object(release_artifacts, '__version__', version):
                result = runpy.run_path(str(ROOT / 'Cropperio.spec'), init_globals={
                    'Analysis': lambda *a, **kw: fake_analysis,
                    'PYZ': lambda *a: None,
                    'EXE': lambda *a, **kw: calls.append(kw),
                })
            names = artifact_names(version)
            self.assertEqual(calls[0]['name'] + '.exe', names['standalone'])
            self.assertEqual(result['version_numbers'], tuple(names['windows_version']))
            resource = calls[0]['version'].__str__()
            self.assertIn(version, resource)
            self.assertIn(names['standalone'], resource)

    def test_manifests_reference_only_expected_binaries_and_actual_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for version in ('2.4.2', '2.5.0', '3.0.0'):
                names = artifact_names(version)
                versions = {}
                for kind in ('standalone', 'installer'):
                    name = names[kind]
                    (directory / name).write_bytes((name + version).encode())
                    versions[name] = version + '   '
                manifest = release_manifest(directory, versions, version, commit='test-commit')
                write_manifest(directory, manifest)
                sums = (directory / 'SHA256SUMS.txt').read_text()
                saved = json.loads((directory / 'BUILD_INFO.json').read_text())
                self.assertEqual(saved, manifest)
                self.assertEqual(len(sums.splitlines()), 2)
                for item in saved['artifacts']:
                    payload = (directory / item['file']).read_bytes()
                    self.assertIn(hashlib.sha256(payload).hexdigest() + '  ' + item['file'], sums)
                    self.assertEqual(item['bytes'], len(payload))
                    self.assertEqual(item['product_version'], version)
                self.assertNotIn('  Cropperio.exe', sums)
                self.assertNotIn('  Cropperio_Setup.exe', sums)

    def test_missing_or_mismatched_binaries_prevent_manifest(self):
        names = artifact_names('2.4.2')
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                release_manifest(tmp, {names['standalone']: '2.4.1'}, '2.4.2')
            versions = {names[k]: '2.4.2' for k in ('standalone', 'installer')}
            with self.assertRaises(FileNotFoundError):
                release_manifest(tmp, versions, '2.4.2')

    def test_cli_resolves_names_without_writing_artifacts(self):
        result = subprocess.run([sys.executable, '-m', 'cropper.release_artifacts', 'names'],
                                cwd=ROOT, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(result.stdout), artifact_names())

    def test_cli_manifest_uses_changed_canonical_version_in_isolated_checkout(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            package = directory / 'cropper'
            package.mkdir()
            (package / '__init__.py').write_text('')
            (package / 'version.py').write_text("__version__ = '2.4.2'\n")
            shutil.copyfile(ROOT / 'cropper/release_artifacts.py', package / 'release_artifacts.py')
            versions = {}
            for name in ('Cropperio_v2_4_2.exe', 'Cropperio_Setup_v2_4_2.exe'):
                (directory / name).write_bytes(b'synthetic artifact for manifest testing')
                versions[name] = '2.4.2'
            result = subprocess.run([sys.executable, '-m', 'cropper.release_artifacts',
                                     'manifest', '--directory', tmp, '--commit', 'test-commit'],
                                    input=json.dumps(versions), cwd=directory,
                                    capture_output=True, text=True, check=True)
            manifest = json.loads(result.stdout)
            self.assertEqual(manifest['version'], '2.4.2')
            self.assertEqual({item['file'] for item in manifest['artifacts']}, set(versions))
            self.assertEqual(manifest['commit'], 'test-commit')
            self.assertIn('Cropperio_Setup_v2_4_2.exe', (directory / 'SHA256SUMS.txt').read_text())

    @unittest.skipUnless(os.name == 'nt', 'Actual Windows PE version validation')
    def test_release_preparation_rejects_wrong_pe_version_without_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = artifact_names()
            # These are deliberately Python binaries, never executed by the script.
            for kind in ('standalone', 'installer'):
                shutil.copyfile(sys.executable, Path(tmp) / names[kind])
            result = subprocess.run(['powershell', '-NoProfile', '-File',
                                     str(ROOT / 'tools/prepare_release.ps1'),
                                     '-DistDirectory', tmp], cwd=ROOT,
                                    capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b'Product version mismatch', result.stderr)
            self.assertFalse((Path(tmp) / 'SHA256SUMS.txt').exists())
            self.assertFalse((Path(tmp) / 'BUILD_INFO.json').exists())

    def test_active_packaging_has_no_legacy_distribution_paths(self):
        for path in (ROOT / 'build.ps1', ROOT / 'tools/test_installer.ps1',
                     ROOT / 'tools/prepare_release.ps1'):
            text = path.read_text(encoding='utf-8')
            self.assertNotRegex(text, r'dist[\\/]+Cropperio(?:_Setup)?\.exe')
            self.assertNotIn('Cropperio_Setup.exe', text)
            self.assertIn('cropper.release_artifacts', text)
        installer = (ROOT / 'installer/Cropperio.iss').read_text(encoding='utf-8-sig')
        self.assertIn('OutputBaseFilename={#SetupBaseName}', installer)
        self.assertIn('DestName: "{#AppExeName}"', installer)
        build = (ROOT / 'build.ps1').read_text()
        self.assertIn('/DStandaloneFileName=$($release.standalone)', build)
        self.assertIn('/DSetupBaseName=$($release.installer_base)', build)
        self.assertIn('prepare_release.ps1', build)


if __name__ == '__main__':
    unittest.main()
