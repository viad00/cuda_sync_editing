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

Plugin also ignores words, which are located in string constants, and in comments.
To detect string constants and comments, plugin uses lexer API, it wants words
with lexer styles "Id", "Id1"... but not "Id nnnnn".

Author: Vladislav Utkin (viad00 at GitHub)
License: MIT
