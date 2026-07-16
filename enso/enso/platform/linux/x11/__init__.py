"""
X11 backend of the Enso Linux port.

Implements the quasimode trigger with a passive root-window key grab,
keyboard capture with an active grab, overlays as override-redirect
GTK popups, selection via PRIMARY/CLIPBOARD + XTEST paste, and window
management via EWMH.  Selected by enso.platform.linux.detect for X11
sessions.
"""
