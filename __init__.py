# Disclaimer: this is WIP plugin, so it not supposed to work (by now)
# Current TODO: Select variables from brackets

from cudatext import *
import re


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
    CASE_SENSITIVE = True
    BREAK_CHARS = ['(', ')', ':', "'", '"', '=', '{', '}', '[', ']']
    
    
    def Toggle(self):
        original = ed.get_text_sel()
        # Check if we have selection of text
        if original == '':
            return
        start, end = ed.get_sel_lines()
        text = original
        # Delete all comments
        to_delete = set()
        try:
            comments = lexer_proc(LEXER_GET_PROP, ed.get_prop(PROP_LEXER_FILE))['c_line']
        except TypeError as e:
            print('Current lexer is undefined ({})'.format(str(e)))
            comments = ''
        for i in range(len(text)):
            # Check comments
            if text[i:i-1+len(comments)] == comments:
                y = i
                while text[y] != '\n':
                    y += 1
                to_delete.add(text[i:y])
        # Delete them
        for substr in to_delete:
            text = text.replace(substr, '')
        # Delete all strings
        text = delete_strings(text)
        # Check if we need case-sensitive search
        if not self.CASE_SENSITIVE:
            text = lower(text)
        # Split string on substrings which are supposed to be variables
        substrs = set(text.split())
        for char in self.BREAK_CHARS:
            to_add = set()
            prev_to_add = set()
            to_delete = set()
            for substr in substrs:
                to_add |= set(substr.split(char))
                if prev_to_add != to_add:
                    to_delete.add(substr)
                prev_to_add = to_add
            substrs -= to_delete
            substrs |= to_add
        # Find and delete all substrings that are not looks like statements
        to_delete = set()
        for substr in substrs:
            if len(substr) <= 1:
                to_delete.add(substr)
                continue
            for char in self.BREAK_CHARS:
                if char in substr:
                    to_delete.add(substr)
        substrs -= to_delete
        # Hightlight all found statements
        for i in range(start, end+1):
            cur_line = ed.get_text_line(i)
            # Check that current line is not comment
            if len(cur_line.split()) > 0 and cur_line.split()[0][:len(comments)] == comments:
                continue
            # Delete strings from line
            cur_line = delete_strings(cur_line)
            for substr in substrs:
                indexes = [m.start() for m in re.finditer(substr, cur_line)]
                for index in indexes:
                    if index - 1 > 0 and cur_line[index-1] == ' ':
                        ed.markers(MARKERS_ADD, index, i)
                        
    
    def Reset(self):
        ed.markers(MARKERS_DELETE_ALL)
