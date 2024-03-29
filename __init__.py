# Sync Editing plugin for CudaText
# by Vladislav Utkin <vlad@teamfnd.ru>
# MIT License
# 2018
import re
import os
from . import randomcolor
from cudatext import *
from cudatext_keys import *
from cudax_lib import html_color_to_int, get_opt, set_opt, CONFIG_LEV_USER, CONFIG_LEV_LEX

from cudax_lib import get_translation
_ = get_translation(__file__)  # I18N

# Uniq value for all marker plugins
MARKER_CODE = app_proc(PROC_GET_UNIQUE_TAG, '') 

CASE_SENSITIVE = True
FIND_REGEX_DEFAULT = r'\w+'
FIND_REGEX = FIND_REGEX_DEFAULT

STYLES_DEFAULT = r'(?i)id[\w\s]*'
STYLES_NO_DEFAULT = '(?i).*keyword.*'
STYLES = STYLES_DEFAULT
STYLES_NO = STYLES_NO_DEFAULT

NON_STANDART_LEXERS = {
  'HTML': 'Text|Tag id correct|Tag prop',
  'PHP': 'Var',
}
  
NAIVE_LEXERS = [
  'Markdown', # it has 'Text' rule for many chars, including punctuation+spaces
  'reStructuredText',
  'Textile',
]

MARKER_BG_COLOR = 0xFFAAAA
MARKER_F_COLOR  = 0x005555
MARKER_BORDER_COLOR = 0xFF0000
MARK_COLORS = True
ASK_TO_EXIT = True

theme = app_proc(PROC_THEME_SYNTAX_DICT_GET, '')

def theme_color(name, is_font):
    if name in theme:
        return theme[name]['color_font' if is_font else 'color_back']
    return 0x808080

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
    saved_sel = None
    pattern = None
    pattern_styles = None
    pattern_styles_no = None
    naive_mode = False
    
    
    def __init__(self):
        global MARKER_F_COLOR
        global MARKER_BG_COLOR
        global MARKER_BORDER_COLOR
        global MARK_COLORS
        global ASK_TO_EXIT
        MARKER_F_COLOR = theme_color('Id', True)
        MARKER_BG_COLOR = theme_color('SectionBG4', False)
        MARKER_BORDER_COLOR = MARKER_F_COLOR
        ASK_TO_EXIT = get_opt('syncedit_ask_to_exit', True, lev=CONFIG_LEV_USER)
        MARK_COLORS = get_opt('syncedit_mark_words', True, lev=CONFIG_LEV_USER)
    
    
    def token_style_ok(self, s):
        good = self.pattern_styles.fullmatch(s)
        bad = self.pattern_styles_no.fullmatch(s)
        return good and not bad
         

    def toggle(self):
        global FIND_REGEX
        global CASE_SENSITIVE
        global STYLES_DEFAULT
        global STYLES_NO_DEFAULT
        global STYLES
        global STYLES_NO
        carets = ed.get_carets()
        if len(carets)!=1:
            msg_status(_('Sync Editing: Need single caret'))
            return
        caret = carets[0]

        def restore_caret():
            ed.set_caret(caret[0], caret[1])

        original = ed.get_text_sel()
        # Check if we have selection of text
        if not original and self.saved_sel is None:
            msg_status(_('Sync Editing: Make selection first'))
            return
        self.set_progress(3)
        if self.saved_sel is not None:
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
        self.set_progress(5)
        ed.set_prop(PROP_MARKED_RANGE, (self.start_l, self.end_l))
        ed.set_prop(PROP_TAG, 'sync_edit:1')
        # Go naive way if lexer id none or other text file
        cur_lexer = ed.get_prop(PROP_LEXER_FILE)
        if cur_lexer in NON_STANDART_LEXERS:
            # If it if non-standart lexer, change it's behaviour
            STYLES_DEFAULT = NON_STANDART_LEXERS[cur_lexer]
        elif cur_lexer == '':
            # If lexer is none, go very naive way
            self.naive_mode = True
        if cur_lexer in NAIVE_LEXERS or get_opt('syncedit_naive_mode', False, lev=CONFIG_LEV_LEX):
            self.naive_mode = True
        # Load lexer config
        CASE_SENSITIVE = get_opt('case_sens', True, lev=CONFIG_LEV_LEX)
        FIND_REGEX = get_opt('id_regex', FIND_REGEX_DEFAULT, lev=CONFIG_LEV_LEX)
        STYLES = get_opt('id_styles', STYLES_DEFAULT, lev=CONFIG_LEV_LEX)
        STYLES_NO = get_opt('id_styles_no', STYLES_NO_DEFAULT, lev=CONFIG_LEV_LEX)
        # Compile regex
        self.pattern = re.compile(FIND_REGEX)
        self.pattern_styles = re.compile(STYLES)
        self.pattern_styles_no = re.compile(STYLES_NO)
        # Run lexer scan form start
        self.set_progress(10)
        ed.action(EDACTION_LEXER_SCAN, self.start_l) #API 1.0.289
        self.set_progress(40)
        # Find all occurences of regex
        tokenlist = ed.get_token(TOKEN_LIST_SUB, self.start_l, self.end_l)
        #print(tokenlist)
        if not tokenlist and not self.naive_mode:
            self.reset()
            self.saved_sel = None
            msg_status(_('Sync Editing: Cannot find IDs in selection'))
            self.set_progress(-1)
            restore_caret()
            return
        elif self.naive_mode:
            # Naive filling
            for y in range(self.start_l, self.end_l+1):
                cur_line = ed.get_text_line(y)
                for match in self.pattern.finditer(cur_line):
                    token = ((match.start(), y), (match.end(), y), match.group(), 'id')
                    if match.group() in self.dictionary:
                        self.dictionary[match.group()].append(token)
                    else:
                        self.dictionary[match.group()] = [(token)]
        else:
            for token in tokenlist:
                if not self.token_style_ok(token['style']):
                    continue
                idd = token['str'].strip()
                if not CASE_SENSITIVE:
                    idd = idd.lower()
                old_style_token = ((token['x1'], token['y1']), (token['x2'], token['y2']), token['str'], token['style'])
                if idd in self.dictionary:
                    if old_style_token not in self.dictionary[idd]:
                        self.dictionary[idd].append(old_style_token)
                else:
                    self.dictionary[idd] = [(old_style_token)]
        # Fix tokens
        self.set_progress(60)
        self.fix_tokens()
        # Exit if no id's (eg: comments and etc)
        if len(self.dictionary) == 0:
            self.reset()
            self.saved_sel = None
            msg_status(_('Sync Editing: Cannot find IDs in selection'))
            self.set_progress(-1)
            restore_caret()
            return
        # Exit if 1 occurence found (issue #44)
        elif len(self.dictionary) == 1 and len(self.dictionary[list(self.dictionary.keys())[0]]) == 1:
            self.reset()
            self.saved_sel = None
            msg_status(_('Sync Editing: Need several IDs in selection'))
            self.set_progress(-1)
            restore_caret()
            return
        self.set_progress(90)
        # Mark all words that we can modify with pretty light color
        if MARK_COLORS:
            rand_color = randomcolor.RandomColor()
            for key in self.dictionary:
                color  = html_color_to_int(rand_color.generate(luminosity='light')[0])
                for key_tuple in self.dictionary[key]:
                    ed.attr(MARKERS_ADD,
                        tag = MARKER_CODE,
                        x = key_tuple[0][0],
                        y = key_tuple[0][1],
                        len = key_tuple[1][0] - key_tuple[0][0],
                        color_font = 0xb000000,
                        color_bg = color,
                        color_border = 0xb000000, 
                        border_down = 1
                        )
        self.set_progress(-1)
        if self.want_exit:
            msg_status(_('Sync Editing: Cancel? Click somewhere else to cancel, or on ID to continue.'))
        else:
            msg_status(_('Sync Editing: Click on ID to edit it, or somewhere else to cancel'))
        # restore caret but w/o selection
        restore_caret()
        
        
    # Fix tokens with spaces at the start of the line (eg: ((0, 50), (16, 50), '        original', 'Id')) and remove if it has 1 occurence (issue #44 and #45)
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
        todelete = []
        for neww in new_replace:
            for key in self.dictionary:
                for i in range(len(self.dictionary[key])):
                    if self.dictionary[key][i] == neww[1]:
                        self.dictionary[key][i] = neww[0]
                if len(self.dictionary[key]) < 2:
                    todelete.append(key)
        for dell in todelete:
            self.dictionary.pop(dell, None)
    
    
    # Set progress (issue #46)
    def set_progress(self, prg):
        app_proc(PROC_PROGRESSBAR, prg)
        app_idle()
    
    
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
        self.pattern = None
        self.pattern_styles = None
        self.pattern_styles_no = None
        self.naive_mode = False
        self.saved_sel = None
        # Restore original position
        if self.original:
            ed.set_caret(self.original[0], self.original[1], id=CARET_SET_ONE)
            self.original = None
        ed.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        ed.set_prop(PROP_MARKED_RANGE, (-1, -1))
        self.set_progress(-1)
        ed.set_prop(PROP_TAG, 'sync_edit:0')
        msg_status(_('Sync Editing: Cancelled'))


    def doclick(self):
        # state = app_proc(PROC_GET_KEYSTATE, '')
        state = ''
        return self.on_click(ed, state)


    def on_click(self, ed_self, state):
        global CASE_SENSITIVE
        global FIND_REGEX
        global ASK_TO_EXIT
        if ed_self.get_prop(PROP_TAG, 'sync_edit:0') != '1':
            return
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
                    msg_status(_('Sync Editing: Not a word! Click another, or click somewhere else again'))
                    self.want_exit = True
                    return
                else:
                    if not ASK_TO_EXIT:
                        self.reset()
                        self.saved_sel = None
                        return
                    if msg_box(_('Do you want to cancel Sync Editing mode?'), MB_YESNO+MB_ICONQUESTION) == ID_YES:
                        self.reset()
                        self.saved_sel = None
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
                color_font=MARKER_F_COLOR, \
                color_bg=MARKER_BG_COLOR, \
                color_border=MARKER_BORDER_COLOR, \
                border_left=1, \
                border_right=1, \
                border_down=1, \
                border_up=1 \
                )
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
        if ed_self.get_prop(PROP_TAG, 'sync_edit:0') != '1':
            return
        if self.editing:
            # If we leaved original line, we have to break selection
            first_caret = ed_self.get_carets()[0]
            x0, y0, x1, y1 = first_caret
            if y0 != self.start:
                self.editing = False
                self.reset()
                ed_self.set_caret(*first_caret)
                self.toggle()
            # If amount of text changed, we have to redraw it.
            self.redraw(ed_self)
     
     
    # Redraws Id's borders
    def redraw(self, ed_self):
        # Simple workaround to prevent redraw while redraw
        if not self.our_key:
            return
        # Find out what changed on the first caret (on others changes will be the same)
        old_key = self.our_key
        self.our_key = None
        first_y = ed_self.get_carets()[0][1]
        first_x = ed_self.get_carets()[0][0]
        first_y_line = ed_self.get_text_line(first_y)
        start_pos = first_x
        # Workaround for end of id case
        if not self.pattern.match(first_y_line[start_pos:]):
            start_pos -= 1
        while self.pattern.match(first_y_line[start_pos:]):
            start_pos -= 1
        start_pos += 1
        # Workaround for EOL #65
        if start_pos < 0:
            start_pos = 0
        # Workaround for empty id (eg. when it was deleted) #62
        if not self.pattern.match(first_y_line[start_pos:]):
            self.our_key = old_key
            ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
            return
        new_key = self.pattern.match(first_y_line[start_pos:]).group(0)
        if not CASE_SENSITIVE:
            new_key = new_key.lower()
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
            while self.pattern.match(y_line[x:]):
                x -= 1
            x += 1
            # Workaround for EOL #65
            if x < 0:
                x = 0
            self.dictionary[new_key].append(((x, y), (x+len(new_key), y), new_key, 'Id'))
        # End rebuilding dictionary
        self.our_key = new_key
        # Paint new borders
        ed_self.attr(MARKERS_DELETE_BY_TAG, tag=MARKER_CODE)
        for key_tuple in self.dictionary[self.our_key]:
                ed_self.attr(MARKERS_ADD, tag = MARKER_CODE, \
                x = key_tuple[0][0], y = key_tuple[0][1], \
                len = key_tuple[1][0] - key_tuple[0][0], \
                color_font=MARKER_F_COLOR, \
                color_bg=MARKER_BG_COLOR, \
                color_border=MARKER_BORDER_COLOR, \
                border_left=1, \
                border_right=1, \
                border_down=1, \
                border_up=1 \
                )
                
    
    def config(self):
        if msg_box(_('Open plugin\'s readme.txt to read about configuring?'), 
                MB_OKCANCEL+MB_ICONQUESTION) == ID_OK:
            fn = os.path.join(os.path.dirname(__file__), 'readme', 'readme.txt')
            if os.path.isfile(fn):
                file_open(fn)
            else:
                msg_status(_('Cannot find file: ')+fn)
