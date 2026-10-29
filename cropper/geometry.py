"""Crop geometry and direct output sizing, independent of Pillow and Qt."""
from dataclasses import dataclass, replace
import math

from .settings import ASPECT_RATIOS, ProcessingOptions, custom_output


def crop_box(width, height, ratio=(4, 3)):
    """Return the largest centered integer-pixel box near the requested ratio.

    One source dimension is retained in full and the other is rounded to the
    nearest pixel. Thus 6000 × 4000 becomes 5333 × 4000 at 4:3.
    """
    if width < 1 or height < 1:
        raise ValueError('Image dimensions must be positive.')
    if ratio is None:
        return 0, 0, width, height
    a, b = ratio
    if a < 1 or b < 1:
        raise ValueError('Aspect ratio must be positive.')
    if height > width:
        a, b = b, a
    if width * b > height * a:
        crop_width = min(width, max(1, round(height * a / b)))
        crop_height = height
    else:
        crop_width = width
        crop_height = min(height, max(1, round(width * b / a)))
    left = (width - crop_width) // 2
    top = (height - crop_height) // 2
    return left, top, left + crop_width, top + crop_height


def output_size(cropped_size, options: ProcessingOptions, *, portrait=False):
    width, height = cropped_size
    preset = options.output
    if preset.key == 'custom':
        custom_output(preset.reference_dimension, preset.value)
        a, b = options.effective_ratio or cropped_size
        if options.effective_ratio and portrait:
            a, b = b, a
        if preset.reference_dimension == 'width':
            target = preset.value, max(1, round(preset.value * b / a))
        else:
            target = max(1, round(preset.value * a / b)), preset.value
    elif preset.dimensions:
        target = preset.dimensions[::-1] if portrait else preset.dimensions
    elif preset.long_edge:
        edge = preset.long_edge
        if width >= height:
            target = edge, max(1, round(height * edge / width))
        else:
            target = max(1, round(width * edge / height)), edge
    else:
        return cropped_size, False
    blocked = not options.allow_upscaling and (target[0] > width or target[1] > height)
    return (cropped_size if blocked else target), blocked


@dataclass(frozen=True)
class ManualCrop:
    """Relative geometry in the EXIF-oriented source; absent means automatic.

    Scale is relative to the largest crop of the current ratio. This permits
    predictable ratio changes without reusing incompatible absolute boxes.
    """
    center_x: float = 0.5
    center_y: float = 0.5
    scale: float = 1.0
    ratio_override: str | None = None  # None inherits batch; 'Original' means source ratio.
    framing: bool = True  # False allows a ratio-only override with automatic framing.


def image_options(source_size, options, manual=None):
    """Resolve a source's ratio and logical output size from the batch snapshot.

    Numeric presets retain their long edge; the other dimension follows the
    effective ratio, oriented using the source. Custom retains its chosen axis.
    With no ratio override, every historical output calculation is unchanged.
    """
    if manual is None or manual.ratio_override is None:
        return options
    ratio = ASPECT_RATIOS[manual.ratio_override]
    preset = options.output
    if ratio != options.effective_ratio and (preset.dimensions or preset.long_edge):
        edge = max(preset.dimensions) if preset.dimensions else preset.long_edge
        a, b = ratio or tuple(sorted(source_size, reverse=True))
        preset = replace(preset, dimensions=(edge, max(1, round(edge * b / a))), long_edge=None)
    return replace(options, aspect_ratio=ratio, output=preset)


def crop_size(box):
    return box[2] - box[0], box[3] - box[1]


def _scaled_size(source_size, options, scale):
    maximum = crop_size(crop_box(*source_size, options.effective_ratio))
    if scale >= 1:
        return maximum  # Preserve the historical maximum's rounding exactly.
    a, b = options.effective_ratio or source_size
    if options.effective_ratio and source_size[1] > source_size[0]:
        a, b = b, a
    # Always derive both dimensions from the locked ratio, never from a
    # previously rounded crop. Integer pixels require nearest-pixel rounding.
    width = min(maximum[0], max(1, round(maximum[0] * scale)))
    height = min(maximum[1], max(1, round(width * b / a)))
    return width, height


def minimum_scale(source_size, options):
    maximum = crop_size(crop_box(*source_size, options.effective_ratio))
    # Even with upscaling/Maximum, retain at least 16 source pixels on the
    # short edge (or all pixels when the input itself is smaller).
    required = (min(16, maximum[0]), min(16, maximum[1]))
    if not options.allow_upscaling:
        target, _ = output_size(maximum, replace(options, allow_upscaling=True),
                                portrait=source_size[1] > source_size[0])
        if options.output.key not in ('maximum', 'original'):
            required = tuple(max(a, b) for a, b in zip(required, target))
    if any(a > b for a, b in zip(required, maximum)):
        return 1.0  # Source already too small: retain existing no-upscale policy.
    low, high = 0.0, 1.0
    for _ in range(48):
        middle = (low + high) / 2
        if all(a >= b for a, b in zip(_scaled_size(source_size, options, middle), required)):
            high = middle
        else:
            low = middle
    return high


def resolve_crop(source_size, options, manual=None):
    """The sole integer source box used by painting and final export."""
    options = image_options(source_size, options, manual)
    if manual is None or not manual.framing:
        return crop_box(*source_size, options.effective_ratio)
    scale = min(1.0, max(minimum_scale(source_size, options), manual.scale))
    width, height = _scaled_size(source_size, options, scale)
    left = min(source_size[0] - width, max(0, round(manual.center_x * source_size[0] - width / 2)))
    top = min(source_size[1] - height, max(0, round(manual.center_y * source_size[1] - height / 2)))
    return left, top, left + width, top + height


def crop_adjustment(source_size, options, box):
    maximum = crop_size(crop_box(*source_size, options.effective_ratio))
    return ManualCrop((box[0] + box[2]) / (2 * source_size[0]),
                      (box[1] + box[3]) / (2 * source_size[1]),
                      (box[2] - box[0]) / maximum[0])


def move_crop(source_size, options, box, dx, dy):
    state = crop_adjustment(source_size, options, box)
    return resolve_crop(source_size, options, replace(
        state, center_x=state.center_x + dx / source_size[0],
        center_y=state.center_y + dy / source_size[1]))


def zoom_crop(source_size, options, manual, steps):
    options = image_options(source_size, options, manual)
    state = manual or crop_adjustment(source_size, options, resolve_crop(source_size, options))
    state = replace(state, framing=True)
    # Fractional wheel steps are preserved even before they move a source pixel.
    scale = state.scale * math.exp(-0.04 * max(-100, min(100, steps)))
    candidate = replace(state, scale=min(1.0, max(minimum_scale(source_size, options), scale)))
    width, height = crop_size(resolve_crop(source_size, options, candidate))
    half_x, half_y = width / (2 * source_size[0]), height / (2 * source_size[1])
    # Clamp the continuous center, not the rounded box's center. Repeated
    # fractional deltas must not accumulate half-pixel rounding drift.
    return replace(candidate,
                   center_x=min(1 - half_x, max(half_x, candidate.center_x)),
                   center_y=min(1 - half_y, max(half_y, candidate.center_y)))
