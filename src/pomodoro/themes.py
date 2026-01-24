from __future__ import annotations

from textwrap import dedent
from typing import Dict


THEMES: Dict[str, Dict[str, str]] = {
	"Pastel Blue": {
		"bg": "#D8E9FF",
		"panel": "#BED9FF",
		"accent": "#5B8DEF",
		"text": "#112542",
	},
	"Pastel Pink": {
		"bg": "#FFE4EF",
		"panel": "#FFD1E4",
		"accent": "#FF7AA2",
		"text": "#3F0D21",
	},
	"Pastel Orange": {
		"bg": "#FFF0DC",
		"panel": "#FFE2C4",
		"accent": "#FF9B42",
		"text": "#3D1F0F",
	},
	"Pastel Red": {
		"bg": "#FFE1E1",
		"panel": "#FFCACA",
		"accent": "#FF6B6B",
		"text": "#3D0F0F",
	},
}

DEFAULT_THEME = "Pastel Orange"


def resolve_theme(name: str) -> Dict[str, str]:
	"""Return a valid theme configuration, falling back to the default."""

	return THEMES.get(name, THEMES[DEFAULT_THEME])


def build_stylesheet(colors: Dict[str, str]) -> str:
	"""Generate the application stylesheet for the provided theme colors."""

	return dedent(
		f"""
		#Frame {{
			background-color: {colors['bg']};
			border: 3px solid {colors['accent']};
			border-radius: 10px;
			color: {colors['text']};
			font-family: 'Press Start 2P', 'VT323', 'Courier New', monospace;
		}}
		#Title {{
			color: {colors['accent']};
			font-size: 16px;
			letter-spacing: 2px;
			font-weight: bold;
		}}
		#Caption {{
			color: {colors['text']};
			font-size: 12px;
		}}
		#TimeLabel {{
			background-color: {colors['panel']};
			border: 3px solid {colors['accent']};
			border-radius: 8px;
			padding: 16px 12px;
			font-size: 28px;
			letter-spacing: 1px;
			color: #000000;
		}}
		QSlider::groove:horizontal {{
			border: 2px solid {colors['accent']};
			height: 12px;
			background: {colors['panel']};
			margin: 4px 6px;
		}}
		QSlider::handle:horizontal {{
			background: {colors['accent']};
			border: 2px solid {colors['text']};
			width: 18px;
			height: 18px;
			margin: -7px 0;
		}}
		QSlider::sub-page:horizontal {{
			background: {colors['accent']};
		}}
		QPushButton {{
			background-color: {colors['accent']};
			color: {colors['bg']};
			border: 3px solid {colors['text']};
			border-radius: 8px;
			padding: 10px 14px;
			font-weight: bold;
		}}
		QPushButton:hover {{
			background-color: {colors['text']};
			color: {colors['bg']};
		}}
		QPushButton:pressed {{
			background-color: {colors['panel']};
			color: {colors['text']};
		}}
		QPushButton#ResetButton {{
			background-color: {colors['panel']};
			color: {colors['text']};
		}}
		QPushButton#TitleButton {{
			background-color: transparent;
			color: {colors['text']};
			border: 2px solid {colors['accent']};
			border-radius: 6px;
			font-weight: bold;
			padding: 2px 6px;
			min-width: 0px;
		}}
		QPushButton#TitleButton:hover {{
			background-color: {colors['accent']};
			color: {colors['bg']};
		}}
		QPushButton#TitleButton:pressed {{
			background-color: {colors['text']};
			color: {colors['bg']};
		}}
		QComboBox {{
			background-color: {colors['panel']};
			color: {colors['text']};
			border: 2px solid {colors['accent']};
			border-radius: 6px;
			padding: 6px 8px;
		}}
		QComboBox QAbstractItemView {{
			selection-background-color: {colors['accent']};
			selection-color: {colors['bg']};
		}}
		"""
	)
