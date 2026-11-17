"""Canonical distribution names and checksums; independent of the GUI/toolchain."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from .version import __version__


def artifact_names(version=None):
    version = __version__ if version is None else version
    match = re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', version)
    if not match:
        # The project currently supports stable x.y.z versions only.
        raise ValueError('Expected a stable major.minor.patch version')
    numbers = tuple(map(int, match.groups()))
    if any(number > 65535 for number in numbers):
        raise ValueError('Windows version components must be at most 65535')
    suffix = '_v' + version.replace('.', '_') if numbers >= (2, 4, 2) else ''
    return {
        'version': version,
        'standalone': 'Cropperio' + suffix + '.exe',
        'installer': 'Cropperio_Setup' + suffix + '.exe',
        'standalone_base': 'Cropperio' + suffix,
        'installer_base': 'Cropperio_Setup' + suffix,
        'installed': 'Cropperio.exe',
        'windows_version': list(numbers + (0,)),
    }


def release_manifest(directory, product_versions, version=None, commit=None):
    """Reject missing/wrong-version binaries before generating publication inputs."""
    names = artifact_names(version)
    artifacts = []
    for kind in ('standalone', 'installer'):
        name = names[kind]
        if product_versions.get(name, '').strip() != names['version']:
            raise ValueError('Product version mismatch: ' + name)
        path = Path(directory) / name
        artifacts.append({'file': name, 'bytes': path.stat().st_size,
                          'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                          'product_version': names['version']})
    return {'version': names['version'], 'commit': commit, 'artifacts': artifacts}


def write_manifest(directory, manifest):
    directory = Path(directory)
    checksums = ''.join(f"{item['sha256']}  {item['file']}\n"
                        for item in manifest['artifacts'])
    (directory / 'SHA256SUMS.txt').write_text(checksums, encoding='ascii')
    (directory / 'BUILD_INFO.json').write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('names', 'manifest'))
    parser.add_argument('--directory', type=Path, default=Path('dist'))
    parser.add_argument('--commit')
    args = parser.parse_args()
    if args.command == 'names':
        print(json.dumps(artifact_names()))
    else:
        manifest = release_manifest(args.directory, json.load(sys.stdin),
                                    commit=args.commit)
        write_manifest(args.directory, manifest)
        print(json.dumps(manifest))


if __name__ == '__main__':
    main()
