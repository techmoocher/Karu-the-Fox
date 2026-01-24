from pathlib import Path
from random import shuffle
from typing import Any, Dict, List, Optional

from mutagen._file import File as MutagenFile
from mutagen._util import MutagenError
from mutagen.id3 import ID3
from mutagen.id3._util import ID3NoHeaderError

from .constants import NO_ART_IMAGE_PATH

SongData = Dict[str, Any]


def _find_thumbnail(song_dir: Path) -> Path | None:
	for ext in (".jpg", ".png", ".jfif", ".jpeg"):
		candidate = song_dir / f"thumbnail{ext}"
		if candidate.exists():
			return candidate
	return None


def _first_tag_value(tags: Any, key: str) -> Optional[str]:
	if not tags:
		return None
	values = tags.get(key)
	if not values:
		return None
	if isinstance(values, (list, tuple)):
		return str(values[0]) if values else None
	return str(values)


def _read_metadata(mp3_path: Path) -> tuple[Optional[str], Optional[str], Optional[bytes]]:
	title: Optional[str] = None
	artist: Optional[str] = None
	art_bytes: Optional[bytes] = None

	try:
		audio = MutagenFile(mp3_path, easy=True)
		if audio and audio.tags:
			title = _first_tag_value(audio.tags, "title")
			artist = _first_tag_value(audio.tags, "artist")
	except MutagenError:
		pass

	try:
		id3 = ID3(mp3_path)
		apic_frames = id3.getall("APIC")
		if apic_frames:
			art_bytes = apic_frames[0].data
	except (ID3NoHeaderError, MutagenError, FileNotFoundError):
		pass

	return title, artist, art_bytes


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
		title, artist, art_bytes = _read_metadata(mp3_path)
		thumbnail_path = _find_thumbnail(song_dir) or NO_ART_IMAGE_PATH
		songs.append(
			{
				"title": title or "Unknown Title",
				"artist": artist or "Unknown Author",
				"path": mp3_path,
				"thumbnail_path": thumbnail_path,
				"thumbnail_data": art_bytes,
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
