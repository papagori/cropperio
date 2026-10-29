"""Supported raster inputs and shared primary-image loading for preview/batch."""
from pathlib import Path
from struct import error as StructError

from PIL import Image, ImageOps
from pillow_heif import register_heif_opener


# libheif supplies HEVC decoding directly; no Windows codec is used. AVIF keeps
# Pillow's native decoder. Do not load HEIF thumbnails, depth or auxiliary data.
register_heif_opener(thumbnails=False, depth_images=False, aux_images=False)

EXTENSIONS = frozenset({
    '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.webp', '.bmp',
    '.heic', '.heif', '.avif', '.gif', '.ico',
})
INPUT_GLOB = ' '.join('*' + extension for extension in sorted(EXTENSIONS))
PILLOW_FORMATS = ('JPEG', 'PNG', 'TIFF', 'WEBP', 'BMP', 'HEIF', 'AVIF', 'GIF', 'ICO')
METADATA_ERRORS = (OSError, ValueError, TypeError, SyntaxError, OverflowError, StructError)


def load_primary_image(path):
    """Return detached, oriented pixels from one supported raster image.

    The HEIF plugin opens its primary image by default (which need not be index
    zero). Other Pillow decoders open frame/page zero. Never iterate a sequence.
    """
    path = Path(path)
    if path.suffix.lower() not in EXTENSIONS:
        raise ValueError(f'Unsupported input extension: {path.suffix}')
    with Image.open(path, formats=PILLOW_FORMATS) as source:
        source.load()
        try:
            return ImageOps.exif_transpose(source)
        except METADATA_ERRORS:
            # A malformed EXIF block must not reject otherwise valid pixels.
            image = source.copy()
            image.info.pop('exif', None)
            image.info.pop('Raw profile type exif', None)
            return image
