#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import termios, sys

class ConsoleTK:

    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    palette = [ ('red', False),
                ('red', True),
                ('yellow', False),
                ('yellow', True),
                ('green', False),
                ('green', True)]

    csi = '\x1b['
    reset = '\x1b[0m'
 
    def __init__(self, height = 10):
        self.fg = None
        self.bg = None
        self.bold = False
        self.blink = False

        self.height = height
        self.initzone(self.height)

        self.cur_x = 0
        self.cur_y = 0

    @property
    def is_tty(self):
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def initzone(self, height = 10):
        sys.stdout.write("\n" * height)
        sys.stdout.write(self.csi + "?25l") # hide the cursor
        sys.stdout.write(self.csi + "%sF"%height)
        self.cur_x = 0
        self.cur_y = 0
        self.clear()

        # add margin
        self.relmoveto(1,1)
        self.cur_x = 0
        self.cur_y = 0
 

    def clear(self):
        self.moveto(0,0)
        sys.stdout.write(self.csi + "J")

    def gethotcolor(self, percent, reverse = False):
        percent = (100 - percent) if reverse else percent
        idx = min(int(len(self.palette) * percent / 100.), len(self.palette)-1)
        return self.palette[idx]

    def colorize(self, message, fg = None, bg = None, bold = None, blink = None):

        # arguments overrides instance defaults
        fg = fg or self.fg
        bg = bg or self.bg
        bold = self.bold if bold is None else bold
        blink = self.blink if blink is None else blink

        params = []
        if bg in self.color_map:
            params.append(str(self.color_map[bg] + 40))
        if fg in self.color_map:
            params.append(str(self.color_map[fg] + 30))
        if bold:
            params.append('1')
        elif blink:
            params.append('5')
        if params:
            message = ''.join((self.csi, ';'.join(params),
                                'm', message, self.reset))
        
        return message

    def writeat(self, message, x, y, fg = None, bg = None, bold = None, blink = None):
        self.moveto(x, y)
        self.savepos()
        sys.stdout.write(self.colorize(message, fg, bg, bold, blink))
        self.restorepos()

    def write(self, message, fg = None, bg = None, bold = None, blink = None):
        self.savepos()
        sys.stdout.write(self.colorize(message, fg, bg, bold, blink))
        self.restorepos()

    def bar(self, 
            percent, maxlength = 30, 
            msg = "", showvalue = True, label = None, 
            color = None,
            autocolor = None, highishot = False):
        """
        With auto-color, the color depends on the percentage value.
        If 'highishot' is True, the higher the percentage, the closer to red,
        else, the higher the percentage, the closer to green.
        """
        msg = msg if msg else "{0}%".format(percent)

        self.savepos()
        sys.stdout.write(("%s |"%label if label else "|") + \
                          self.csi +"%sC"%(maxlength-2) + "|"+ \
                         ((" " + msg) if showvalue else ""))
        self.restorepos()

        bold = False
        if not color and autocolor:
            color, bold = self.gethotcolor(percent, reverse = highishot)

        barlen = int(percent / 100. * (maxlength-2))
        bar = self.colorize("█" * barlen + " " * (maxlength-2-barlen), fg = color, bold = bold)
        #bar = self.colorize("-" * int(percent / 100. * (maxlength-2)), fg = color)
        sys.stdout.write(("%s |"%label if label else "|") + bar)
        self.restorepos()

    def boolean(self, state, label):
        self.savepos()
        msg = (self.colorize("☑", fg = "green") if state else self.colorize("☒", fg = "red")) + " " + label
        sys.stdout.write(msg)
        self.restorepos()

    def absolutebar(self, 
                    value, maxvalue, 
                    unit, label = "", 
                    maxlength = 30, 
                    color = None,
                    autocolor = None, highishot = False):

        value = max(0, min(value, maxvalue))

        self.bar(value * 100. / maxvalue, 
                 maxlength, 
                 "%s%s" % (value, unit), 
                 label = label,
                 showvalue = True, 
                 color = color,
                 autocolor = autocolor, highishot = highishot)

    def booleanmatrix(self, values, label = ""):
        """ 'values' is a list of columns.
        """

        cell = "██"

        if label:
            self.write(label)
            self.relmoveto(0,1)

        orig_x = self.cur_x
        orig_y = self.cur_y

        for i, col in enumerate(values):
            for j, val in enumerate(col):
                self.moveto(orig_x + i * 2, orig_y + j)
                self.write(cell, fg = ("green" if val else "red"))

        self.moveto(orig_x, orig_y - (1 if label else 0))

    def savepos(self):
        sys.stdout.write(self.csi + "s")

    def restorepos(self):
        sys.stdout.write(self.csi + "u")

    def moveto(self, x = 0, y = 0):
        if x < 0:
            print("moveto x out of bounds")
            sys.exit(1)
        if y < 0 or y > self.height:
            print("moveto y out of bounds")

        self.relmoveto(x-self.cur_x, y-self.cur_y)

    def relmoveto(self, x = 0, y = 0):
        """ Relative placement of the cursor
        """
        self.cur_x += x
        self.cur_y += y
        if x < 0:
            sys.stdout.write(self.csi + "%sD" % -x)
        elif x > 0:
            sys.stdout.write(self.csi + "%sC" % x)
        if y < 0:
            sys.stdout.write(self.csi + "%sA" % -y)
        elif y > 0:
            sys.stdout.write(self.csi + "%sB" % y)

    def __enter__(self):
        self._configure_keyboard()
        return self

    def __exit__(self, type, value, traceback):
        self._restore_keyboard()
        # remove margin
        self.moveto(0,0)
        self.relmoveto(-1,-1)
        self.cur_x = 0
        self.cur_y = 0

        self.clear()

        sys.stdout.write(self.csi + "?25h") # show the cursor

    def _configure_keyboard(self):
        """
        set keyboard to read single chars lookahead only
        """
        fd = sys.stdin.fileno()
        self.original_kbd_settings = termios.tcgetattr(fd)
        new = termios.tcgetattr(fd)
        new[3] = new[3] & ~termios.ECHO # lflags
        new[3] = new[3] & ~termios.ICANON # lflags
        new[6][6] = '\000' # Set VMIN to zero for lookahead only
        termios.tcsetattr(fd, termios.TCSADRAIN, new)

    def _restore_keyboard(self):
        """
        restore previous keyboard settings
        """
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, self.original_kbd_settings)

    ARROW_UP = "up"
    ARROW_DOWN = "down"
    ARROW_RIGHT = "right"
    ARROW_LEFT = "left"

    def get_keypress(self):
        """
        Non-blocking polling of the keyboard.
        Read max 1 chars from look ahead.

        Process as well common ANSI escape sequences for arrows.
        """
        key = sys.stdin.read(1)

        if key:
            if ord(key) == 27: # ESC!
                sys.stdin.read(1) # we expect a [ here (ANSI CSI sequence)
                ansicode = sys.stdin.read(1)

                if ansicode == "A":
                    return self.ARROW_UP
                elif ansicode == "B":
                    return self.ARROW_DOWN
                elif ansicode == "C":
                    return self.ARROW_RIGHT
                elif ansicode == "D":
                    return self.ARROW_LEFT

                assert(False)

            return key

if __name__ == "__main__":

    with ConsoleTK() as console:

        while True:
            key = console.get_keypress()
            if key:
                print("%s (code: %s)" % (key, ord(key)))
