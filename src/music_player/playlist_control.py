from pathlib import Path
from random import shuffle
from typing import Any, Dict, List

SongData = Dict[str, Any]


def _parse_filename(mp3_path: Path) -> tuple[str, str]:
	stem = mp3_path.stem
	if "_" in stem:
		title_part, artist_part = stem.split("_", 1)
		return title_part.replace("-", " "), artist_part.replace("-", " ")
	return stem.replace("-", " "), "Unknown Artist"


def _find_thumbnail(song_dir: Path) -> Path | None:
	for ext in (".jpg", ".png", ".jfif", ".jpeg"):
		candidate = song_dir / f"thumbnail{ext}"
		if candidate.exists():
			return candidate
	return None


def scan_music_directory(music_dir: Path) -> List[SongData]:
	songs: List[SongData] = []
	if not music_dir.exists():
		return songs

	for song_dir in music_dir.iterdir():
		if not song_dir.is_dir():
			continue
		mp3_files = list(song_dir.glob("*.mp3"))
		if not mp3_files:
			continue

		mp3_path = mp3_files[0]
		title, artist = _parse_filename(mp3_path)
		songs.append(
			{
				"title": title or "Unknown Title",
				"artist": artist or "Unknown Artist",
				"path": mp3_path,
				"thumbnail": _find_thumbnail(song_dir),
			}
		)

	songs.sort(key=lambda song: (song["title"].casefold(), song["artist"].casefold()))
	return songs


def build_shuffle_queue(length: int, current_index: int) -> List[int]:
	queue = list(range(length))
	if current_index in queue:
		queue.remove(current_index)
	shuffle(queue)
	return queue


def ensure_shuffle_queue(queue: List[int], length: int, current_index: int) -> None:
	if length == 0:
		queue.clear()
		return
	if not queue:
		queue.extend(build_shuffle_queue(length, current_index))


def remove_from_shuffle_queue(queue: List[int], index: int) -> None:
	if index in queue:
		queue.remove(index)


__all__ = [
	"SongData",
	"scan_music_directory",
	"build_shuffle_queue",
	"ensure_shuffle_queue",
	"remove_from_shuffle_queue",
]
