#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os
import termios, sys

class ConsoleTK:

    # color names to indices
    solarized_scheme = {
        "base03":    234, # #002b36 
        "base02":    235, # #073642 
        "base01":    240, # #586e75 
        "base00":    241, # #657b83 
        "base0":     244, # #839496 
        "base1":     245, # #93a1a1 
        "base2":     254, # #eee8d5 
        "base3":     230, # #fdf6e3 
        "yellow":    136, # #b58900 
        "orange":    166, # #cb4b16 
        "red":       160, # #dc322f 
        "magenta":   125, # #d33682 
        "violet":     61, # #6c71c4 
        "blue":       33, # #268bd2 
        "cyan":       37, # #2aa198 
        "green":      64, # #859900 
        }


    solarized_palette = [ ('red', False),
                          ('orange', False),
                          ('yellow', False),
                          ('green', False)]
    csi = '\x1b['
    reset = '\x1b[0m'
 
    def __init__(self, height = 10):

        # unbuffered output
        self.out = os.fdopen(sys.stdout.fileno(), 'w', 0)

        self.color_map = self.solarized_scheme
        self.palette = self.solarized_palette

        self.fg = "base2"
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
        self.out.write("\n" * height)
        self.out.write(self.csi + "?25l") # hide the cursor
        self.out.write(self.csi + "%sF"%height)
        self.cur_x = 0
        self.cur_y = 0
        self.clearzone()

        # add margin
        self.relmoveto(1,1)
        self.cur_x = 0
        self.cur_y = 0
 

    def clearzone(self):
        self.moveto(0,0)
        self.out.write(self.csi + "J")

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
            params.append("48;5;%s" % self.color_map[bg])

        if fg in self.color_map:
            params.append("38;5;%s" % self.color_map[fg])

        if bold:
            params.append('1')
        elif blink:
            params.append('5')
        if params:
            message = ''.join((self.csi, ';'.join(params),
                                'm', message, self.reset))
        
        return message

    def colorint(self, val, warning = False):
        if warning:
            return self.colorize(str(val), fg = "orange")
        else:
            return self.colorize(str(val), fg = "base3")

    def label(self, message, fg = None, bg = None, bold = None, blink = None):
        self.savepos()
        self.out.write(self.colorize(message, fg, bg, bold, blink))
        self.restorepos()

    def vseparator(self, height = 1):
        self.savepos()

        for i in range(height):
            self.out.write("│" + self.csi +"1B" + self.csi + "1D")

        self.restorepos()

    def clear(self, width, height):
        self.savepos()

        for i in range(height):
            self.out.write(" " * width + self.csi +"1B" + self.csi + "%sD" % width)

        self.restorepos()



    def bar(self, 
            percent, maxlength = 30, 
            msg = "", showvalue = True, label = None, 
            color = "base1",
            autocolor = False, highishot = False):
        """
        With auto-color, the color depends on the percentage value.
        If 'highishot' is True, the higher the percentage, the closer to red,
        else, the higher the percentage, the closer to green.
        """
        msg = msg if msg else "{0}%".format(self.colorint(percent))

        self.savepos()

        if label:
            label = self.colorize(label, fg = "base0")

        self.out.write(("%s |"%label if label else "|") + \
                          self.csi +"%sC"%(maxlength-2) + "|"+ \
                         ((" " + msg) if showvalue else ""))
        self.restorepos()

        bold = False
        if autocolor:
            color, bold = self.gethotcolor(percent, reverse = highishot)

        barlen = int(percent / 100. * (maxlength-2))
        bar = self.colorize("█" * barlen + " " * (maxlength-2-barlen), fg = color, bold = bold)
        self.out.write(("%s |"%label if label else "|") + bar)
        self.restorepos()

    def boolean(self, state, label):
        self.savepos()
        label = self.colorize(label, fg = "base0")

        msg = (self.colorize("☑", fg = "green") if state else self.colorize("☒", fg = "red")) + " " + label

        self.out.write(msg)
        self.restorepos()

    def absolutebar(self, 
                    value, maxvalue, 
                    unit, label = "", 
                    maxlength = 30, 
                    color = "base1",
                    autocolor = False, highishot = False):

        msg = "%s%s" % (self.colorint(value, warning = (value > maxvalue)), unit)

        clampedvalue = max(0, min(value, maxvalue))

        self.bar(clampedvalue * 100. / maxvalue, 
                 maxlength, 
                 msg, 
                 label = label,
                 showvalue = True, 
                 color = color,
                 autocolor = autocolor, highishot = highishot)

    def booleanmatrix(self, values, label = ""):
        """ 'values' is a list of columns.
        """

        cell = "██"

        if label:
            label = self.colorize(label, fg = "base0")
            self.label(label)
            self.relmoveto(0,1)

        orig_x = self.cur_x
        orig_y = self.cur_y

        for i, col in enumerate(values):
            for j, val in enumerate(col):
                self.moveto(orig_x + i * 2, orig_y + j)
                self.label(cell, fg = ("green" if val else "red"))

        self.moveto(orig_x, orig_y - (1 if label else 0))

    def savepos(self):
        self.out.write(self.csi + "s")

    def restorepos(self):
        self.out.write(self.csi + "u")

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
            self.out.write(self.csi + "%sD" % -x)
        elif x > 0:
            self.out.write(self.csi + "%sC" % x)
        if y < 0:
            self.out.write(self.csi + "%sA" % -y)
        elif y > 0:
            self.out.write(self.csi + "%sB" % y)

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

        self.clearzone()

        self.out.write(self.csi + "?25h") # show the cursor

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
                else: # return ESC
                    return key

            return key

if __name__ == "__main__":

    with ConsoleTK() as console:

        key = ""
        while ord(key) != 27: # esc
            key = console.get_keypress()
            if key:
                print("%s (code: %s)" % (key, ord(key)))
