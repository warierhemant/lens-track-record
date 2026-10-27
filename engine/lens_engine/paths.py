"""Filesystem layout. Everything is relative to the project root."""
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ENGINE_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
UPWORTHY_DIR = DATA_DIR / "upworthy"
SEALED_DIR = DATA_DIR / "sealed"
SPLITS_DIR = DATA_DIR / "splits"
PROCESSED_DIR = DATA_DIR / "processed"

HOLDOUT_IDS_FILE = SEALED_DIR / "holdout_ids.txt"
HOLDOUT_HASH_FILE = SEALED_DIR / "HOLDOUT_SHA256.txt"

PACKAGE_FILES = {
    "exploratory": "upworthy-archive-exploratory-packages-03.12.2020.csv",
    "holdout": "upworthy-archive-holdout-packages-03.12.2020.csv",
    "confirmatory": "upworthy-archive-confirmatory-packages-03.12.2020.csv",
}
