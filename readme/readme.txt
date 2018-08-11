Plugin for CudaText
Sync Editing feature to edit identical identifiers, inspired by SynWrite editor.

Usage:
 - Select block (one or several lines), containing some ID's (identifiers)
 - Activate plugin by menu item: "Plugins / Sync Editing / Activate"
 - Selection is removed but plugin colorizes that block in different color
 - Click on any ID in that block, which you want to edit
 - Edit it (type new text)
 - To cancel Sync Editing: click somewhere else; or leave ID's line (e.g. with arrow keys); or call menu item "Plugins / Sync Editing / Cancel"

Plugin has several options, which are listed/described in the help message-box. 
Call menu item "Options / Settings-plugins / Sync Editing / Config".
Options "case sensitive", "reg.ex. for identifiers" and few UI options.

Plugin ignores IDs, which are located in syntax constants/comments.
To detect constants and comments, plugin uses lexer API, it wants words
with lexer style, beginning with "Id", but not containing "keyword".

Author: Vladislav Utkin (viad00 at GitHub)
License: MIT
