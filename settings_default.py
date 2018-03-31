# Default setting for Sync Editing plugin
import sys
from cudatext import *

# Check if you need case-sensitive search
CASE_SENSITIVE = True
# Regex for finding words
FIND_REGEX = r'[a-zA-Z0-9_-]+'
# Code for markers
MARKER_CODE = 1002
# BG color for markers
MARKER_BG_COLOR = 0xFFAAAA
# Border color for markers
MARKER_BORDER_COLOR = 0xFF0000
# BG color for selected text
MARKER_BG_COLOR_SELECTED = 0xFFDDDD

# Load user settings from cuda_sync_editing.py
sys.path.append(app_path(APP_DIR_SETTINGS))
try:
    from cuda_sync_editing import *
except ImportError:
    pass
