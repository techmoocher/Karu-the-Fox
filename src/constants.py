from pathlib import Path


SOURCE_DIR = Path(__file__).resolve().parent 

BASE_DIR = SOURCE_DIR.parent

ASSETS_DIR = BASE_DIR / "assets"
IMAGE_DIR = ASSETS_DIR / "images"
MUSIC_DIR = ASSETS_DIR / "music"
CONFIG_FILE = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"
LOGO_ICON = IMAGE_DIR / "logo.png"