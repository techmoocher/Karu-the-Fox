from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtGui import QPixmap

SpriteMap = Dict[str, QPixmap | List[QPixmap]]


def _safe_pixmap(path: Path) -> Optional[QPixmap]:
	if not path.exists():
		return None
	return QPixmap(str(path))


def load_tomato_sprites(image_dir: Path) -> SpriteMap:
	"""Load tomato sprites if they exist on disk."""

	sprite_map = {
		"neutral": "tomato-neutral.png",
		"ticking": ["tomato-ticking-1.png", "tomato-ticking-2.png"],
		"vibrate": "tomato-vibrate.png",
	}

	sprites: SpriteMap = {}
	for key, filename in sprite_map.items():
		if isinstance(filename, list):
			frames: List[QPixmap] = []
			for fname in filename:
				pix = _safe_pixmap(image_dir / "pomodoro" / fname)
				if pix:
					frames.append(pix)
			if frames:
				sprites[key] = frames
		else:
			pix = _safe_pixmap(image_dir / "pomodoro" / filename)
			if pix:
				sprites[key] = pix

	legacy_tick = image_dir / "pomodoro" / "tomato-ticking.png"
	if legacy_tick.exists() and "ticking" not in sprites:
		pix = _safe_pixmap(legacy_tick)
		if pix:
			sprites["ticking"] = [pix, pix]

	return sprites


def load_fox_icons(image_dir: Path) -> SpriteMap:
	"""Load fox hourglass icons if available."""

	icon_map = {
		"empty": "fox-hourglass-empty.png",
		"half_top": "fox-hourglass-half-top.png",
		"half_bottom": "fox-hourglass-half-bottom.png",
	}

	icons: SpriteMap = {}
	for key, filename in icon_map.items():
		pix = _safe_pixmap(image_dir / "pomodoro" / filename)
		if pix:
			icons[key] = pix

	return icons
