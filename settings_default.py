# Default setting for Sync Editing plugin

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


# Load user settings from <plugin-directory>/settings_user.py
try:
    from .settings_user import *
except ImportError:
    pass
