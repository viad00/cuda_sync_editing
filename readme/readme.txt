Plugin for CudaText.
Synchronized-editing feature to edit identical identifiers, inspired by SynWrite editor.

Usage:

 - Select block (one or several lines), containing some ID's (identifiers)
 - Activate plugin by menu item: "Plugins / Sync Editing / Activate"
 - Selection is removed but plugin colorizes that block in different color
 - Click on any ID in that block, which you want to edit
 - Edit it (type new text)
 - To cancel Sync Editing: click somewhere else; or leave ID's line (e.g. with arrow keys); or call menu item "Plugins / Sync Editing / Cancel"

To detect IDs, plugin gets lexer fragments with style beginning with "Id",
but excludes fragments with style "Id keyword". This is customizable.

Plugin ignores IDs, which are located in syntax "comments" and "strings"
(this depends on lexer settings).


Options
-------

Plugin has several options, which are listed/described in the help message-box.
Call menu item "Options / Settings-plugins / Sync Editing / Config".
There are options "case sensitive", "reg.ex. for identifiers" and few UI options.


Lexers HTML and Markdown
------------------------

By default, plugin don't support lexer HTML and Markdown, but this can be customized.
1) HTML.
Open HTML-specific config file: activate HTML lexer, call "Options / Settings - lexer specific".
File "settings/lexer HTML.json" will be opened. Write there:

  "id_styles": "Tag id correct",

Now plugin must detect tag-names as IDs, and must allow to rename them.
To detect also tag properties as IDs, write:

  "id_styles": "Tag id correct|Tag prop",
  
To detect words inside quotes values, you will need this option (it overrides "id_styles"):

  "syncedit_naive_mode": true,

2) Markdown.
By default, plugin cannot detect separate words in Markdown.
Open Markdown-specific config, file "settings/lexer Markdown.json". Write there:

  "syncedit_naive_mode": true,


About
-----

Author: Vladislav Utkin (viad00 at GitHub)
  with minor help of Alexey Torgashin
License: MIT
