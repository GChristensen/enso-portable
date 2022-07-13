# Enso version for use in UI
ENSO_VERSION = "0.9.1"

# The message displayed when the user types some text that is not a command.
BAD_COMMAND_MSG = "<p><command>%s</command> is not a command.</p>" \
                  "%s"

# Minimum number of characters that should have been typed into the
# quasimode for a bad command message to be shown.
BAD_COMMAND_MSG_MIN_CHARS = 2

# The captions for the above message, indicating commands that are related
# to the command the user typed.
ONE_SUGG_CAPTION = "<caption>Did you mean <command>%s</command>?</caption>"

# The string that is displayed in the quasimode window when the user
# first enters the quasimode.
QUASIMODE_DEFAULT_HELP = "Welcome to Enso! Enter a command, " \
                         "or type \u201chelp\u201d for assistance."

# The string displayed when the user has typed some characters but there
# is no matching command.
QUASIMODE_NO_COMMAND_HELP = "There is no matching command. " \
                            "Use backspace to delete characters."

# Message XML for the Splash message shown when Enso first loads.
OPENING_MSG_XML = "<p><command>Enso</command> is loaded!</p>"

# Message XML for the Splash message shown when Enso is refreshed.
REFRESHING_MSG_XML = "<p><command>Enso</command> is refreshed!</p>"

CLOSING_MSG_XML = "<p>Closing Enso...</p><caption>Enso</caption>"

# Message XML displayed when the mouse hovers over a mini message.
MINI_MSG_HELP_XML = "<p>The <command>hide mini messages</command>" \
                    " and <command>put</command> commands control" \
                    " these mini-messages.</p>"

ABOUT_BOX_XML = "<p><command>Enso</command> Open-Source " + ENSO_VERSION + "</p>" \
                "" \
                "<caption>Based on Enso Community Edition</caption><p> </p>" \
                "<p>Copyright &#169; 2008 <command>Humanized, Inc.</command></p>" \
                "<p>Copyright &#169; 2008-2009 <command>Enso Community</command></p>" \
                "<p>Copyright &#169; 2011-2021 <command>g/christensen</command></p>" \
                "<p> </p><caption>Hit the <command>CapsLock</command> key to invoke Enso</caption>"


BLOCKED_BY_RETREAT_MSG = "<p>Enso Retreat denies the operation.</p><caption>Enso</caption>"