# Sync Editing plugin for CudaText
# by Vladislav Utkin <vlad@teamfnd.ru>
# MIT License
# 2018
import re
import os
import json
from cudatext import *
from cudatext_keys import *
from cudax_lib import html_color_to_int

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'user.json')

# Uniq value for all marker plugins
MARKER_CODE = 1002 

# Check if you need case-sensitive search
CASE_SENSITIVE = True
# Regex for finding words
FIND_REGEX_DEFAULT = r'[a-zA-Z_]\w*'
FIND_REGEX = FIND_REGEX_DEFAULT
# Code for markers
# BG color for markers
MARKER_BG_COLOR = 0xFFAAAA
# Border color for markers
MARKER_BORDER_COLOR = 0xFF0000
    

def delete_strings(text):
    to_delete = set()
    for i in range(len(text)):
        # Check strings
        if text[i] == '"':
            y = i + 1
            # Check end of string
            if len(text) <= y:
                y -= 1
            while text[y] != '"':
                y += 1
                # Check that it is not an escaped char and out of range
                try:
                    if text[y] == '\\':
                       y += 1
                except IndexError:
                    break
            to_delete.add(text[i:y])        
        # Check other strings
        if text[i] == "'":
            y = i + 1
            # Check end of string
            if len(text) <= y:
                y -= 1
            while text[y] != "'":
                y += 1
                # Check that it is not an escaped char and out of range
                try:
                    if text[y] == '\\':
                       y += 1
                except IndexError:
                    break
            to_delete.add(text[i:y])
    for substr in to_delete:
        text = text.replace(substr, '')
    return text


class Command:
    start = None
    end = None
    selected = False 
    editing = False
    dictionary = {}
    
    
    def __init__(self):
        global MARKER_BORDER_COLOR
        global MARKER_BG_COLOR
        parsed_config = json.load(open(fn_config))
        if 'syncedit_color_marker_back' in parsed_config:
            MARKER_BG_COLOR = html_color_to_int(parsed_config['syncedit_color_marker_back'])
        if 'syncedit_color_marker_border' in parsed_config:
            MARKER_BORDER_COLOR = html_color_to_int(parsed_config['syncedit_color_marker_border'])
    
    
    def toggle(self):
        original = ed.get_text_sel()
        # Check if we have selection of text
        if not original:
            msg_status('Sync Editing: Make selection first')
            return
        # Save cords
        self.start, self.end = ed.get_sel_lines()
        self.selected = True
        # Break text selection
        ed.set_sel_rect(0,0,0,0)
        # Mark text that was selected
        ed.set_prop(PROP_MARKED_RANGE, (self.start, self.end))
        # Find all occurences of regex
        for y in range(self.start, self.end+1):
            line = ed.get_text_line(y)
            for x in range(len(line)):
                token = ed.get_token(TOKEN_AT_POS, x, y)
                idd = token[2]
                x += len(token[2])
                idd = idd.strip()
                if token[3] != 'Id':
                    continue
                if idd in self.dictionary:
                    if token not in self.dictionary[idd]:
                        self.dictionary[idd].append((token))
                else:
                    self.dictionary[idd] = [(token)]
        print(self.dictionary)
        msg_status('Sync Editing: Now, on the word that you want to modify')
        
    
    def reset(self):
        self.start = None
        self.end = None
        self.selected = False
        ed.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        ed.set_prop(PROP_MARKED_RANGE, (-1, -1))
        msg_status('Sync Editing: Selection reset')
        
    
    def on_click(self, ed_self, state):
        global CASE_SENSITIVE
        global FIND_REGEX
        if self.selected:
            ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
            # Find where we are
            our_key = None
            caret = ed_self.get_carets()[0]
            for key in self.dictionary:
                for key_tuple in self.dictionary[key]:
                    print(caret, key_tuple)
                    if  caret[1] >= key_tuple[0][1] \
                    and caret[1] <= key_tuple[1][1] \
                    and caret[0] <= key_tuple[1][0] \
                    and caret[0] >= key_tuple[0][0]:
                        our_key = key
            # TODO: Scan all occurences
            
            # Reset selection
            #self.selected = False
            #self.editing = True
            # Save 'green' position of first caret
            first_caret = ed_self.get_carets()[0]
            self.start = first_caret[1]
            self.end = first_caret[3]
            # support reverse selection
            if self.start > self.end:
                self.start, self.end = self.end, self.start
                
        elif self.editing:
            self.editing = False
            self.reset()
            first_caret = ed_self.get_carets()[0]
            ed_self.set_caret(*first_caret)
            
    
    def on_caret(self, ed_self):
        if self.editing:
            # If we leaved original line, we have to break selection
            first_caret = ed_self.get_carets()[0]
            if first_caret[1] < self.start or first_caret[3] > self.end:
                self.editing = False
                self.reset()
                ed_self.set_caret(*first_caret)
                 
    
    def config(self):
        msg_box(
'''To configure Sync Editing, open lexer-specific config in CudaText (Options / Settings-more / Settings lexer specific) and write there options: case sensitive, regular expression for identifiers:

  "case_sens": true,
  "id_regex": "[a-zA-Z_]\\\\w*",

Also you can write to CudaText's user.json these options:

  "syncedit_color_marker_back": "#rrggbb",
  "syncedit_color_marker_border": "#rrggbb",
''', MB_OK+MB_ICONINFO)
