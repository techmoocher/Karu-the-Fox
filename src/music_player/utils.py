TITLE_DISPLAY_LIMIT = 25
ARTIST_DISPLAY_LIMIT = 22

def _truncate(text: str, limit: int) -> str:
	if len(text) <= limit:
		return text
	if limit <= 3:
		return text[:limit]
	return text[: limit - 3] + "..."


def format_time(ms: int) -> str:
	seconds = int((ms / 1000) % 60)
	minutes = int((ms / (1000 * 60)) % 60)
	return f"{minutes:02d}:{seconds:02d}"


def format_title_display(title: str) -> str:
	return _truncate(title or "Unknown Title", TITLE_DISPLAY_LIMIT)


def format_artist_display(artist: str) -> str:
	return _truncate(artist or "Unknown Author", ARTIST_DISPLAY_LIMIT)


def format_song_label(title: str, artist: str, max_len: int = 42) -> str:
	short_title = format_title_display(title)
	short_artist = format_artist_display(artist)
	text = f"{short_title} - {short_artist}"
	if len(text) > max_len:
		return text[: max_len - 3] + "..."
	return text


__all__ = [
	"TITLE_DISPLAY_LIMIT",
	"ARTIST_DISPLAY_LIMIT",
	"format_time",
	"format_title_display",
	"format_artist_display",
	"format_song_label",
]
