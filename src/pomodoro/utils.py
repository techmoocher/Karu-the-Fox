from __future__ import annotations

MIN_MINUTES = 10
MAX_MINUTES = 60


def clamp_duration_minutes(minutes: int | float | None) -> int:
	"""Clamp the duration to the allowed slider range."""

	try:
		value = int(minutes or 0)
	except (TypeError, ValueError):
		value = 0
	return max(MIN_MINUTES, min(MAX_MINUTES, value))


def seconds_to_clock(seconds: int) -> str:
	seconds = max(0, int(seconds))
	mins, secs = divmod(seconds, 60)
	return f"{mins:02d}:{secs:02d}"


def can_reset_timer(is_running: bool, remaining_seconds: int, total_seconds: int) -> bool:
	"""Determine if reset should be enabled."""

	return (not is_running) and (
		remaining_seconds < total_seconds or remaining_seconds == 0
	)
