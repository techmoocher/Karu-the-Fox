def format_time(ms: int) -> str:
	seconds = int((ms / 1000) % 60)
	minutes = int((ms / (1000 * 60)) % 60)
	return f"{minutes}:{seconds:02d}"


def format_song_label(title: str, artist: str, max_len: int = 42) -> str:
	text = f"{title} - {artist}"
	if len(text) > max_len:
		return text[: max_len - 3] + "..."
	return text


__all__ = ["format_time", "format_song_label"]
