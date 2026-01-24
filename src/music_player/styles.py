MUSIC_PLAYER_STYLESHEET = r"""
	* {
		font-family: "Press Start 2P", "VT323", "Courier New", monospace;
		letter-spacing: 0.5px;
		font-size: 13px;
	}

	#CentralFrame {
		background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
			stop:0 #CFE8FF, stop:1 #B6DCFF);
		color: #1F2A44;
		border: 4px solid #1F3D66;
		border-radius: 10px;
	}

	#TitleBar {
		background: #9CD5FF;
		border-top-left-radius: 7px;
		border-top-right-radius: 7px;
		border-bottom: 3px solid #1F3D66;
	}

	#WindowButton {
		background: #7CB8F0;
		border: 3px solid #1F3D66;
		border-radius: 4px;
		color: #0F1B2D;
		font-size: 12px;
		padding: 2px 6px;
	}
	#WindowButton:hover { background: #B6E2FF; }
	#WindowButton:pressed {
		background: #6AA7DD;
		margin-top: 2px;
	}

	#TitleLabel {
		font-size: 20px;
		font-weight: bold;
		color: #0F1B2D;
	}
	#ArtistLabel {
		font-size: 14px;
		color: #294368;
	}
	#Thumbnail {
		border: 3px solid #1F3D66;
		border-radius: 6px;
		background: #E5F3FF;
	}

	#ControlButton, #PlaylistButton, #PlayPauseButton {
		background: #9CD5FF;
		border: 3px solid #1F3D66;
		border-radius: 6px;
		color: #0F1B2D;
		padding: 6px 10px;
		font-size: 13px;
		line-height: 1.2em;
	}
	#ControlButton:hover, #PlaylistButton:hover, #PlayPauseButton:hover { background: #BFE6FF; }
	#ControlButton:pressed, #PlaylistButton:pressed, #PlayPauseButton:pressed {
		background: #7CB8F0;
		margin-top: 2px;
	}
	#PlayPauseButton {
		min-width: 56px;
		min-height: 56px;
		border-radius: 8px;
		background: #8BC7FF;
		font-size: 13px;
	}
	#PlaylistButton { font-size: 13px; padding: 8px 14px; font-weight: bold; }

	QSlider::groove:horizontal {
		border: 3px solid #1F3D66;
		height: 10px;
		background: #E5F3FF;
		margin: 4px 0;
	}
	QSlider::sub-page:horizontal {
		background: #7CB8F0;
		border: 3px solid #1F3D66;
	}
	QSlider::add-page:horizontal {
		background: #CFE8FF;
		border: 3px solid #1F3D66;
	}
	QSlider::handle:horizontal {
		background: #1F3D66;
		border: 2px solid #0F1B2D;
		width: 16px;
		height: 16px;
		margin: -6px 0;
		border-radius: 2px;
	}

	QListWidget {
		background: #E5F3FF;
		border: 3px solid #1F3D66;
		font-size: 12px;
		padding: 6px;
		color: #0F1B2D;
	}
	QListWidget::item { padding: 10px 6px; }
	QListWidget::item:selected {
		background: #7CB8F0;
		color: #0F1B2D;
		border: 2px solid #1F3D66;
	}

	#TimeLabel {
		color: #000000;
		font-weight: bold;
		font-size: 13px;
	}

	QToolTip {
		background: #0F1B2D;
		color: #CFE8FF;
		border: 2px solid #7CB8F0;
		padding: 6px;
		font-size: 10px;
	}
"""

HELP_HTML = """
<h2>Keybind</h2>
<ul>
  <li><b>Up / K</b>: Move selection up</li>
  <li><b>Down / J</b>: Move selection down</li>
  <li><b>Enter</b>: Play selected (switches to Normal)</li>
  <li><b>P</b>: Play/Pause</li>
  <li><b>M</b>: Change Mode</li>
</ul>
<h2>Modes</h2>
<ul>
	<li><b>Normal</b>: Alphabetical order, repeats the playlist upon end</li>
	<li><b>Loop</b>: Repeats the current song</li>
	<li><b>Shuffle</b>: Plays all tracks in random order</li>
</ul>
"""

__all__ = ["MUSIC_PLAYER_STYLESHEET", "HELP_HTML"]
