# Sync Editing plugin for CudaText
# by Vladislav Utkin <vlad@teamfnd.ru>
# MIT License
# 2018
import re
import os
from cudatext import *

fn_config = os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_sync_editing.ini')

# Uniq value for all marker plugins
MARKER_CODE = 1002 

# Check if you need case-sensitive search
CASE_SENSITIVE = True
# Regex for finding words
FIND_REGEX = r'[a-zA-Z0-9_]+'
# Code for markers
# BG color for markers
MARKER_BG_COLOR = 0xFFAAAA
# Border color for markers
MARKER_BORDER_COLOR = 0xFF0000
# BG color for selected text
MARKER_BG_COLOR_SELECTED = 0xFFDDDD


def bool_to_str(v):
    return '1' if v else '0'

def str_to_bool(s):
    return s=='1'
    

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
    
    def __init__(self):
    
        global CASE_SENSITIVE
        CASE_SENSITIVE = str_to_bool(ini_read(fn_config, 'op', 'case_sens', '1'))
    
    
    def toggle(self):
        original = ed.get_text_sel()
        # Check if we have selection of text
        if original == '':
            msg_status('Sync Editing: You need to select text that you want to modify')
            return
        # Save cords
        self.start, self.end = ed.get_sel_lines()
        self.selected = True
        # Break text selection
        ed.set_sel_rect(0,0,0,0)
        # Mark text that was selected
        for y in range(self.start, self.end+1):
            ed.attr(MARKERS_ADD, MARKER_CODE, 0, y, len(ed.get_text_line(y)), color_bg=MARKER_BG_COLOR_SELECTED)
        msg_status('Sync Editing: Now, click at the start of the word that you want to modify')
        
    
    def reset(self):
        self.start = None
        self.end = None
        self.selected = False
        ed.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        msg_status('Sync Editing: Selection reset')
        
    
    def on_click(self, ed_self, state):
        if self.selected:
            ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
            # Save comments to check if this line is comment
            comments = ''
            lexer = ed.get_prop(PROP_LEXER_FILE)
            if lexer:
                prop = lexer_proc(LEXER_GET_PROP, lexer)
                if prop:
                    comments = prop['c_line']
            # Set word to search
            caret = ed_self.get_carets()[0]
            word = re.match(FIND_REGEX, ed_self.get_text_line(caret[1])[caret[0]:])
            if not word:
                msg_status('Sync Editing: No word! Try again, reset or check regular expression in settings')
                return
            word = str(word.group(0))
            # Find word
            for y in range(self.start, self.end+1):
                current_string = ed_self.get_text_line(y)
                # Check if this line is empty
                if len(current_string.split()) == 0:
                    continue
                # Check if this line is comment
                if not comments == '' and current_string.split()[0] == comments:
                    continue
                # Delete all strings
                current_string = delete_strings(current_string)
                # Check if CASE_SENSITIVE need
                if not CASE_SENSITIVE:
                    current_string = lower(current_string)
                indexes = [m.start() for m in re.finditer(word, current_string)]
                for index in indexes:
                    # Check if this not a part of other word
                    if index - 1 >= 0 \
                       and not re.match(FIND_REGEX, current_string[index - 1]) \
                       and index + len(word) < len(current_string) \
                       and not re.match(FIND_REGEX, current_string[index + len(word)]):
                        ed_self.attr(MARKERS_ADD, MARKER_CODE, index, y, len(word), color_bg=MARKER_BG_COLOR, color_border=MARKER_BORDER_COLOR, border_down=1)
                        ed_self.set_caret(index, y, id=CARET_ADD)
                    # Check if it is on start of line
                    elif index - 1 < 0 \
                       and index + len(word) < len(current_string) \
                       and not re.match(FIND_REGEX, current_string[index + len(word)]):
                        ed_self.attr(MARKERS_ADD, MARKER_CODE, index, y, len(word), color_bg=MARKER_BG_COLOR, color_border=MARKER_BORDER_COLOR, border_down=1)
                        ed_self.set_caret(index, y, id=CARET_ADD)
            # Reset selection
            self.selected = False
            self.editing = True
            # Save 'green' position of first caret
            first_caret = ed_self.get_carets()[0]
            self.start = first_caret[1]
            self.end = first_caret[3]
        elif self.editing:
            self.editing = False
            self.reset()
            first_caret = ed_self.get_carets()[0]
            ed_self.set_caret(first_caret[0], first_caret[1], first_caret[2], first_caret[3])
            
    
    def on_caret(self, ed_self):
        if self.editing:
            # If we leaved original line, we have to break selection
            first_caret = ed_self.get_carets()[0]
            if first_caret[1] < self.start or first_caret[3] > self.end:
                self.editing = False
                self.reset()
                ed_self.set_caret(first_caret[0], first_caret[1], first_caret[2], first_caret[3])
                
    
    def config(self):
    
        ini_write(fn_config, 'op', 'case_sens', bool_to_str(CASE_SENSITIVE))
        file_open(fn_config)
