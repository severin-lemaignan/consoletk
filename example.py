#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import consoletk

with consoletk.ConsoleTK(height=20) as console:

    key = None 
    lastkey = None
    i = 0
    while not key or ord(key) != 27: # esc

        i+=1

        key = console.get_keypress()
        if key:
            lastkey = key

        console.label("ConsoleTK demo", fg="violet",bold=True)
        console.relmoveto(0,2)
        console.boolean(True, "I'm true")
        console.relmoveto(11,0)
        console.boolean(False, "I'm false")

        console.moveto(0,3)
        console.vsep(2)
        console.moveto(2,3)
        console.absolutebar(i % 10, 10, "kg", 
                            label = "Weight", 
                            maxlength = 20, 
                            autocolor = True, 
                            highishot = True)

        console.moveto(2,4)
        console.absolutebar((i % 10) / 10., 1, 
                            "rad.s^-1", 
                            label = " Angle")

        console.moveto(0,5)
        console.hsep(78, fg="green")

        console.moveto(30,6)
        console.vsep(5, double=True)

        console.relmoveto(-20,1)
        console.label("I'm a label!")

        console.relmoveto(25,2)
        console.label("I'm another label!")

        console.relmoveto(20,-2)
        console.box(8,4,border_fg="yellow",border_bg="orange",bg="violet")
        console.relmoveto(1,1)
        console.label("In the",bg="violet")
        console.relmoveto(0,1)
        console.label("box!",bg="violet")

        console.moveto(78,1)
        console.vsep(10)

        console.moveto(80,1)
        console.label("Press a key... (esc to quit)")

        console.relmoveto(0,2)
        if lastkey:
            console.label("Keypress: %s (code: %s)" % (lastkey, ord(lastkey)))

        console.relmoveto(1,3)
        console.box(20,6,"blue","base00",bg="base02",double=True)
        console.moveto(0,0)
        time.sleep(0.1)
