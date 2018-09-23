def cmd_count_lines(ensoapi):
    """ Count lines in selected text """
    seldict = ensoapi.get_selection()
    ensoapi.display_message( "Selection is %s lines." %
                             len(seldict.get("text","").splitlines()) )


def cmd_count_characters(ensoapi):
    """ Count characters in selected text """
    text = ensoapi.get_selection().get("text", "").strip()
    if not text:
        ensoapi.display_message( "No selection." )
    ensoapi.display_message( "%d characters." % len(text) )


def cmd_uppercase(ensoapi):
    """ Uppercase selected text """
    seldict = ensoapi.get_selection()
    text = seldict.get("text", "")
    if not text:
        ensoapi.display_message("No selection!")
    else:
        ensoapi.set_selection({"text":text.upper()})


def cmd_lowercase(ensoapi):
    """ Lowercase selected text """
    seldict = ensoapi.get_selection()
    text = seldict.get("text", "")
    if not text:
        ensoapi.display_message("No selection!")
    else:
        ensoapi.set_selection({"text":text.lower()})


def cmd_titlecase(ensoapi):
    """ Titlecase selected text """
    seldict = ensoapi.get_selection()
    text = seldict.get("text", "")
    if not text:
        ensoapi.display_message("No selection!")
    else:
        ensoapi.set_selection({"text":text.title()})


def cmd_unaccent(ensoapi):
    """ Unaccent (normalize) selected text """
    import unicodedata

    seldict = ensoapi.get_selection()
    text = seldict.get("text", "")
    if not text:
        ensoapi.display_message("No selection!")
    else:
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')
        ensoapi.set_selection({"text": text})


def cmd_datetime(ensoapi):
    """ Insert short datetime string in the form yymmdd-HHMMss """
    from time import localtime, strftime
    dt = strftime("%y%m%d-%H%M%S", localtime())
    ensoapi.set_selection(dt)


def cmd_unquote_url(ensoapi):
    """ Decodes encoded characters in a URL """
    import urllib.request, urllib.parse, urllib.error
    seldict = ensoapi.get_selection()
    text = seldict.get("text", "")
    if not text:
        ensoapi.display_message("No selection!")
    else:
        text = urllib.parse.unquote(text)
        ensoapi.set_selection({"text": text})

