"""Lightweight shared product identity, also safe before image-library imports."""

TAGLINE = 'Drop. Crop. Export. Voilà.'
DESCRIPTION = 'A lightweight open-source Windows utility for fast batch image cropping and resizing.'
from .i18n import LANGUAGES, tr

STARTING = {language: tr('starting', language) for language in LANGUAGES}
