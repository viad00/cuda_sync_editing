# Sync Editing plugin for CudaText
# by Vladislav Utkin <vlad@teamfnd.ru>
# MIT License
# 2018
import re
from . import randomcolor
from cudatext import *
from cudatext_keys import *
from cudax_lib import html_color_to_int, get_opt, set_opt, CONFIG_LEV_USER, CONFIG_LEV_LEX

# Uniq value for all marker plugins
MARKER_CODE = 1002 

# Check if you need case-sensitive search
CASE_SENSITIVE = True
# Regex for finding words
FIND_REGEX_DEFAULT = r'\w+'
FIND_REGEX = FIND_REGEX_DEFAULT
# Code for markers
# BG color for markers
MARKER_BG_COLOR = 0xFFAAAA
# Border color for markers
MARKER_BORDER_COLOR = 0xFF0000
# Mark selections with colors
MARK_COLORS = True
# Ask to confirm exit
NO_ASK_TO_EXIT = False


class Command:
    start = None
    end = None
    selected = False 
    editing = False
    dictionary = {}
    our_key = None
    original = None
    start_l = None
    end_l = None
    want_exit = False
    saved_sel = (0,0)
    
    
    def __init__(self):
        global MARKER_BORDER_COLOR
        global MARKER_BG_COLOR
        global MARK_COLORS
        global NO_ASK_TO_EXIT
        if get_opt('syncedit_color_marker_back'):
            MARKER_BG_COLOR = html_color_to_int(get_opt('syncedit_color_marker_back', lev=CONFIG_LEV_USER))
        if get_opt('syncedit_color_marker_border'):
            MARKER_BORDER_COLOR = html_color_to_int(get_opt('syncedit_color_marker_border', lev=CONFIG_LEV_USER))
        NO_ASK_TO_EXIT = get_opt('syncedit_no_ask_to_exit', False, lev=CONFIG_LEV_USER)
        MARK_COLORS = get_opt('syncedit_color_mark_words', True, lev=CONFIG_LEV_USER)
    
    
    def toggle(self):
        global FIND_REGEX
        global CASE_SENSITIVE
        original = ed.get_text_sel()
        # Check if we have selection of text
        if not original and self.saved_sel == (0,0):
            msg_status('Sync Editing: Make selection first')
            return
        if self.saved_sel != (0,0):
            self.start_l, self.end_l = self.saved_sel
            self.selected = True
        else:
            # Save cords
            self.start_l, self.end_l = ed.get_sel_lines()
            self.selected = True
            # Save text selection
            self.saved_sel = ed.get_sel_lines()
            # Break text selection
            ed.set_sel_rect(0,0,0,0)
        # Mark text that was selected
        ed.set_prop(PROP_MARKED_RANGE, (self.start_l, self.end_l))
        # Load lexer config
        CASE_SENSITIVE = get_opt('case_sens', True, lev=CONFIG_LEV_LEX)
        FIND_REGEX = get_opt('id_regex', FIND_REGEX_DEFAULT, lev=CONFIG_LEV_LEX)
        # Run lexer scan
        ed.lexer_scan(0)
        # Find all occurences of regex
        for token in ed.get_token(TOKEN_LIST_SUB, self.start_l, self.end_l):
            idd = token['str'].strip()
            # Workaround for lexers that have either 'Id' and 'Identifier' in scan result
            if token['style'][:2] != 'Id':
                continue
            if len(token['style']) > 2 and token['style'][2] == ' ':
                continue
            old_style_token = ((token['x1'], token['y1']), (token['x2'], token['y2']), token['str'], token['style'])
            if idd in self.dictionary:
                if old_style_token not in self.dictionary[idd]:
                    self.dictionary[idd].append(old_style_token)
            else:
                self.dictionary[idd] = [(old_style_token)]
        # Exit if no id's (eg: comments and etc)
        if len(self.dictionary) == 0:
            self.reset()
            msg_status('Sync Editing: Cannot find IDs in selection')
            return
        # Fix tokens
        self.fix_tokens()
        # Mark all words that we can modify with pretty light color
        if MARK_COLORS:
            rand_color = randomcolor.RandomColor()
            for key in self.dictionary:
                color = html_color_to_int(rand_color.generate(luminosity='light')[0])
                for key_tuple in self.dictionary[key]:
                    ed.attr(MARKERS_ADD, tag = MARKER_CODE, \
                    x = key_tuple[0][0], y = key_tuple[0][1], \
                    len = key_tuple[1][0] - key_tuple[0][0], \
                    color_bg=color, color_border=0xb000000, border_down=1)
        if self.want_exit:
            msg_status('Sync Editing: Are want to exit? Click somewhere else to confirm exit or on marked word to continue editing.')
        else:
            msg_status('Sync Editing: Now, click on the word that you want to modify or somewhere else to exit')
        
        
    # Fix tokens with spaces at the start of the line (eg: ((0, 50), (16, 50), '        original', 'Id'))
    def fix_tokens(self):
        new_replace = []
        for key in self.dictionary:
            for key_tuple in self.dictionary[key]:
                token = key_tuple[2]
                if token[0] != ' ':
                    pass
                offset = 0
                for i in range(len(token)):
                    if token[i] != ' ':
                        offset = i
                        break
                new_token = token[offset:]
                new_start = key_tuple[0][0] + offset
                new_tuple = ((new_start, key_tuple[0][1]), key_tuple[1], new_token, key_tuple[3])
                new_replace.append([new_tuple, key_tuple])
        for neww in new_replace:
            for key in self.dictionary:
                for i in range(len(self.dictionary[key])):
                    if self.dictionary[key][i] == neww[1]:
                        self.dictionary[key][i] = neww[0]
    
    
    def reset(self):
        self.start = None
        self.end = None
        self.selected = False
        self.editing = False
        self.dictionary = {}
        self.our_key = None
        self.offset = None
        self.start_l = None
        self.end_l = None
        self.want_exit = False
        # Restore original position
        if self.original:
            ed.set_caret(self.original[0], self.original[1], id=CARET_SET_ONE)
            self.original = None
        ed.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        ed.set_prop(PROP_MARKED_RANGE, (-1, -1))
        msg_status('Sync Editing: exited')
        
    
    def on_click(self, ed_self, state):
        global CASE_SENSITIVE
        global FIND_REGEX
        global NO_ASK_TO_EXIT
        if self.selected:
            # Find where we are
            self.our_key = None
            caret = ed_self.get_carets()[0]
            for key in self.dictionary:
                for key_tuple in self.dictionary[key]:
                    if  caret[1] >= key_tuple[0][1] \
                    and caret[1] <= key_tuple[1][1] \
                    and caret[0] <= key_tuple[1][0] \
                    and caret[0] >= key_tuple[0][0]:
                        self.our_key = key
                        self.offset = caret[0] - key_tuple[0][0]
            # Reset if None
            if not self.our_key:
                if not self.want_exit:
                    msg_status('Sync Editing: Not a word! Select another or click somewhere else again')
                    self.want_exit = True
                    return
                else:
                    if NO_ASK_TO_EXIT:
                        self.reset()
                        self.saved_sel = (0,0)
                        return
                    if msg_box('Are you want to leave Sync Edit mode?', MB_YESNO+MB_ICONINFO) == ID_YES:
                        self.reset()
                        self.saved_sel = (0,0)
                        return
                    else:
                        self.want_exit = False
                        return
            ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
            # Save original position
            self.original = (caret[0], caret[1])
            # Select editable word
            for key_tuple in self.dictionary[self.our_key]:
                ed_self.attr(MARKERS_ADD, tag = MARKER_CODE, \
                x = key_tuple[0][0], y = key_tuple[0][1], \
                len = key_tuple[1][0] - key_tuple[0][0], \
                color_bg=MARKER_BG_COLOR, color_border=MARKER_BORDER_COLOR, \
                border_left=1, border_right=1, border_down=1, border_up=1)
                ed_self.set_caret(key_tuple[0][0] + self.offset, key_tuple[0][1], id=CARET_ADD)
            # Reset selection
            self.selected = False
            self.editing = True
            # Save 'green' position of first caret
            first_caret = ed_self.get_carets()[0]
            self.start = first_caret[1]
            self.end = first_caret[3]
            # support reverse selection
            if self.start > self.end and not self.end == -1: # If not selected, cudatext returns -1
                self.start, self.end = self.end, self.start
        elif self.editing:
            self.editing = False
            first_caret = ed_self.get_carets()[0]
            self.reset()
            ed_self.set_caret(*first_caret)
            self.toggle()
            
    
    def on_caret(self, ed_self):
        if self.editing:
            # If we leaved original line, we have to break selection
            first_caret = ed_self.get_carets()[0]
            x0, y0, x1, y1 = first_caret
            if y0 > self.start or y1 > self.end or y0 < self.start:
                self.editing = False
                self.reset()
                ed_self.set_caret(*first_caret)
                self.toggle()
            # If amount of text changed, we have to redraw it.
            self.redraw(ed_self)
     
     
    # Redraws Id's borders
    def redraw(self, ed_self):
        # Simple workaround to prevent redraw while redraw
        if not self.our_key: # Do not forget to set it back
            return
        # Find out what changed on the first caret (on others changes will be the same)
        old_key = self.our_key
        self.our_key = None
        first_y = ed_self.get_carets()[0][1]
        first_x = ed_self.get_carets()[0][0]
        first_y_line = ed_self.get_text_line(first_y)
        start_pos = first_x
        # Compile regex
        pattern = re.compile(FIND_REGEX)
        # Workaround for end of id case
        if not pattern.match(first_y_line[start_pos:]):
            start_pos -= 1
        while pattern.match(first_y_line[start_pos:]):
            start_pos -= 1
        start_pos += 1
        new_key = pattern.match(first_y_line[start_pos:]).group(0)
        # Rebuild dictionary with new values
        old_key_dictionary = self.dictionary[old_key]
        self.dictionary = {}
        self.dictionary[new_key] = []
        pointers = []
        for i in old_key_dictionary:
            pointers.append(i[0])
        for pointer in pointers:
            x = pointer[0]
            y = pointer[1]
            y_line = ed_self.get_text_line(y)
            while pattern.match(y_line[x:]):
                x -= 1
            x += 1
            self.dictionary[new_key].append(((x, y), (x+len(new_key), y), new_key, 'Id'))
        # End rebuilding dictionary
        self.our_key = new_key
        # Paint new borders
        ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        for key_tuple in self.dictionary[self.our_key]:
                ed_self.attr(MARKERS_ADD, tag = MARKER_CODE, \
                x = key_tuple[0][0], y = key_tuple[0][1], \
                len = key_tuple[1][0] - key_tuple[0][0], \
                color_bg=MARKER_BG_COLOR, color_border=MARKER_BORDER_COLOR, \
                border_left=1, border_right=1, border_down=1, border_up=1)
                
    
    def config(self):
        msg_box(
'''To configure Sync Editing, open lexer-specific config in CudaText (Options / Settings-more / Settings lexer specific) and write there options: case sensitive, regular expression for identifiers:

  "case_sens": true, // case sensitive search
  "id_regex": "\w+", // regex to find id's

Also you can write to CudaText's user.json these options:

  "syncedit_color_marker_back": "#rrggbb", // background color for id's
  "syncedit_color_marker_border": "#rrggbb", // border color for id's
  "syncedit_color_mark_words": true, // if false plugin does not marking all id's in selection mode
  "syncedit_no_ask_to_exit": false // if true plugin exits editing mode without confirmation
''', MB_OK+MB_ICONINFO)
