"""Generate small original raster fixtures; no personal/third-party images."""
from pathlib import Path

from PIL import Image, ImageCms

from cropper import input_formats  # Registers the HEIF writer for fixture creation.


ROOT = Path(__file__).resolve().parent.parent / 'tests' / 'fixtures' / 'input_formats'


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    image = Image.new('RGB', (96, 64), (220, 30, 40))
    image.paste((30, 70, 220), (48, 0, 96, 32))
    for filename, fmt in (
        ('sample.jpg', 'JPEG'), ('sample.jpeg', 'JPEG'), ('sample.png', 'PNG'),
        ('sample.tif', 'TIFF'), ('sample.tiff', 'TIFF'),
        ('sample.webp', 'WEBP'), ('sample.bmp', 'BMP'),
    ):
        image.save(ROOT / filename, format=fmt)

    exif = Image.Exif()
    exif[274], exif[315] = 6, 'Cropperio synthetic fixture'
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
    image.save(ROOT / 'oriented.heic', format='HEIF', quality=-1, chroma=444,
               exif=exif, icc_profile=profile)

    primary = Image.new('RGBA', (80, 120), (20, 180, 70, 128))
    primary.paste((20, 180, 70, 0), (0, 0, 20, 20))
    image.save(ROOT / 'primary-second.heif', format='HEIF', save_all=True,
               append_images=[primary], primary_index=1, quality=-1, chroma=444)

    image.save(ROOT / 'sequence.avif', format='AVIF', save_all=True,
               append_images=[Image.new('RGB', (96, 64), (20, 210, 30))],
               quality=100, subsampling='4:4:4', duration=100)
    primary.save(ROOT / 'alpha.avif', format='AVIF', quality=100, subsampling='4:4:4')

    first = Image.new('P', (96, 64), 0)
    first.putpalette([0, 0, 0, 220, 30, 40, 20, 210, 30] + [0] * (768 - 9))
    first.paste(1, (20, 20, 76, 44))
    second = Image.new('P', (96, 64), 2)
    second.putpalette(first.getpalette())
    first.save(ROOT / 'animated.gif', save_all=True, append_images=[second],
               transparency=0, disposal=2, duration=100, loop=0, optimize=False)
    image.save(ROOT / 'pages.tiff', save_all=True,
               append_images=[Image.new('RGB', (64, 96), (20, 210, 30))])
    primary.resize((64, 64)).save(ROOT / 'sample.ico', sizes=[(16, 16), (32, 32), (64, 64)])
    print(f'Generated fixtures in {ROOT}')


if __name__ == '__main__':
    main()
