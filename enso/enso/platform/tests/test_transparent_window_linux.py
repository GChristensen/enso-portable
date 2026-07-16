#!/usr/bin/env python3

# Standalone bring-up test for the Linux TransparentWindow (no Enso core).
#
# Draws a rounded rectangle with text, fades the window out and in,
# moves it, crops it, then quits.  While it is on screen, try clicking
# through the rectangle: the click must land on the window below.

import math
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                os.path.pardir)))

import cairo

import enso.platform.linux
graphics = enso.platform.linux.provideInterface("graphics")

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib

WIDTH, HEIGHT = 400, 200


def draw_scene(surface):
    cr = cairo.Context(surface)
    cr.set_operator(cairo.OPERATOR_CLEAR)
    cr.paint()
    cr.set_operator(cairo.OPERATOR_OVER)

    # Rounded rectangle
    x, y, w, h, r = 10, 10, WIDTH - 20, HEIGHT - 20, 25
    cr.new_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()
    cr.set_source_rgba(0.0, 0.4, 0.1, 0.85)
    cr.fill()

    cr.set_source_rgba(1, 1, 1, 1)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL,
                        cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(24)
    cr.move_to(40, HEIGHT / 2)
    cr.show_text("Enso TransparentWindow")
    surface.flush()


def main():
    screen = Gdk.Screen.get_default()
    print("Screen composited:", bool(screen and screen.is_composited()))
    print("Desktop size:", graphics.getDesktopSize())
    print("Desktop offset:", graphics.getDesktopOffset())

    window = graphics.TransparentWindow(100, 100, WIDTH, HEIGHT)
    draw_scene(window.makeCairoSurface())
    window.update()

    state = {"phase": "fade_out", "opacity": 255, "ticks": 0}

    def step():
        phase = state["phase"]
        if phase == "fade_out":
            state["opacity"] = max(0, state["opacity"] - 5)
            window.setOpacity(state["opacity"])
            if state["opacity"] == 0:
                state["phase"] = "fade_in"
        elif phase == "fade_in":
            state["opacity"] = min(255, state["opacity"] + 5)
            window.setOpacity(state["opacity"])
            if state["opacity"] == 255:
                print("Fade cycle done; moving window.")
                window.setPosition(300, 300)
                window.update()
                state["phase"] = "moved"
        elif phase == "moved":
            state["ticks"] += 1
            if state["ticks"] == 60:
                print("Cropping window to half size.")
                window.setSize(WIDTH // 2, HEIGHT // 2)
                window.update()
            elif state["ticks"] >= 180:
                print("Done.")
                window.finish()
                Gtk.main_quit()
                return GLib.SOURCE_REMOVE
        return GLib.SOURCE_CONTINUE

    GLib.timeout_add(16, step)
    Gtk.main()


if __name__ == "__main__":
    main()
