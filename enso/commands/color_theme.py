from enso.quasimode import layout

def cmd_enso_theme(ensoapi, color = None):
    """ Change Enso color theme"""
    layout.setColorTheme(color)
    ensoapi.display_message("Enso theme changed to \u201c%s\u201d" % color, "enso")

cmd_enso_theme.valid_args = list(layout.COLOR_THEMES.keys())
