import xml.sax.saxutils

from enso.messages import displayMessage
from enso import selection

class EnsoApi(object):
    """
    A simple facade to Enso's functionality for use by commands.
    """

    def display_message(self, msg, caption=None):
        """
        Displays the given message, with an optional caption.  Both
        parameters should be unicode strings.
        """

        if not isinstance(msg, basestring):
            msg = unicode(msg)

        msg = xml.sax.saxutils.escape(msg)
        xmltext = "<p>%s</p>" % msg
        if caption:
            caption = xml.sax.saxutils.escape(caption)
            xmltext += "<caption>%s</caption>" % caption
        return displayMessage(xmltext)

    def get_selection(self):
        """
        Retrieves the current selection and returns it as a
        selection dictionary.
        """

        return selection.get()

    def set_selection(self, seldict):
        """
        Sets the current selection to the contents of the given
        selection dictionary.

        Alternatively, if a string is provided instead of a
        dictionary, the current selection is set to the unicode
        contents of the string.
        """

        if isinstance(seldict, basestring):
            seldict = { "text" : unicode(seldict) }
        return selection.set(seldict)

    def get_enso_commands_folder(self):
        """
        Returns the location of the Enso scripts folder.
        """
        from enso.providers import getInterface
        return getInterface("scripts_folder")()

    def get_commands_from_text(self, text):
        """
        Given a block of Python text, returns all the valid Enso
        commands defined therein.
        """
        from cmdretriever import getCommandsFromObjects
        execGlobals = {}
        exec text in execGlobals
        commands = getCommandsFromObjects( execGlobals )
        return commands 

